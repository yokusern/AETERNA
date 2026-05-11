"""
analyzer.py — 市場分析エージェント
「何が売れるか」を世の中のデータから見つける
brainのプロンプト構築と、市場トレンド取得を担当する
"""
import sys
import time
import requests
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager, memory

GUMROAD_DISCOVER_URL = "https://gumroad.com/discover"
PYTRENDS_KEYWORDS = [
    "ChatGPT", "Claude AI", "AI自動化", "Python 自動化",
    "Notion テンプレート", "副業 AI", "プロンプト", "業務効率化"
]


def get_trending_topics() -> list[str]:
    """複数ソースからトレンドトピックを収集する"""
    topics = set()

    # 1. pytrends（Google Trends）
    pytrends_topics = _fetch_pytrends()
    topics.update(pytrends_topics)

    # 2. Gumroadディスカバリーページのキーワード
    gumroad_topics = _scrape_gumroad_trending()
    topics.update(gumroad_topics)

    # 3. LLMに「今のトレンド」を聞く（フォールバック兼補完）
    if len(topics) < 5:
        llm_topics = _ask_llm_trends()
        topics.update(llm_topics)

    result = list(topics)[:20]
    print(f"[Analyzer] トレンドトピック取得: {len(result)}件")
    return result


def _fetch_pytrends() -> list[str]:
    """Google Trendsからトレンドキーワードを取得する"""
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="ja-JP", tz=540, timeout=(10, 25))
        pt.build_payload(PYTRENDS_KEYWORDS[:4], timeframe="now 7-d", geo="JP")
        related = pt.related_queries()
        topics = []
        for kw, data in related.items():
            if data and data.get("top") is not None:
                for _, row in data["top"].head(5).iterrows():
                    topics.append(row["query"])
        return topics[:10]
    except ImportError:
        return []
    except Exception as e:
        print(f"[Analyzer] pytrends取得失敗（スキップ）: {e}")
        return []


def _scrape_gumroad_trending() -> list[str]:
    """Gumroadのディスカバリーページから売れ筋カテゴリを取得する"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; aeterna-bot/1.0)"}
        resp = requests.get(GUMROAD_DISCOVER_URL, headers=headers, timeout=10)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        topics = []
        for tag in soup.select("a.tag, .product-tag, h2, .category"):
            text = tag.get_text(strip=True)
            if 2 < len(text) < 30:
                topics.append(text)
        return list(set(topics))[:10]
    except Exception as e:
        print(f"[Analyzer] Gumroadスクレイピング失敗（スキップ）: {e}")
        return []


def _ask_llm_trends() -> list[str]:
    """LLMに現在の市場トレンドを聞く"""
    try:
        prompt = """2026年5月現在、Gumroad・note.com・BOOTHなどのデジタル商品市場で
日本人が特に購入しているカテゴリ・キーワードを15個挙げてください。
JSON配列形式で出力（説明なし）: ["キーワード1", "キーワード2", ...]"""
        result = llm_client.call_json(prompt, max_tokens=300)
        if isinstance(result, list):
            return [str(r) for r in result[:15]]
    except Exception as e:
        print(f"[Analyzer] LLMトレンド取得失敗: {e}")
    return ["AI活用", "ChatGPT", "自動化", "副業", "Notion", "Python", "プロンプト"]


def analyze_own_performance(state: dict) -> dict:
    """自社商品の売上パフォーマンスを分析する"""
    revenue = state.get("revenue", {})
    by_product = revenue.get("by_product", {})

    if not by_product:
        return {"best": None, "worst": None, "insights": ["売上データなし"]}

    sorted_products = sorted(by_product.items(), key=lambda x: x[1].get("revenue", 0), reverse=True)
    best = sorted_products[0] if sorted_products else None
    worst = sorted_products[-1] if len(sorted_products) > 1 else None

    insights = []
    if best:
        insights.append(f"最も売れている: {best[0]}（¥{best[1]['revenue']:,}）")
    if worst and worst != best:
        insights.append(f"最も売れていない: {worst[0]}（¥{worst[1]['revenue']:,}）→ 価格調整または改善を検討")

    return {"best": best, "worst": worst, "insights": insights}


def suggest_next_products(state: dict, trends: list[str]) -> list[dict]:
    """次に作るべき商品を提案する（brainのプロンプト補助）"""
    own_perf = analyze_own_performance(state)
    mem_summary = memory.summarize_for_prompt(limit=3)

    existing = state.get("products", {})
    existing_list = existing.get("published", []) + existing.get("drafts", [])

    prompt = f"""Gumroadでデジタル商品を販売するAIエージェントです。
以下のデータを基に、次に制作すべき商品を3つ提案してください。

## 市場トレンド
{', '.join(trends[:15])}

## 自社の状況
{json_str(own_perf['insights'])}

## 過去の記憶
{mem_summary}

## 既存商品（重複しないこと）
{existing_list}

## 制約
- 制作時間: 24時間以内
- 価格: ¥480〜¥4,980
- 形式: pdf / zip / notion のいずれか
- Claude APIで生成できるもの

JSON配列で出力:
[
  {{
    "theme": "商品テーマ",
    "price": 980,
    "format": "pdf",
    "target": "ターゲット層",
    "differentiator": "差別化ポイント",
    "reason": "この商品を選ぶ理由"
  }}
]"""

    try:
        suggestions = llm_client.call_json(prompt, max_tokens=1024)
        if isinstance(suggestions, list):
            return suggestions[:3]
    except Exception as e:
        print(f"[Analyzer] 商品提案エラー: {e}")
    return []


def json_str(obj) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False)
