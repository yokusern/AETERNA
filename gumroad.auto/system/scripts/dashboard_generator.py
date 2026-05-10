#!/usr/bin/env python3
"""
Gumroad.auto - CEO向けダッシュボード自動生成システム

役割: 週次ダッシュボードとレポートを自動生成
出力: CEO向けの週次レポート（Markdown）、ダッシュボードデータ（JSON）
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def load_all_data():
    """全てのデータを読み込む"""
    data_dir = Path(__file__).parent.parent / "data"
    
    data = {
        "market_analysis": None,
        "content_plan": None,
        "meeting_decision": None,
        "improvement_execution": None,
        "next_actions": None,
        "sales_report": None
    }
    
    # 各ファイルを読み込む
    for key, filename in [
        ("market_analysis", "market_analysis.json"),
        ("content_plan", "content_plan.json"),
        ("meeting_decision", "meeting_decision.json"),
        ("improvement_execution", "improvement_execution.json"),
        ("next_actions", "next_actions.json"),
        ("sales_report", "sales_report.json")
    ]:
        file_path = data_dir / filename
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
    
    return data

def generate_dashboard_data(data):
    """ダッシュボードデータを生成"""
    
    dashboard = {
        "generated_at": datetime.now().isoformat(),
        "week_start": (datetime.now() - timedelta(days=datetime.now().weekday())).isoformat(),
        "week_end": (datetime.now() + timedelta(days=6 - datetime.now().weekday())).isoformat(),
        "summary": {
            "total_revenue": 0,
            "content_count": 0,
            "avg_rating": 0,
            "improvement_count": 0
        },
        "content_status": [],
        "top_contents": [],
        "improvement_actions": [],
        "next_week_plan": []
    }
    
    # 売上データから集計
    if data["sales_report"]:
        daily_sales = data["sales_report"].get("daily_sales", [])
        dashboard["summary"]["total_revenue"] = sum([s.get("revenue", 0) for s in daily_sales])
        dashboard["summary"]["avg_rating"] = sum([s.get("avg_rating", 0) for s in daily_sales]) / len(daily_sales) if daily_sales else 0
    
    # コンテンツ企画から集計
    if data["content_plan"]:
        dashboard["summary"]["content_count"] = len(data["content_plan"].get("planned_content", []))
    
    # 改善施策から集計
    if data["improvement_execution"]:
        dashboard["summary"]["improvement_count"] = len(data["improvement_execution"].get("executed_actions", []))
    
    # コンテンツ状況
    if data["content_plan"]:
        for content in data["content_plan"].get("planned_content", [])[:5]:
            dashboard["content_status"].append({
                "id": content.get("id"),
                "theme": content.get("theme"),
                "status": content.get("status"),
                "estimated_revenue": content.get("estimated_revenue"),
                "deadline": content.get("deadline")
            })
    
    # 次週の計画
    if data["next_actions"]:
        dashboard["next_week_plan"] = data["next_actions"].get("next_actions", [])[:5]
    
    return dashboard

def generate_weekly_report(data, dashboard):
    """週次レポートを生成"""
    
    report = f"""# Gumroad事業部 週次レポート

**生成日**: {datetime.now().strftime('%Y年%m月%d日')}  
**対象期間**: {dashboard['week_start'][:10]} 〜 {dashboard['week_end'][:10]}

---

## 📊 売上サマリー

| 指標 | 数値 |
|---|---|
| **週間売上** | ¥{dashboard['summary']['total_revenue']:,} |
| **コンテンツ数** | {dashboard['summary']['content_count']}個 |
| **平均評価** | {dashboard['summary']['avg_rating']:.1f}/5.0 |
| **実行改善施策** | {dashboard['summary']['improvement_count']}個 |

---

## 📝 コンテンツ状況

"""
    
    if dashboard["content_status"]:
        report += "| テーマ | 状態 | 予想売上 | 期限 |\n"
        report += "|---|---|---|---|\n"
        for content in dashboard["content_status"]:
            report += f"| {content['theme']} | {content['status']} | ¥{content['estimated_revenue']:,} | {content['deadline'][:10]} |\n"
    else:
        report += "（コンテンツ情報なし）\n"
    
    report += "\n---\n\n## 🔍 市場分析結果\n\n"
    
    if data["market_analysis"]:
        trending = data["market_analysis"].get("trending_categories", [])[:3]
        report += "**トレンドトップ3:**\n\n"
        for i, trend in enumerate(trending, 1):
            report += f"{i}. {trend.get('category')} - {trend.get('subcategory')} (スコア: {trend.get('trend_score')})\n"
    
    report += "\n---\n\n## 🤝 AI会議の決定\n\n"
    
    if data["meeting_decision"]:
        decisions = data["meeting_decision"].get("decisions", [])
        for decision in decisions[:3]:
            report += f"- **{decision.get('decision')}**\n"
            if decision.get("theme"):
                report += f"  テーマ: {decision.get('theme')}\n"
            if decision.get("expected_revenue"):
                report += f"  予想売上: ¥{decision.get('expected_revenue'):,}\n"
    
    report += "\n---\n\n## 🔧 実行済み改善施策\n\n"
    
    if data["improvement_execution"]:
        actions = data["improvement_execution"].get("executed_actions", [])[:3]
        for action in actions:
            report += f"- {action.get('result')}\n"
    
    report += "\n---\n\n## 📌 来週の計画\n\n"
    
    if dashboard["next_week_plan"]:
        for action in dashboard["next_week_plan"][:3]:
            report += f"- {action.get('action')}\n"
            if action.get("priority"):
                report += f"  優先度: {action.get('priority')}\n"
    
    report += "\n---\n\n## 💡 参謀からのコメント\n\n"
    report += "本週のGumroad事業部は、市場分析に基づくコンテンツ企画と自律的改善ロジックが正常に稼働しています。\n\n"
    report += "AIエージェント間の会議により、最適なコンテンツ制作スケジュールが自動決定されています。\n\n"
    report += "来週は、実行済み改善施策の効果測定と、新規コンテンツの制作に注力します。\n\n"
    report += "**目標**: 月間50万円売上達成に向け、現在のペースを維持・加速させます。\n"
    
    return report

def save_dashboard_and_report(dashboard, report):
    """ダッシュボードとレポートを保存"""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # ダッシュボードデータ（JSON）
    dashboard_file = output_dir / "dashboard.json"
    with open(dashboard_file, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    # 週次レポート（Markdown）
    report_file = output_dir / "weekly_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    return dashboard_file, report_file

def main():
    """メイン処理"""
    print("📊 Gumroad.auto - CEO向けダッシュボード自動生成システム")
    print("=" * 60)
    
    # 全てのデータを読み込む
    print("\n📖 データを読み込み中...")
    data = load_all_data()
    
    # ダッシュボードデータを生成
    print("⏳ ダッシュボードデータを生成中...")
    dashboard = generate_dashboard_data(data)
    
    # 週次レポートを生成
    print("⏳ 週次レポートを生成中...")
    report = generate_weekly_report(data, dashboard)
    
    # ダッシュボードとレポートを保存
    dashboard_file, report_file = save_dashboard_and_report(dashboard, report)
    
    # 結果を表示
    print(f"\n✅ ダッシュボード・レポート生成完了")
    print(f"   週間売上: ¥{dashboard['summary']['total_revenue']:,}")
    print(f"   コンテンツ数: {dashboard['summary']['content_count']}個")
    print(f"   平均評価: {dashboard['summary']['avg_rating']:.1f}/5.0")
    print(f"   実行改善施策: {dashboard['summary']['improvement_count']}個")
    
    print(f"\n📁 出力ファイル:")
    print(f"   ダッシュボード: {dashboard_file}")
    print(f"   週次レポート: {report_file}")
    
    print(f"\n📄 週次レポート プレビュー:")
    print("=" * 60)
    print(report[:500] + "...")
    print("=" * 60)

if __name__ == "__main__":
    main()
