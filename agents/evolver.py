"""
evolver.py — エージェント増殖エンジン
brainが「新しい収益チャネルが必要」と判断したとき、
新しいエージェントのPythonコードを自動生成・登録する

核心: AIがAIを生む。会社が自律的に成長する。
"""
import sys
import ast
import json
import subprocess
import tempfile
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager

JST = timezone(timedelta(hours=9))
AGENTS_DIR = ROOT / "agents"
BRAIN_PATH = ROOT / "core" / "brain.py"

AGENT_GENERATION_PROMPT = """あなたはPythonエキスパートです。
以下の仕様に従って、実際に動作するPythonエージェントを作成してください。

## エージェント仕様
- 名前: {name}
- 役割: {role}
- 理由: {reason}
- トリガー（brainから呼ばれるアクション種別）: {triggers}
- 入力パラメータ: {inputs}
- 出力: {outputs}

## コーディング規約
- ファイル冒頭にdocstringで役割を説明する
- メイン関数名は `run(params: dict) -> dict` とする（brainから呼ばれる）
- APIキー未設定時はEnvironmentError（シミュレーション値を返さない）
- エラーは例外を上げる（握りつぶさない）
- `ROOT = Path(__file__).parent.parent` でプロジェクトルートを参照
- sys.path.insert(0, str(ROOT)) して core/ をインポート可能にする
- リトライは最大3回まで（指数バックオフ）
- 実行ログは print("[AgentName] ...") 形式

## 参考: 既存エージェントの構造
```python
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager

def run(params: dict) -> dict:
    \"\"\"brainから呼ばれるメイン関数\"\"\"
    # 処理
    return {{"status": "ok", "detail": "..."}}
```

## 追加要件
- 対象プラットフォームのAPIが利用可能な場合は実際のAPI呼び出しを実装
- APIキーは os.environ.get("XXX_API_KEY") で取得
- 処理結果はdict（status, detail, data）で返す

Pythonコードのみ出力（```python...```で囲む）:"""

DISPATCHER_REGISTRATION = '''
        elif action_type == "{trigger}":
            from agents.{module_name} import run as run_{safe_name}
            result["detail"] = str(run_{safe_name}(params))'''


def create_agent(spec: dict) -> str:
    """新しいエージェントを生成してagents/に保存する。返り値はファイルパス。"""
    name = spec.get("name", "new_agent").replace("-", "_").replace(" ", "_")
    role = spec.get("role", "新しい収益チャネルへの参入")
    reason = spec.get("reason", "")
    triggers = spec.get("triggers", [f"RUN_{name.upper()}"])
    inputs = spec.get("inputs", ["params"])
    outputs = spec.get("outputs", ["result"])

    print(f"[Evolver] エージェント生成開始: {name}")
    print(f"[Evolver] 役割: {role}")

    # 1. LLMでコードを生成
    prompt = AGENT_GENERATION_PROMPT.format(
        name=name, role=role, reason=reason,
        triggers=triggers, inputs=inputs, outputs=outputs,
    )
    raw_code = llm_client.call(prompt, max_tokens=4096)

    # コードブロックを抽出
    if "```python" in raw_code:
        code = raw_code.split("```python")[1].split("```")[0].strip()
    elif "```" in raw_code:
        code = raw_code.split("```")[1].split("```")[0].strip()
    else:
        code = raw_code.strip()

    # 2. 構文チェック
    try:
        ast.parse(code)
        print(f"[Evolver] 構文チェック: OK")
    except SyntaxError as e:
        raise ValueError(f"生成コードに構文エラー: {e}\n---\n{code[:500]}")

    # 3. サンドボックステスト（importのみ）
    _sandbox_test(code, name)

    # 4. agents/{name}.py に保存
    agent_path = AGENTS_DIR / f"{name}.py"
    agent_path.write_text(code, encoding="utf-8")
    print(f"[Evolver] 保存: {agent_path}")

    # 5. brain.pyのディスパッチャーに登録
    _register_in_brain(name, triggers)

    # 6. state.jsonに記録
    state_manager.register_agent(name, created_by_evolver=True)

    # 7. エージェント台帳を更新
    _update_agent_registry(name, spec)

    print(f"[Evolver] エージェント生成完了: {agent_path}")
    return str(agent_path)


def _sandbox_test(code: str, name: str) -> None:
    """一時ファイルに書き込んでimportテストを行う"""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["python", "-c", f"import ast; ast.parse(open('{tmp_path}').read()); print('OK')"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise ValueError(f"サンドボックステスト失敗:\n{result.stderr}")
        print(f"[Evolver] サンドボックステスト: OK")
    finally:
        os.unlink(tmp_path)


def _register_in_brain(name: str, triggers: list[str]) -> None:
    """brain.pyのexecute_action()ディスパッチャーに新エージェントを追記する"""
    brain_code = BRAIN_PATH.read_text(encoding="utf-8")

    # 既に登録済みなら何もしない
    if f"from agents.{name} import" in brain_code:
        print(f"[Evolver] brain.pyへの登録: 既に存在")
        return

    # DO_NOTHING の elif の直前に挿入
    insert_marker = '        elif action_type == "DO_NOTHING":'
    if insert_marker not in brain_code:
        print(f"[Evolver] brain.py挿入ポイントが見つかりません。手動登録が必要です。")
        return

    safe_name = name.replace("-", "_")
    new_block = ""
    for trigger in triggers:
        new_block += DISPATCHER_REGISTRATION.format(
            trigger=trigger,
            module_name=name,
            safe_name=safe_name,
        )

    updated_code = brain_code.replace(insert_marker, new_block + "\n" + insert_marker)

    # 構文チェック
    try:
        ast.parse(updated_code)
    except SyntaxError as e:
        print(f"[Evolver] brain.py更新後に構文エラー。スキップ: {e}")
        return

    BRAIN_PATH.write_text(updated_code, encoding="utf-8")
    print(f"[Evolver] brain.pyに登録完了: {triggers}")


def _update_agent_registry(name: str, spec: dict) -> None:
    """エージェント台帳 data/agent_registry.json を更新する"""
    registry_path = ROOT / "data" / "agent_registry.json"
    registry = {}
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)

    registry[name] = {
        "name": name,
        "role": spec.get("role", ""),
        "triggers": spec.get("triggers", []),
        "created_at": datetime.now(JST).isoformat(),
        "created_by": "evolver",
        "status": "active",
    }

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def deactivate_agent(name: str) -> bool:
    """パフォーマンスが悪いエージェントを無効化する"""
    agent_path = AGENTS_DIR / f"{name}.py"
    disabled_path = AGENTS_DIR / f"_{name}.py.disabled"

    if not agent_path.exists():
        return False

    agent_path.rename(disabled_path)

    registry_path = ROOT / "data" / "agent_registry.json"
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registry = json.load(f)
        if name in registry:
            registry[name]["status"] = "disabled"
            registry[name]["disabled_at"] = datetime.now(JST).isoformat()
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

    print(f"[Evolver] エージェント無効化: {name}")
    return True


def improve_agent(name: str, performance_data: dict) -> str:
    """既存エージェントのコードを改善する"""
    from agents.improver import improve_code
    return improve_code(
        f"agents/{name}.py",
        {"goal": "パフォーマンス改善", "error": str(performance_data)}
    )
