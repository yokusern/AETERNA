"""
improver.py — 改善実行エージェント
商品コンテンツとコード自体を改善する
「エージェントがエージェントを改善する」機能を含む
"""
import sys
import os
import ast
import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager

JST = timezone(timedelta(hours=9))
PRODUCTS_DIR = ROOT / "products"
AGENTS_DIR = ROOT / "agents"
BACKUP_DIR = ROOT / "data" / "backups"


def improve(target: str, spec: dict) -> str:
    """ターゲットに応じて商品またはコードを改善する"""
    if target.startswith("product_") or (PRODUCTS_DIR / target).exists():
        return improve_product(target, spec)
    elif target.endswith(".py"):
        return improve_code(target, spec)
    else:
        print(f"[Improver] 不明なターゲット: {target}")
        return f"スキップ: {target}"


def improve_product(product_id: str, spec: dict) -> str:
    """商品の説明文・コンテンツを改善する"""
    product_dir = PRODUCTS_DIR / product_id
    if not product_dir.exists():
        raise FileNotFoundError(f"商品ディレクトリなし: {product_dir}")

    improvement_type = spec.get("improvement", "description")
    reason = spec.get("reason", "改善")

    if improvement_type == "description":
        return _improve_description(product_id, product_dir, reason)
    elif improvement_type == "content":
        return _improve_content(product_id, product_dir, spec)
    else:
        return f"スキップ（不明な改善タイプ: {improvement_type}）"


def _improve_description(product_id: str, product_dir: Path, reason: str) -> str:
    """Gumroad商品説明文を改善する"""
    spec_path = product_dir / "spec.json"
    page_path = product_dir / "gumroad_page.md"

    if not spec_path.exists():
        raise FileNotFoundError(f"spec.jsonなし: {spec_path}")

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    current_desc = ""
    if page_path.exists():
        current_desc = page_path.read_text(encoding="utf-8")[:500]

    prompt = f"""以下のGumroad商品の説明文を改善してください。

商品名: {spec.get('name', '')}
現在の説明文: {current_desc}
改善理由: {reason}

改善のポイント:
- 最初の2行でキーワードと価値を伝える
- ベネフィット（機能でなく価値）を強調
- 具体的な数値や例を追加
- 購買障壁を取り除くFAQを追加

改善後の説明文（Markdown形式、400字程度）を出力:"""

    improved = llm_client.call(prompt, max_tokens=800, fast=True)

    # バックアップ
    _backup(page_path)
    page_path.write_text(improved, encoding="utf-8")

    # spec.jsonのステータスを更新
    spec["status"] = "ready_to_upload"
    spec["improved_at"] = datetime.now(JST).isoformat()
    with open(spec_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    print(f"[Improver] 説明文改善完了: {product_id}")
    return f"改善完了: {product_id}/gumroad_page.md"


def _improve_content(product_id: str, product_dir: Path, spec: dict) -> str:
    """商品コンテンツ本体を補強する"""
    main_path = product_dir / "content" / "main.md"
    if not main_path.exists():
        raise FileNotFoundError(f"main.mdなし: {main_path}")

    current = main_path.read_text(encoding="utf-8")
    add_what = spec.get("add", "実用例と具体的な手順")

    prompt = f"""以下のデジタル商品コンテンツに、{add_what}を追加してください。
既存の内容を変更せず、末尾に追記してください。

## 現在のコンテンツ（最後の500文字）
{current[-500:]}

## 追加する内容
{add_what}

追記するMarkdownコンテンツのみ出力:"""

    addition = llm_client.call(prompt, max_tokens=2000)
    _backup(main_path)
    with open(main_path, "a", encoding="utf-8") as f:
        f.write(f"\n\n---\n\n{addition}")

    print(f"[Improver] コンテンツ補強完了: {product_id}")
    return f"コンテンツ追記完了: {product_id}"


def improve_code(filename: str, spec: dict) -> str:
    """エージェントのPythonコードを改善する（自己改善）"""
    target_path = ROOT / filename
    if not target_path.exists():
        target_path = AGENTS_DIR / filename
    if not target_path.exists():
        raise FileNotFoundError(f"ファイルなし: {filename}")

    code = target_path.read_text(encoding="utf-8")
    improvement_goal = spec.get("goal", "エラー率低下・可読性向上")
    error_context = spec.get("error", "")

    prompt = f"""以下のPythonコードを改善してください。

## 改善目標
{improvement_goal}

## エラー（あれば）
{error_context}

## 現在のコード
```python
{code[:3000]}
```

## 要件
- 機能を変えずに品質を向上させる
- 既存のAPIシグネチャは維持する
- コメントは最小限に

改善後のPythonコード全体のみ出力（```python...```で囲む）:"""

    improved_raw = llm_client.call(prompt, max_tokens=4096)

    # コードブロックを抽出
    if "```python" in improved_raw:
        improved = improved_raw.split("```python")[1].split("```")[0].strip()
    elif "```" in improved_raw:
        improved = improved_raw.split("```")[1].split("```")[0].strip()
    else:
        improved = improved_raw

    # 構文チェック
    try:
        ast.parse(improved)
    except SyntaxError as e:
        raise ValueError(f"改善後コードに構文エラー: {e}")

    # バックアップしてから書き込む
    _backup(target_path)
    target_path.write_text(improved, encoding="utf-8")

    _log_change(filename, "auto-improvement", improvement_goal)
    print(f"[Improver] コード改善完了: {filename}")
    return f"コード改善完了: {filename}"


def _backup(path: Path) -> Path:
    """ファイルをバックアップする"""
    if not path.exists():
        return path
    ts = datetime.now(JST).strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"{path.name}.{ts}.bak"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup_path)
    return backup_path


def _log_change(filename: str, change_type: str, description: str) -> None:
    """変更ログをdata/change_log.jsonlに記録する"""
    log_path = ROOT / "data" / "change_log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(JST).isoformat(),
        "file": filename,
        "type": change_type,
        "description": description,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def fix_error(spec: dict) -> str:
    """エラーレポートに基づいてコードを修正する"""
    target = spec.get("target", "")
    error = spec.get("error", "")
    if not target or not error:
        return "target/errorが指定されていません"
    return improve_code(target, {"goal": "バグ修正", "error": error})
