"""
notifier.py — Discord Webhook通知
brain実行後のCEO向けレポートを送信する
"""
import os
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional

JST = timezone(timedelta(hours=9))


def _webhook_url() -> Optional[str]:
    return os.environ.get("DISCORD_WEBHOOK_URL")


def send(message: str, urgent: bool = False) -> bool:
    """Discordにメッセージを送信する"""
    url = _webhook_url()
    if not url:
        print(f"[Notifier] DISCORD_WEBHOOK_URL未設定。通知スキップ:\n{message}")
        return False
    try:
        prefix = "🚨 " if urgent else ""
        resp = requests.post(url, json={"content": prefix + message}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[Notifier] Discord送信失敗: {e}")
        return False


def send_daily_report(state: dict, actions_taken: list, errors: list) -> bool:
    """日次レポートをDiscordに送信する"""
    now = datetime.now(JST).strftime("%Y-%m-%d")
    revenue = state.get("revenue", {})
    products = state.get("products", {})
    agents = state.get("agents", {})

    action_lines = ""
    for i, a in enumerate(actions_taken[:5], 1):
        action_lines += f"  {i}. {a.get('type', '?')}: {a.get('summary', '')}\n"
    if not action_lines:
        action_lines = "  なし（DO_NOTHING）\n"

    error_line = f"⚠️ エラー: {len(errors)}件\n" if errors else "✅ エラー: なし\n"

    msg = (
        f"📊 **AETERNA日報 ({now})**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 売上（累計）: ¥{revenue.get('total_lifetime', 0):,}\n"
        f"💰 直近7日: ¥{revenue.get('last_7_days', 0):,}\n"
        f"📦 商品数: {products.get('total', 0)}個（公開: {len(products.get('published', []))}）\n"
        f"🤖 稼働エージェント: {agents.get('total', 0)}個\n"
        f"📈 今日の実行:\n{action_lines}"
        f"{error_line}"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"次回実行: 明日21:00 JST"
    )
    return send(msg)


def send_error(error: str, agent: str = "brain") -> bool:
    """緊急エラー通知を送信する"""
    msg = f"🚨 **AETERNA エラー通知**\nAgent: {agent}\n```\n{error[:500]}\n```"
    return send(msg, urgent=True)


def send_weekly_summary(state: dict) -> bool:
    """週次サマリーを送信する（毎週日曜に呼ぶ）"""
    revenue = state.get("revenue", {})
    decisions = state.get("decisions_log", [])[-7:]

    completed = [d for d in decisions if d.get("result") not in ("pending", "failed")]
    failed = [d for d in decisions if d.get("result") == "failed"]

    msg = (
        f"📅 **AETERNA 週次サマリー**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 直近30日売上: ¥{revenue.get('last_30_days', 0):,}\n"
        f"✅ 完了した意思決定: {len(completed)}件\n"
        f"❌ 失敗した意思決定: {len(failed)}件\n"
        f"🏃 累計実行回数: {state.get('run_count', 0)}回\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    return send(msg)
