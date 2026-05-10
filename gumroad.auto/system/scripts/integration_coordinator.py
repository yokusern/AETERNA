#!/usr/bin/env python3
"""
Gumroad.auto - 統合調整エージェント

役割: 全エージェント間の調整、優先度決定、リソース配分
出力: 日次実行計画、意思決定結果
"""

import json
from datetime import datetime
from pathlib import Path

def load_all_agent_outputs():
    """全エージェントの出力を読み込む"""
    
    data_dir = Path(__file__).parent.parent / "data"
    
    outputs = {
        "market_analysis": None,
        "content_plan": None,
        "high_price_ideas": None,
        "template_ideas": None,
        "business_models": None,
        "course_programs": None
    }
    
    # 各ファイルを読み込む
    for key, filename in [
        ("market_analysis", "market_analysis.json"),
        ("content_plan", "content_plan.json"),
        ("high_price_ideas", "high_price_ideas.json"),
        ("template_ideas", "template_ideas.json"),
        ("business_models", "business_models.json"),
        ("course_programs", "course_programs.json")
    ]:
        file_path = data_dir / filename
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    outputs[key] = data.get("ideas") or data.get("templates") or data.get("models") or data.get("courses") or data.get("planned_content") or data.get("trending_categories")
            except:
                pass
    
    return outputs

def determine_daily_priorities(agent_outputs):
    """日次の優先度を決定"""
    
    priorities = {
        "today": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "focus_area": "高単価商品の企画と実装",
            "tasks": []
        }
    }
    
    # 高単価商品から最優先タスクを抽出
    if agent_outputs["high_price_ideas"]:
        high_price_ideas = agent_outputs["high_price_ideas"]
        if isinstance(high_price_ideas, list):
            top_ideas = sorted(high_price_ideas, key=lambda x: x.get("estimated_revenue", 0), reverse=True)[:3]
            for idea in top_ideas:
                priorities["today"]["tasks"].append({
                    "type": "high_price_product",
                    "name": idea.get("theme"),
                    "priority": "high",
                    "estimated_revenue": idea.get("estimated_revenue"),
                    "deadline": idea.get("deadline", "2026-05-20"),
                    "difficulty": idea.get("implementation_difficulty", "medium")
                })
    
    # テンプレート・ツール制作タスク
    if agent_outputs["template_ideas"]:
        template_ideas = agent_outputs["template_ideas"]
        if isinstance(template_ideas, list):
            top_templates = sorted(template_ideas, key=lambda x: x.get("estimated_revenue", 0), reverse=True)[:2]
            for template in top_templates:
                priorities["today"]["tasks"].append({
                    "type": "template_creation",
                    "name": template.get("name"),
                    "priority": "high",
                    "estimated_revenue": template.get("estimated_revenue"),
                    "deadline": template.get("implementation_time", "3日"),
                    "difficulty": template.get("difficulty", "low")
                })
    
    # ビジネスモデル実装タスク
    if agent_outputs["business_models"]:
        business_models = agent_outputs["business_models"]
        if isinstance(business_models, list):
            quick_wins = [m for m in business_models if m.get("difficulty") == "low"][:2]
            for model in quick_wins:
                priorities["today"]["tasks"].append({
                    "type": "business_model",
                    "name": model.get("name"),
                    "priority": "medium",
                    "estimated_revenue": model.get("estimated_monthly_revenue"),
                    "deadline": model.get("implementation_time", "1週間"),
                    "difficulty": model.get("difficulty", "low")
                })
    
    # コース・プログラム企画タスク
    if agent_outputs["course_programs"]:
        course_programs = agent_outputs["course_programs"]
        if isinstance(course_programs, list):
            easy_courses = [c for c in course_programs if c.get("difficulty") == "low"][:1]
            for course in easy_courses:
                priorities["today"]["tasks"].append({
                    "type": "course_planning",
                    "name": course.get("name"),
                    "priority": "medium",
                    "estimated_revenue": course.get("estimated_revenue"),
                    "deadline": course.get("implementation_time", "2週間"),
                    "difficulty": course.get("difficulty", "low")
                })
    
    return priorities

def calculate_resource_allocation(priorities):
    """リソース配分を計算"""
    
    allocation = {
        "total_tasks": len(priorities["today"]["tasks"]),
        "high_priority_tasks": len([t for t in priorities["today"]["tasks"] if t["priority"] == "high"]),
        "medium_priority_tasks": len([t for t in priorities["today"]["tasks"] if t["priority"] == "medium"]),
        "resource_allocation": {
            "content_creation": 40,  # 40%
            "template_creation": 30,  # 30%
            "business_model_setup": 20,  # 20%
            "course_planning": 10   # 10%
        },
        "parallel_execution": True,
        "estimated_completion_time": "90分"
    }
    
    return allocation

def generate_decision_summary(priorities, allocation):
    """意思決定サマリーを生成"""
    
    summary = {
        "decision_date": datetime.now().isoformat(),
        "decision_summary": f"本日は{allocation['total_tasks']}個のタスクを優先度順に実行。高優先度{allocation['high_priority_tasks']}個、中優先度{allocation['medium_priority_tasks']}個。",
        "key_decisions": [
            {
                "decision": "高単価商品の企画を最優先",
                "reason": "月間売上ポテンシャルが最も高い",
                "expected_impact": "¥1,000,000以上の売上ポテンシャル"
            },
            {
                "decision": "テンプレート・ツール制作を並列実行",
                "reason": "実装難易度が低く、高速で収益化可能",
                "expected_impact": "¥1,400,000以上の売上ポテンシャル"
            },
            {
                "decision": "ビジネスモデル実装を段階的に進める",
                "reason": "継続的な収益源の構築",
                "expected_impact": "¥1,800,000以上の安定収益"
            },
            {
                "decision": "コース・プログラムの企画を開始",
                "reason": "高付加価値商品による売上拡大",
                "expected_impact": "¥3,000,000以上の売上ポテンシャル"
            }
        ],
        "next_week_focus": "全ての高単価商品とテンプレートの実装完了を目指す",
        "risk_factors": [
            "実装速度が遅れる可能性",
            "品質低下の可能性",
            "マーケティング不足"
        ],
        "mitigation_strategies": [
            "並列処理で実装速度を最大化",
            "品質チェックを自動化",
            "Gumroad内での検索・ランキング最適化に注力"
        ]
    }
    
    return summary

def save_coordination_results(priorities, allocation, summary):
    """調整結果を保存"""
    
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 日次優先度
    priorities_file = output_dir / "daily_priorities.json"
    with open(priorities_file, "w", encoding="utf-8") as f:
        json.dump(priorities, f, ensure_ascii=False, indent=2)
    
    # リソース配分
    allocation_file = output_dir / "resource_allocation.json"
    with open(allocation_file, "w", encoding="utf-8") as f:
        json.dump(allocation, f, ensure_ascii=False, indent=2)
    
    # 意思決定サマリー
    summary_file = output_dir / "coordination_decision_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    return priorities_file, allocation_file, summary_file

def main():
    """メイン処理"""
    print("🔗 Gumroad.auto - 統合調整エージェント")
    print("=" * 60)
    
    # 全エージェントの出力を読み込む
    print("\n⏳ 全エージェントの出力を読み込み中...")
    agent_outputs = load_all_agent_outputs()
    
    # 日次の優先度を決定
    print("⏳ 日次の優先度を決定中...")
    priorities = determine_daily_priorities(agent_outputs)
    
    # リソース配分を計算
    print("⏳ リソース配分を計算中...")
    allocation = calculate_resource_allocation(priorities)
    
    # 意思決定サマリーを生成
    print("⏳ 意思決定サマリーを生成中...")
    summary = generate_decision_summary(priorities, allocation)
    
    # 結果を保存
    priorities_file, allocation_file, summary_file = save_coordination_results(
        priorities, allocation, summary
    )
    
    # 結果を表示
    print(f"\n✅ 統合調整エージェント完了")
    print(f"   本日のタスク数: {allocation['total_tasks']}個")
    print(f"   高優先度: {allocation['high_priority_tasks']}個")
    print(f"   中優先度: {allocation['medium_priority_tasks']}個")
    print(f"   推定完了時間: {allocation['estimated_completion_time']}")
    
    print(f"\n📋 本日の優先タスク:")
    for i, task in enumerate(priorities["today"]["tasks"][:5], 1):
        print(f"   {i}. {task['name']}")
        print(f"      優先度: {task['priority']} | 売上: ¥{task['estimated_revenue']:,}")
    
    print(f"\n💡 主要な意思決定:")
    for decision in summary["key_decisions"]:
        print(f"   - {decision['decision']}")
        print(f"     期待効果: {decision['expected_impact']}")
    
    print(f"\n📁 出力ファイル:")
    print(f"   日次優先度: {priorities_file}")
    print(f"   リソース配分: {allocation_file}")
    print(f"   意思決定サマリー: {summary_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
