"""
revenue_scanner.py — 収益チャネル探索エンジン
AIエージェントだけで参入可能な収益チャネルを分析し、優先度を付ける
月1回brainから呼ばれる
"""
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager, memory

JST = timezone(timedelta(hours=9))

CHANNELS = [
    {
        "name": "Gumroad",
        "type": "marketplace",
        "url": "https://gumroad.com",
        "status": "active",
        "entry_barrier": "low",
        "ai_automatable": True,
        "products": ["pdf", "zip", "template"],
        "estimated_monthly_jpy": (30000, 500000),
    },
    {
        "name": "note.com",
        "type": "article",
        "url": "https://note.com",
        "status": "not_entered",
        "entry_barrier": "low",
        "ai_automatable": True,
        "products": ["article", "magazine"],
        "estimated_monthly_jpy": (10000, 200000),
    },
    {
        "name": "BOOTH",
        "type": "marketplace",
        "url": "https://booth.pm",
        "status": "not_entered",
        "entry_barrier": "low",
        "ai_automatable": True,
        "products": ["digital_goods", "pdf"],
        "estimated_monthly_jpy": (5000, 100000),
    },
    {
        "name": "Kindle Direct Publishing",
        "type": "ebook",
        "url": "https://kdp.amazon.co.jp",
        "status": "not_entered",
        "entry_barrier": "medium",
        "ai_automatable": True,
        "products": ["ebook"],
        "estimated_monthly_jpy": (5000, 300000),
    },
    {
        "name": "Zenn",
        "type": "article",
        "url": "https://zenn.dev",
        "status": "not_entered",
        "entry_barrier": "low",
        "ai_automatable": True,
        "products": ["book", "article"],
        "estimated_monthly_jpy": (3000, 50000),
    },
    {
        "name": "ココナラ",
        "type": "skill",
        "url": "https://coconala.com",
        "status": "not_entered",
        "entry_barrier": "low",
        "ai_automatable": True,
        "products": ["text_service", "template"],
        "estimated_monthly_jpy": (10000, 100000),
    },
]


def scan_opportunities(state: dict) -> list[dict]:
    """参入可能な収益チャネルを分析・ランク付けする"""
    revenue = state.get("revenue", {})
    total = revenue.get("total_lifetime", 0)
    mem = memory.summarize_for_prompt(limit=3)

    channel_summary = json.dumps(
        [{k: v for k, v in c.items() if k != "url"} for c in CHANNELS],
        ensure_ascii=False
    )

    prompt = f"""AETERNAはAIエージェントが自律的に運営するデジタル商品会社です。

## 現在の状況
- 累計売上: ¥{total:,}
- 現在の参入チャネル: Gumroadのみ
- 過去の記憶: {mem}

## 分析対象チャネル
{channel_summary}

## AIエージェントの能力
- テキスト・Markdown・Pythonコードを自動生成できる
- Webスクレイピングで情報収集できる
- APIが公開されているサービスには自動投稿できる
- 画像生成は難しい（テキストベースのみ）
- 動画撮影は不可能
- 銀行振込などの物理操作は不可能

## 指示
現在の状況を踏まえ、次に参入すべきチャネルをTOP3で優先度順にJSON配列で出力してください。

[
  {{
    "channel": "チャネル名",
    "priority": 1,
    "reason": "参入理由（2文以内）",
    "first_action": "最初に作るべき商品/コンテンツ",
    "required_agent": "必要なエージェント名（snake_case）",
    "estimated_days_to_first_revenue": 数値,
    "estimated_monthly_jpy": 数値
  }}
]"""

    try:
        opportunities = llm_client.call_json(prompt, max_tokens=1024)
        if isinstance(opportunities, list):
            _save_scan_result(opportunities)
            return opportunities[:3]
    except Exception as e:
        print(f"[RevenueScanner] スキャンエラー: {e}")

    return []


def _save_scan_result(opportunities: list) -> None:
    """スキャン結果をdata/revenue_scan.jsonに保存する"""
    scan_path = ROOT / "data" / "revenue_scan.json"
    scan_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scan_path, "w", encoding="utf-8") as f:
        json.dump({
            "scanned_at": datetime.now(JST).isoformat(),
            "opportunities": opportunities,
        }, f, ensure_ascii=False, indent=2)
    print(f"[RevenueScanner] スキャン結果保存: {scan_path}")


def get_channel_status() -> dict:
    """各チャネルの参入状況をまとめる"""
    return {c["name"]: c["status"] for c in CHANNELS}


def should_scan_today(state: dict) -> bool:
    """今日スキャンを実行すべきか判断する（月1回）"""
    scan_path = ROOT / "data" / "revenue_scan.json"
    if not scan_path.exists():
        return True
    try:
        with open(scan_path, encoding="utf-8") as f:
            last = json.load(f)
        last_ts = datetime.fromisoformat(last["scanned_at"]).timestamp()
        return (datetime.now(JST).timestamp() - last_ts) > 30 * 86400
    except Exception:
        return True
