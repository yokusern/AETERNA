"""
analytics_agent.py - 分析・改善エージェント
Gumroad売上データを分析し、改善提案とレポートを生成する
"""
import os
import sys
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from gumroad_uploader import GumroadUploader


DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
SALES_DIR = DATA_DIR / "sales"


def fetch_sales(days: int = 7) -> list:
    """Gumroadから売上データを取得する"""
    uploader = GumroadUploader()
    after = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return uploader.get_sales(after=after)


def save_sales_csv(sales: list, date_str: str):
    """売上データをCSVに保存する"""
    SALES_DIR.mkdir(parents=True, exist_ok=True)
    path = SALES_DIR / f"{date_str}.csv"
    if not sales:
        path.write_text("no_sales\n")
        return

    fieldnames = ["created_at", "product_name", "price", "email", "country"]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sales)
    print(f"売上CSV保存: {path}")


def analyze(sales: list) -> dict:
    """売上データを分析する"""
    if not sales:
        return {
            "total_revenue": 0,
            "total_sales": 0,
            "products": {},
            "insights": ["売上データなし。商品を公開しているか確認してください。"],
            "recommendations": ["Gumroadの商品ページSEOを最適化する", "SNSで商品を告知する"],
        }

    total_revenue = sum(s.get("price", 0) for s in sales)
    product_stats = {}
    for s in sales:
        name = s.get("product_name", "Unknown")
        if name not in product_stats:
            product_stats[name] = {"count": 0, "revenue": 0}
        product_stats[name]["count"] += 1
        product_stats[name]["revenue"] += s.get("price", 0)

    sorted_products = sorted(product_stats.items(), key=lambda x: x[1]["revenue"], reverse=True)
    top_product = sorted_products[0][0] if sorted_products else None

    insights = [
        f"総売上: ¥{total_revenue:,}（{len(sales)}件）",
        f"最も売れた商品: {top_product}" if top_product else "売上なし",
        f"商品数: {len(product_stats)}種類",
    ]

    recommendations = []
    if total_revenue < 10000:
        recommendations.append("商品ページのキャッチコピーをA/Bテストする")
        recommendations.append("SNSで商品紹介投稿を週2回行う")
    if len(product_stats) < 5:
        recommendations.append("商品ラインナップを増やす（類似商品の横展開）")
    if top_product:
        recommendations.append(f"「{top_product}」の関連商品を追加制作する")

    return {
        "total_revenue": total_revenue,
        "total_sales": len(sales),
        "products": dict(sorted_products),
        "insights": insights,
        "recommendations": recommendations,
        "analyzed_at": datetime.now().isoformat(),
    }


def generate_report(analysis: dict, date_str: str) -> str:
    """分析結果からMarkdownレポートを生成する"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{date_str}.md"

    lines = [
        f"# 売上分析レポート - {date_str}",
        "",
        "## サマリー",
        f"- 総売上: **¥{analysis['total_revenue']:,}**",
        f"- 総販売数: **{analysis['total_sales']}件**",
        "",
        "## 洞察",
    ]
    for insight in analysis["insights"]:
        lines.append(f"- {insight}")

    lines += ["", "## 商品別売上"]
    for name, stats in analysis["products"].items():
        lines.append(f"- {name}: ¥{stats['revenue']:,}（{stats['count']}件）")

    lines += ["", "## 改善提案"]
    for rec in analysis["recommendations"]:
        lines.append(f"- [ ] {rec}")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"レポート保存: {report_path}")
    return str(report_path)


def notify_discord(analysis: dict, webhook_url: str):
    """Discord Webhookに週次サマリーを送信する"""
    import requests
    message = (
        f"📊 **週次売上レポート**\n"
        f"売上: ¥{analysis['total_revenue']:,} | 件数: {analysis['total_sales']}件\n"
        f"改善提案: {analysis['recommendations'][0] if analysis['recommendations'] else 'なし'}"
    )
    try:
        resp = requests.post(webhook_url, json={"content": message}, timeout=10)
        resp.raise_for_status()
        print("Discord通知送信完了")
    except Exception as e:
        print(f"Discord通知エラー: {e}")


def run():
    print("=== Analytics Agent 起動 ===")
    date_str = datetime.now().strftime("%Y-%m-%d")

    sales = fetch_sales(days=7)
    save_sales_csv(sales, date_str)

    analysis = analyze(sales)
    report_path = generate_report(analysis, date_str)

    # 分析結果をJSONで保存（他エージェントが参照）
    analysis_path = DATA_DIR / "latest_analysis.json"
    analysis_path.parent.mkdir(parents=True, exist_ok=True)
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)

    # Discord通知（設定されている場合）
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if webhook_url:
        notify_discord(analysis, webhook_url)

    print(f"\n分析完了: 売上¥{analysis['total_revenue']:,} / {analysis['total_sales']}件")
    return analysis


if __name__ == "__main__":
    run()
