"""
memory.py — 学習・記憶システム
成功/失敗パターンを蓄積し、brainの判断精度を上げる
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

JST = timezone(timedelta(hours=9))
MEMORY_DIR = Path(__file__).parent.parent / "data" / "memory"
SUCCESSES = MEMORY_DIR / "successes.jsonl"
FAILURES = MEMORY_DIR / "failures.jsonl"
MARKET_HISTORY = MEMORY_DIR / "market_history.jsonl"

MAX_LINES = 500  # 各ファイルの最大行数


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    _trim(path)


def _read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def _trim(path: Path) -> None:
    """ファイルが大きくなりすぎたら古いエントリを削除する"""
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) > MAX_LINES:
        path.write_text("\n".join(lines[-MAX_LINES:]) + "\n", encoding="utf-8")


def record_success(action_type: str, details: dict, outcome: str) -> None:
    """成功した施策を記録する"""
    _append(SUCCESSES, {
        "timestamp": datetime.now(JST).isoformat(),
        "action_type": action_type,
        "details": details,
        "outcome": outcome,
    })


def record_failure(action_type: str, details: dict, reason: str) -> None:
    """失敗した施策を記録する"""
    _append(FAILURES, {
        "timestamp": datetime.now(JST).isoformat(),
        "action_type": action_type,
        "details": details,
        "reason": reason,
    })


def record_market(topics: list[str], source: str = "scan") -> None:
    """市場トレンドを記録する"""
    _append(MARKET_HISTORY, {
        "timestamp": datetime.now(JST).isoformat(),
        "topics": topics,
        "source": source,
    })


def get_relevant_memories(action_type: str = None, limit: int = 10) -> dict:
    """brainのプロンプトに注入する過去の記憶を取得する"""
    successes = _read_all(SUCCESSES)[-limit:]
    failures = _read_all(FAILURES)[-limit:]

    if action_type:
        successes = [s for s in successes if s.get("action_type") == action_type][-5:]
        failures = [f for f in failures if f.get("action_type") == action_type][-5:]

    return {
        "successes": successes,
        "failures": failures,
    }


def get_market_history(days: int = 14) -> list[dict]:
    """直近N日の市場トレンド履歴を取得する"""
    all_records = _read_all(MARKET_HISTORY)
    cutoff = (datetime.now(JST).timestamp() - days * 86400)
    result = []
    for r in all_records:
        try:
            ts = datetime.fromisoformat(r["timestamp"]).timestamp()
            if ts >= cutoff:
                result.append(r)
        except Exception:
            result.append(r)
    return result


def summarize_for_prompt(limit: int = 5) -> str:
    """brainプロンプトに埋め込む記憶サマリーを生成する"""
    successes = _read_all(SUCCESSES)[-limit:]
    failures = _read_all(FAILURES)[-limit:]

    lines = []
    if successes:
        lines.append("【過去の成功パターン】")
        for s in successes:
            lines.append(f"- {s.get('action_type')}: {s.get('outcome', '')}")
    if failures:
        lines.append("【過去の失敗パターン（繰り返すな）】")
        for f in failures:
            lines.append(f"- {f.get('action_type')}: {f.get('reason', '')}")

    return "\n".join(lines) if lines else "（過去の記録なし）"
