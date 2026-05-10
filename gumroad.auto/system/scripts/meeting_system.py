#!/usr/bin/env python3
"""
Gumroad.auto - AIエージェント会議システム

役割: 複数のAIエージェント間で自動的に協議し、意思決定を行う
出力: 会議決定結果（JSON）
"""

import json
import os
from datetime import datetime
from pathlib import Path

def load_agent_reports():
    """各エージェントのレポートを読み込む"""
    data_dir = Path(__file__).parent.parent / "data"
    
    reports = {
        "market_analysis": None,
        "content_plan": None,
        "sales_report": None
    }
    
    # 市場分析レポート
    market_file = data_dir / "market_analysis.json"
    if market_file.exists():
        with open(market_file, "r", encoding="utf-8") as f:
            reports["market_analysis"] = json.load(f)
    
    # コンテンツ企画
    plan_file = data_dir / "content_plan.json"
    if plan_file.exists():
        with open(plan_file, "r", encoding="utf-8") as f:
            reports["content_plan"] = json.load(f)
    
    # 販売監視レポート
    sales_file = data_dir / "sales_report.json"
    if sales_file.exists():
        with open(sales_file, "r", encoding="utf-8") as f:
            reports["sales_report"] = json.load(f)
    
    return reports

def conduct_meeting(reports):
    """
    AIエージェント会議を実施
    
    各エージェントの提案を総合的に評価し、意思決定を行う
    """
    
    meeting_log = {
        "meeting_date": datetime.now().isoformat(),
        "participants": [
            "市場分析エージェント",
            "コンテンツ企画エージェント",
            "販売監視・改善エージェント"
        ],
        "agenda": [],
        "decisions": []
    }
    
    # 市場分析エージェントからの報告
    if reports["market_analysis"]:
        market_data = reports["market_analysis"]
        meeting_log["agenda"].append({
            "speaker": "市場分析エージェント",
            "content": f"本日のトレンド分析完了。トレンドスコア最高: {market_data['trending_categories'][0]['trend_score'] if market_data['trending_categories'] else 'N/A'}"
        })
    
    # コンテンツ企画エージェントからの報告
    if reports["content_plan"]:
        plan_data = reports["content_plan"]
        planned_count = len(plan_data.get("planned_content", []))
        meeting_log["agenda"].append({
            "speaker": "コンテンツ企画エージェント",
            "content": f"{planned_count}個のコンテンツを企画。総予想売上: ¥{sum([c.get('estimated_revenue', 0) for c in plan_data.get('planned_content', [])])}円"
        })
    
    # 販売監視・改善エージェントからの報告
    if reports["sales_report"]:
        sales_data = reports["sales_report"]
        daily_sales = sales_data.get("daily_sales", [])
        if daily_sales:
            total_revenue = sum([s.get("revenue", 0) for s in daily_sales])
            meeting_log["agenda"].append({
                "speaker": "販売監視・改善エージェント",
                "content": f"本日の売上: ¥{total_revenue}円。改善提案: {len(sales_data.get('improvement_suggestions', []))}個"
            })
    
    # 意思決定
    if reports["content_plan"] and reports["content_plan"].get("planned_content"):
        next_content = reports["content_plan"]["planned_content"][0]
        meeting_log["decisions"].append({
            "decision": "次に制作するコンテンツを決定",
            "content_id": next_content.get("id"),
            "theme": next_content.get("theme"),
            "priority": next_content.get("priority"),
            "deadline": next_content.get("deadline"),
            "expected_revenue": next_content.get("estimated_revenue")
        })
    
    # 改善施策
    if reports["sales_report"] and reports["sales_report"].get("improvement_suggestions"):
        improvements = reports["sales_report"]["improvement_suggestions"][:3]  # Top 3
        meeting_log["decisions"].append({
            "decision": "改善施策を実行",
            "improvements": improvements
        })
    
    return meeting_log

def save_meeting_decision(meeting_log):
    """会議決定結果を保存"""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "meeting_decision.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(meeting_log, f, ensure_ascii=False, indent=2)
    
    return output_file

def main():
    """メイン処理"""
    print("🤝 Gumroad.auto - AIエージェント会議システム")
    print("=" * 60)
    
    # 各エージェントのレポートを読み込む
    reports = load_agent_reports()
    
    print("\n📋 参加エージェント:")
    print("   - 市場分析エージェント")
    print("   - コンテンツ企画エージェント")
    print("   - 販売監視・改善エージェント")
    
    # 会議を実施
    print("\n⏳ 会議を実施中...")
    meeting_log = conduct_meeting(reports)
    
    # 会議ログを表示
    print(f"\n✅ 会議完了")
    print(f"   参加者: {len(meeting_log['participants'])}名")
    print(f"   議題: {len(meeting_log['agenda'])}件")
    print(f"   決定: {len(meeting_log['decisions'])}件")
    
    for i, item in enumerate(meeting_log["agenda"], 1):
        print(f"\n   {i}. {item['speaker']}")
        print(f"      {item['content']}")
    
    print(f"\n📌 意思決定:")
    for decision in meeting_log["decisions"]:
        print(f"   - {decision.get('decision')}")
    
    # 会議決定結果を保存
    output_file = save_meeting_decision(meeting_log)
    
    print(f"\n📁 出力ファイル: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
