"""
self_modifier.py — コード自己書き換えエージェント
全エージェントのパフォーマンスを評価し、問題があるコードを自動改善する
"""
import sys
import ast
import json
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from glob import glob

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager

JST = timezone(timedelta(hours=9))
AGENTS_DIR = ROOT / "agents"
CHANGE_LOG = ROOT / "data" / "change_log.jsonl"
PROTECTED_FILES = {"brain.py", "__init__.py"}  # 書き換え禁止


def get_agent_performance(agent_name: str) -> dict:
    """エージェントのパフォーマンス指標をchange_logから集計する"""
    if not CHANGE_LOG.exists():
        return {"error_rate": 0.0, "effectiveness": 1.0, "runs": 0}

    errors = 0
    successes = 0

    with open(CHANGE_LOG, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if agent_name in entry.get("file", ""):
                    if entry.get("type") == "error":
                        errors += 1
                    else:
                        successes += 1
            except Exception:
                continue

    total = errors + successes
    if total == 0:
        return {"error_rate": 0.0, "effectiveness": 1.0, "runs": 0}

    return {
        "error_rate": errors / total,
        "effectiveness": successes / total,
        "runs": total,
        "errors": errors,
        "successes": successes,
    }


def review_and_improve() -> list[dict]:
    """全エージェントをスキャンし、問題があれば改善する"""
    results = []
    state = state_manager.load()
    errors = state.get("errors", [])

    # エラーログからターゲットを特定
    error_targets = {}
    for err in errors:
        agent = err.get("agent", "").split("/")[-1]
        if agent and agent not in PROTECTED_FILES:
            error_targets[agent] = err.get("error", "")

    # 全エージェントのパフォーマンスを評価
    agent_files = list(AGENTS_DIR.glob("*.py"))
    for agent_path in agent_files:
        name = agent_path.name
        if name in PROTECTED_FILES or name.startswith("_"):
            continue

        perf = get_agent_performance(name)
        needs_fix = (
            perf["error_rate"] > 0.3
            or name.replace(".py", "") in error_targets
        )

        if not needs_fix:
            continue

        print(f"[SelfModifier] 改善対象: {name} (エラー率: {perf['error_rate']:.1%})")
        error_context = error_targets.get(name.replace(".py", ""), "")

        try:
            from agents.improver import improve_code
            result = improve_code(name, {
                "goal": f"エラー率低下（現在{perf['error_rate']:.1%}）",
                "error": error_context,
            })
            results.append({"file": name, "status": "improved", "detail": result})
            _log_change(name, "auto-improvement", f"エラー率{perf['error_rate']:.1%}を改善")
        except Exception as e:
            results.append({"file": name, "status": "failed", "detail": str(e)})
            print(f"[SelfModifier] 改善失敗 {name}: {e}")

        time.sleep(2)  # API制限対策

    if not results:
        print("[SelfModifier] 改善が必要なエージェントなし")

    return results


def validate_all_agents() -> dict:
    """全エージェントの構文チェックを行う"""
    results = {"ok": [], "errors": []}
    for agent_path in AGENTS_DIR.glob("*.py"):
        try:
            code = agent_path.read_text(encoding="utf-8")
            ast.parse(code)
            results["ok"].append(agent_path.name)
        except SyntaxError as e:
            results["errors"].append({"file": agent_path.name, "error": str(e)})
            print(f"[SelfModifier] 構文エラー: {agent_path.name}: {e}")

    print(f"[SelfModifier] 構文チェック: OK={len(results['ok'])}件, エラー={len(results['errors'])}件")
    return results


def fix_error(spec: dict) -> str:
    """brainからFIX_ERRORが来たとき呼ばれる"""
    target = spec.get("target", "")
    error = spec.get("error", "")

    if not target:
        # エラーログから最も深刻な問題を特定
        results = review_and_improve()
        return f"自動改善実行: {len(results)}件"

    from agents.improver import improve_code
    return improve_code(target, {"goal": "バグ修正", "error": error})


def _log_change(filename: str, change_type: str, description: str) -> None:
    CHANGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(JST).isoformat(),
        "file": filename,
        "type": change_type,
        "description": description,
    }
    with open(CHANGE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def run(params: dict = None) -> dict:
    """brainから呼ばれるエントリポイント"""
    validation = validate_all_agents()
    improvements = review_and_improve()
    return {
        "status": "ok",
        "syntax_errors": len(validation["errors"]),
        "improved": len([r for r in improvements if r["status"] == "improved"]),
        "detail": str(improvements),
    }
