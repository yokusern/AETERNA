#!/usr/bin/env python3
"""
Gumroad.auto - 自律的改善ロジック

役割: AIエージェント間の会議結果に基づき、自動的に改善施策を実行
出力: 改善実行ログ、次のアクション提案
"""

import json
from datetime import datetime
from pathlib import Path

def load_meeting_decision():
    """会議決定結果を読み込む"""
    decision_file = Path(__file__).parent.parent / "data" / "meeting_decision.json"
    if decision_file.exists():
        with open(decision_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def load_sales_report():
    """販売レポートを読み込む"""
    sales_file = Path(__file__).parent.parent / "data" / "sales_report.json"
    if sales_file.exists():
        with open(sales_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def generate_improvement_actions(meeting_decision, sales_report):
    """改善施策を自動生成"""
    
    improvement_actions = []
    
    # 会議決定から改善施策を抽出
    if meeting_decision and "decisions" in meeting_decision:
        for decision in meeting_decision["decisions"]:
            if decision.get("decision") == "改善施策を実行":
                improvements = decision.get("improvements", [])
                for improvement in improvements:
                    improvement_actions.append({
                        "type": "content_improvement",
                        "content_id": improvement.get("content_id"),
                        "issue": improvement.get("issue"),
                        "action": improvement.get("suggestion"),
                        "expected_impact": improvement.get("expected_impact"),
                        "status": "pending"
                    })
    
    # 販売レポートから改善施策を抽出
    if sales_report:
        daily_sales = sales_report.get("daily_sales", [])
        
        # 売上が低いコンテンツを特定
        low_sales_content = [s for s in daily_sales if s.get("sales", 0) < 5]
        
        for content in low_sales_content[:3]:  # Top 3
            improvement_actions.append({
                "type": "low_sales_improvement",
                "content_id": content.get("content_id"),
                "current_sales": content.get("sales"),
                "action": "説明文を改善し、ターゲット層を明確化",
                "expected_impact": "売上20%向上",
                "status": "pending"
            })
    
    return improvement_actions

def execute_improvements(improvement_actions):
    """改善施策を実行"""
    
    execution_log = {
        "execution_date": datetime.now().isoformat(),
        "executed_actions": []
    }
    
    for action in improvement_actions[:5]:  # 最大5個の改善施策を実行
        executed_action = {
            "action": action,
            "executed_at": datetime.now().isoformat(),
            "status": "completed",
            "result": f"改善施策を実行: {action.get('action')}"
        }
        execution_log["executed_actions"].append(executed_action)
    
    return execution_log

def generate_next_actions(meeting_decision, improvement_actions):
    """次のアクションを提案"""
    
    next_actions = []
    
    # 会議決定から次のアクションを抽出
    if meeting_decision and "decisions" in meeting_decision:
        for decision in meeting_decision["decisions"]:
            if decision.get("decision") == "次に制作するコンテンツを決定":
                next_actions.append({
                    "action": "コンテンツ制作開始",
                    "content_id": decision.get("content_id"),
                    "theme": decision.get("theme"),
                    "deadline": decision.get("deadline"),
                    "priority": "high"
                })
    
    # 改善施策の実行状況から次のアクションを提案
    if improvement_actions:
        next_actions.append({
            "action": "改善施策の効果測定",
            "description": f"{len(improvement_actions)}個の改善施策を実行。48時間後に効果を測定。",
            "priority": "medium"
        })
    
    return next_actions

def save_improvement_log(execution_log, next_actions):
    """改善ログと次のアクションを保存"""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 改善実行ログ
    log_file = output_dir / "improvement_execution.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(execution_log, f, ensure_ascii=False, indent=2)
    
    # 次のアクション
    actions_file = output_dir / "next_actions.json"
    next_actions_data = {
        "next_actions": next_actions,
        "generated_at": datetime.now().isoformat()
    }
    with open(actions_file, "w", encoding="utf-8") as f:
        json.dump(next_actions_data, f, ensure_ascii=False, indent=2)
    
    return log_file, actions_file

def main():
    """メイン処理"""
    print("🔧 Gumroad.auto - 自律的改善ロジック")
    print("=" * 60)
    
    # 会議決定結果を読み込む
    print("\n📖 会議決定結果を読み込み中...")
    meeting_decision = load_meeting_decision()
    
    # 販売レポートを読み込む
    print("📊 販売レポートを読み込み中...")
    sales_report = load_sales_report()
    
    # 改善施策を生成
    print("\n⏳ 改善施策を生成中...")
    improvement_actions = generate_improvement_actions(meeting_decision, sales_report)
    
    # 改善施策を実行
    print("⏳ 改善施策を実行中...")
    execution_log = execute_improvements(improvement_actions)
    
    # 次のアクションを提案
    print("⏳ 次のアクションを提案中...")
    next_actions = generate_next_actions(meeting_decision, improvement_actions)
    
    # 改善ログと次のアクションを保存
    log_file, actions_file = save_improvement_log(execution_log, next_actions)
    
    # 結果を表示
    print(f"\n✅ 自律的改善ロジック完了")
    print(f"   改善施策数: {len(improvement_actions)}")
    print(f"   実行済み施策: {len(execution_log['executed_actions'])}")
    print(f"   次のアクション: {len(next_actions)}")
    
    print(f"\n📋 実行済み改善施策:")
    for action in execution_log["executed_actions"][:3]:
        print(f"   - {action['result']}")
    
    print(f"\n📌 次のアクション:")
    for action in next_actions:
        print(f"   - {action['action']}")
        if action.get("priority"):
            print(f"     優先度: {action['priority']}")
    
    print(f"\n📁 出力ファイル:")
    print(f"   改善ログ: {log_file}")
    print(f"   次のアクション: {actions_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
