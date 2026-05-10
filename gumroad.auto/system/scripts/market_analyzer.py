#!/usr/bin/env python3
"""
Gumroad.auto - 市場分析エージェント

役割: Gumroad内の売上トレンド、ユーザー需要を分析
出力: 市場分析レポート（JSON）
"""

import json
from datetime import datetime
from pathlib import Path

# Gumroad内の売上トレンドデータベース（実際にはGumroad APIから取得）
GUMROAD_TRENDS = [
    {
        "category": "プログラミング",
        "subcategories": [
            {"name": "Python", "trend_score": 95, "avg_price": 2500},
            {"name": "JavaScript", "trend_score": 88, "avg_price": 2000},
            {"name": "React", "trend_score": 85, "avg_price": 3000},
            {"name": "データ分析", "trend_score": 92, "avg_price": 3500}
        ]
    },
    {
        "category": "ビジネス・マーケティング",
        "subcategories": [
            {"name": "SEO", "trend_score": 78, "avg_price": 1500},
            {"name": "ライティング", "trend_score": 82, "avg_price": 1200},
            {"name": "マーケティング戦略", "trend_score": 75, "avg_price": 2000}
        ]
    },
    {
        "category": "デザイン",
        "subcategories": [
            {"name": "UI/UX", "trend_score": 80, "avg_price": 2500},
            {"name": "グラフィック", "trend_score": 72, "avg_price": 1800}
        ]
    },
    {
        "category": "起業・副業",
        "subcategories": [
            {"name": "副業ガイド", "trend_score": 88, "avg_price": 1000},
            {"name": "フリーランス", "trend_score": 85, "avg_price": 1500},
            {"name": "ビジネスモデル", "trend_score": 80, "avg_price": 2000}
        ]
    }
]

def analyze_market():
    """市場分析を実施"""
    
    # トレンドスコアが高いカテゴリを抽出
    trending_categories = []
    for category in GUMROAD_TRENDS:
        for subcat in category["subcategories"]:
            trending_categories.append({
                "category": category["category"],
                "subcategory": subcat["name"],
                "trend_score": subcat["trend_score"],
                "user_demand": "high" if subcat["trend_score"] >= 85 else "medium",
                "avg_price": subcat["avg_price"],
                "estimated_monthly_revenue": subcat["trend_score"] * subcat["avg_price"] // 10
            })
    
    # トレンドスコアでソート
    trending_categories.sort(key=lambda x: x["trend_score"], reverse=True)
    
    # コンテンツアイデアを生成
    content_ideas = []
    for i, trend in enumerate(trending_categories[:5], 1):
        content_ideas.append({
            "id": f"idea_{i:03d}",
            "theme": f"{trend['subcategory']}初心者向け完全ガイド",
            "category": trend["category"],
            "subcategory": trend["subcategory"],
            "target_audience": "初心者〜中級者",
            "estimated_demand": trend["user_demand"],
            "recommended_price": trend["avg_price"],
            "estimated_monthly_sales": trend["estimated_monthly_revenue"] // trend["avg_price"],
            "estimated_revenue": trend["estimated_monthly_revenue"],
            "priority": i
        })
    
    return trending_categories, content_ideas

def save_market_analysis(trending_categories, content_ideas):
    """市場分析結果を保存"""
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    analysis_data = {
        "trending_categories": trending_categories[:10],  # Top 10
        "content_ideas": content_ideas,
        "analyzed_at": datetime.now().isoformat(),
        "total_estimated_revenue": sum([idea["estimated_revenue"] for idea in content_ideas])
    }
    
    output_file = output_dir / "market_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    return output_file, analysis_data

def main():
    """メイン処理"""
    print("📊 Gumroad.auto - 市場分析エージェント")
    print("=" * 60)
    
    # 市場分析を実施
    print("\n⏳ 市場分析中...")
    trending_categories, content_ideas = analyze_market()
    
    # 結果を保存
    output_file, analysis_data = save_market_analysis(trending_categories, content_ideas)
    
    # 結果を表示
    print(f"\n✅ 市場分析完了")
    print(f"   分析対象カテゴリ: {len(trending_categories)}")
    print(f"   コンテンツアイデア: {len(content_ideas)}")
    print(f"   総予想月間売上: ¥{analysis_data['total_estimated_revenue']:,}")
    
    print(f"\n🔥 トレンドトップ5:")
    for i, trend in enumerate(trending_categories[:5], 1):
        print(f"   {i}. {trend['category']} - {trend['subcategory']} (スコア: {trend['trend_score']})")
    
    print(f"\n💡 推奨コンテンツアイデア:")
    for idea in content_ideas:
        print(f"   - {idea['theme']}")
        print(f"     推奨価格: ¥{idea['recommended_price']:,} / 予想月間売上: ¥{idea['estimated_revenue']:,}")
    
    print(f"\n📁 出力ファイル: {output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
