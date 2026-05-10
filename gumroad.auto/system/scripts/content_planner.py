#!/usr/bin/env python3
"""
Gumroad.auto - コンテンツ企画エージェント

役割: 市場分析結果に基づき、売れるコンテンツの企画を決定
出力: コンテンツ企画書（JSON）
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

def load_market_analysis():
    """市場分析結果を読み込む"""
    analysis_file = Path(__file__).parent.parent / "data" / "market_analysis.json"
    if analysis_file.exists():
        with open(analysis_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def plan_content(market_analysis):
    """コンテンツ企画を作成"""
    
    if not market_analysis:
        return []
    
    content_ideas = market_analysis.get("content_ideas", [])
    planned_content = []
    
    for idea in content_ideas[:5]:  # Top 5アイデアを企画
        # 制作期間を見積もり
        if idea["estimated_demand"] == "high":
            production_days = 3
        else:
            production_days = 5
        
        deadline = datetime.now() + timedelta(days=production_days)
        
        planned_content.append({
            "id": idea["id"],
            "theme": idea["theme"],
            "category": idea["category"],
            "subcategory": idea["subcategory"],
            "description": f"{idea['subcategory']}の基礎から実践まで、初心者向けの完全ガイド。実例、テンプレート、チェックリストを含む。",
            "target_audience": idea["target_audience"],
            "content_type": "ebook",  # または "template", "guide"
            "estimated_pages": 80 if idea["estimated_demand"] == "high" else 60,
            "recommended_price": idea["recommended_price"],
            "estimated_sales": idea["estimated_monthly_sales"],
            "estimated_revenue": idea["estimated_revenue"],
            "priority": idea["priority"],
            "deadline": deadline.isoformat(),
            "status": "planned"
        })
    
    return planned_content

def save_content_plan(planned_content):
    """コンテンツ企画を保存"""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    plan_data = {
        "planned_content": planned_content,
        "total_planned_revenue": sum([c["estimated_revenue"] for c in planned_content]),
        "planned_at": datetime.now().isoformat()
    }
    
    output_file = output_dir / "content_plan.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, ensure_ascii=False, indent=2)
    
    return output_file, plan_data

def main():
    """メイン処理"""
    print("📋 Gumroad.auto - コンテンツ企画エージェント")
    print("=" * 60)
    
    # 市場分析結果を読み込む
    print("\n📖 市場分析結果を読み込み中...")
    market_analysis = load_market_analysis()
    
    if not market_analysis:
        print("❌ 市場分析結果が見つかりません。market_analyzer.pyを先に実行してください。")
        return
    
    # コンテンツ企画を作成
    print("\n⏳ コンテンツ企画を作成中...")
    planned_content = plan_content(market_analysis)
    
    # 企画を保存
    output_file, plan_data = save_content_plan(planned_content)
    
    # 結果を表示
    print(f"\n✅ コンテンツ企画完了")
    print(f"   企画数: {len(planned_content)}")
    print(f"   総予想売上: ¥{plan_data['total_planned_revenue']:,}")
    
    print(f"\n📝 企画内容:")
    for content in planned_content:
        print(f"   {content['priority']}. {content['theme']}")
        print(f"      推奨価格: ¥{content['recommended_price']:,}")
        print(f"      予想売上: ¥{content['estimated_revenue']:,}")
        print(f"      期限: {content['deadline'][:10]}")
    
    print(f"\n📁 出力ファイル: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
