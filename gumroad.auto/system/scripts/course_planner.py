#!/usr/bin/env python3
"""
Gumroad.auto - コース・プログラム企画エージェント

役割: 複数のコンテンツを組み合わせた「コース」「プログラム」を企画
出力: コース企画書、カリキュラム設計
"""

import json
from datetime import datetime
from pathlib import Path

def plan_course_programs():
    """複数コンテンツを組み合わせたコース・プログラムを企画"""
    
    course_programs = [
        {
            "id": "course_001",
            "name": "Python完全マスターコース",
            "description": "Python初心者から実務レベルまで、段階的に習得できる包括的なコース",
            "price": 19800,
            "estimated_sales_per_month": 30,
            "estimated_revenue": 594000,
            "duration": "3ヶ月",
            "level": "初心者→中級者",
            "contents": [
                {
                    "order": 1,
                    "name": "Python初心者向け完全ガイド",
                    "type": "電子書籍",
                    "hours": 5
                },
                {
                    "order": 2,
                    "name": "データ分析完全ガイド",
                    "type": "電子書籍",
                    "hours": 8
                },
                {
                    "order": 3,
                    "name": "実践プロジェクトテンプレート",
                    "type": "テンプレート",
                    "hours": 3
                },
                {
                    "order": 4,
                    "name": "質問サポート（30日間）",
                    "type": "サポート",
                    "hours": "無制限"
                }
            ],
            "target_audience": "Python を本気で習得したい初心者",
            "expected_outcome": "実務レベルのPythonスキル習得",
            "implementation_time": "2週間",
            "difficulty": "medium"
        },
        {
            "id": "course_002",
            "name": "データ分析エキスパートプログラム",
            "description": "データ分析の基礎から応用、実務プロジェクト実装まで",
            "price": 24800,
            "estimated_sales_per_month": 25,
            "estimated_revenue": 620000,
            "duration": "4ヶ月",
            "level": "初心者→上級者",
            "contents": [
                {
                    "order": 1,
                    "name": "データ分析完全ガイド",
                    "type": "電子書籍",
                    "hours": 8
                },
                {
                    "order": 2,
                    "name": "業界別データ分析完全ガイド",
                    "type": "電子書籍",
                    "hours": 10
                },
                {
                    "order": 3,
                    "name": "データ分析テンプレート（Google Sheets）",
                    "type": "テンプレート",
                    "hours": 4
                },
                {
                    "order": 4,
                    "name": "実践プロジェクト実装サポート",
                    "type": "サポート",
                    "hours": "無制限"
                },
                {
                    "order": 5,
                    "name": "修了証書",
                    "type": "認定",
                    "hours": 0
                }
            ],
            "target_audience": "データ分析スキルを本気で習得したい人",
            "expected_outcome": "実務レベルのデータ分析スキル、修了証書",
            "implementation_time": "3週間",
            "difficulty": "high"
        },
        {
            "id": "course_003",
            "name": "起業家向け業務自動化マスターコース",
            "description": "Google Apps Script を使った業務自動化で時間を100時間削減",
            "price": 14800,
            "estimated_sales_per_month": 40,
            "estimated_revenue": 592000,
            "duration": "6週間",
            "level": "初心者→中級者",
            "contents": [
                {
                    "order": 1,
                    "name": "Google Apps Script - メール自動送信ツール",
                    "type": "ツール",
                    "hours": 3
                },
                {
                    "order": 2,
                    "name": "Google Apps Script - データ自動集計ツール",
                    "type": "ツール",
                    "hours": 4
                },
                {
                    "order": 3,
                    "name": "業務自動化Pythonスクリプト集",
                    "type": "スクリプト集",
                    "hours": 5
                },
                {
                    "order": 4,
                    "name": "カスタマイズサポート（30日間）",
                    "type": "サポート",
                    "hours": "無制限"
                }
            ],
            "target_audience": "起業家、フリーランス、忙しいビジネスパーソン",
            "expected_outcome": "月間100時間の業務時間削減",
            "implementation_time": "2週間",
            "difficulty": "medium"
        },
        {
            "id": "course_004",
            "name": "営業・マーケティング効率化コース",
            "description": "テンプレートとツールで営業・マーケティング業務を50%削減",
            "price": 12800,
            "estimated_sales_per_month": 50,
            "estimated_revenue": 640000,
            "duration": "4週間",
            "level": "初心者→中級者",
            "contents": [
                {
                    "order": 1,
                    "name": "営業管理テンプレート（Excel）",
                    "type": "テンプレート",
                    "hours": 2
                },
                {
                    "order": 2,
                    "name": "顧客管理テンプレート（Notion）",
                    "type": "テンプレート",
                    "hours": 2
                },
                {
                    "order": 3,
                    "name": "SNS投稿スケジュール管理（Notion）",
                    "type": "テンプレート",
                    "hours": 1
                },
                {
                    "order": 4,
                    "name": "コンテンツカレンダー＆分析テンプレート",
                    "type": "テンプレート",
                    "hours": 2
                },
                {
                    "order": 5,
                    "name": "実装サポート（30日間）",
                    "type": "サポート",
                    "hours": "無制限"
                }
            ],
            "target_audience": "営業、マーケター、チームリーダー",
            "expected_outcome": "営業・マーケティング業務の50%削減",
            "implementation_time": "2週間",
            "difficulty": "low"
        },
        {
            "id": "course_005",
            "name": "HR・採用担当者向け効率化コース",
            "description": "採用業務とHR業務を自動化・効率化するテンプレート・ツール集",
            "price": 9800,
            "estimated_sales_per_month": 35,
            "estimated_revenue": 343000,
            "duration": "3週間",
            "level": "初心者",
            "contents": [
                {
                    "order": 1,
                    "name": "面接評価テンプレート（Excel）",
                    "type": "テンプレート",
                    "hours": 1
                },
                {
                    "order": 2,
                    "name": "採用管理テンプレート（Google Sheets）",
                    "type": "テンプレート",
                    "hours": 2
                },
                {
                    "order": 3,
                    "name": "Google Apps Script - 採用通知自動送信ツール",
                    "type": "ツール",
                    "hours": 2
                },
                {
                    "order": 4,
                    "name": "HR業務効率化ガイド",
                    "type": "ガイド",
                    "hours": 1
                }
            ],
            "target_audience": "HR、採用担当者、人事部",
            "expected_outcome": "採用・HR業務の40%削減",
            "implementation_time": "1週間",
            "difficulty": "low"
        }
    ]
    
    return course_programs

def generate_launch_strategy(course_programs):
    """コース・プログラムの立ち上げ戦略を生成"""
    
    strategy = {
        "phase_1": {
            "deadline": "2026-05-25",
            "courses": [
                course_programs[3],  # 営業・マーケティング効率化
                course_programs[4]   # HR・採用担当者向け効率化
            ],
            "reason": "実装難易度が低く、需要が高い",
            "expected_revenue": 983000
        },
        "phase_2": {
            "deadline": "2026-06-05",
            "courses": [
                course_programs[2]   # 起業家向け業務自動化
            ],
            "reason": "中程度の実装難易度、高い売上ポテンシャル",
            "expected_revenue": 592000
        },
        "phase_3": {
            "deadline": "2026-06-20",
            "courses": [
                course_programs[0]   # Python完全マスター
            ],
            "reason": "高度な実装、高い付加価値",
            "expected_revenue": 594000
        },
        "phase_4": {
            "deadline": "2026-07-10",
            "courses": [
                course_programs[1]   # データ分析エキスパート
            ],
            "reason": "最も高度な実装、最高の売上ポテンシャル",
            "expected_revenue": 620000
        }
    }
    
    return strategy

def calculate_total_potential(course_programs):
    """総売上ポテンシャルを計算"""
    
    total_revenue = sum([c["estimated_revenue"] for c in course_programs])
    
    breakdown_by_level = {}
    for course in course_programs:
        level = course["level"]
        if level not in breakdown_by_level:
            breakdown_by_level[level] = 0
        breakdown_by_level[level] += course["estimated_revenue"]
    
    breakdown_by_duration = {}
    for course in course_programs:
        duration = course["duration"]
        if duration not in breakdown_by_duration:
            breakdown_by_duration[duration] = 0
        breakdown_by_duration[duration] += course["estimated_revenue"]
    
    return {
        "total_monthly_revenue": total_revenue,
        "courses_count": len(course_programs),
        "average_per_course": total_revenue / len(course_programs),
        "breakdown_by_level": breakdown_by_level,
        "breakdown_by_duration": breakdown_by_duration
    }

def save_course_programs(course_programs, strategy, potential):
    """コース・プログラム情報を保存"""
    
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # コース・プログラム一覧
    courses_file = output_dir / "course_programs.json"
    with open(courses_file, "w", encoding="utf-8") as f:
        json.dump({
            "courses": course_programs,
            "generated_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    # 立ち上げ戦略
    strategy_file = output_dir / "course_launch_strategy.json"
    with open(strategy_file, "w", encoding="utf-8") as f:
        json.dump({
            "strategy": strategy,
            "generated_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    # 売上ポテンシャル
    potential_file = output_dir / "course_revenue_potential.json"
    with open(potential_file, "w", encoding="utf-8") as f:
        json.dump({
            "potential": potential,
            "generated_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    return courses_file, strategy_file, potential_file

def main():
    """メイン処理"""
    print("🎓 Gumroad.auto - コース・プログラム企画エージェント")
    print("=" * 60)
    
    # コース・プログラムを企画
    print("\n⏳ コース・プログラムを企画中...")
    course_programs = plan_course_programs()
    
    # 立ち上げ戦略を生成
    print("⏳ 立ち上げ戦略を生成中...")
    strategy = generate_launch_strategy(course_programs)
    
    # 売上ポテンシャルを計算
    print("⏳ 売上ポテンシャルを計算中...")
    potential = calculate_total_potential(course_programs)
    
    # 結果を保存
    courses_file, strategy_file, potential_file = save_course_programs(
        course_programs, strategy, potential
    )
    
    # 結果を表示
    print(f"\n✅ コース・プログラム企画エージェント完了")
    print(f"   コース・プログラム数: {len(course_programs)}個")
    print(f"   月間売上ポテンシャル: ¥{potential['total_monthly_revenue']:,}")
    print(f"   平均単価: ¥{potential['average_per_course']:,.0f}")
    
    print(f"\n📊 レベル別売上:")
    for level, revenue in potential['breakdown_by_level'].items():
        print(f"   {level}: ¥{revenue:,}")
    
    print(f"\n📋 コース・プログラムトップ3:")
    sorted_courses = sorted(course_programs, key=lambda x: x["estimated_revenue"], reverse=True)
    for i, course in enumerate(sorted_courses[:3], 1):
        print(f"   {i}. {course['name']} (¥{course['estimated_revenue']:,})")
    
    print(f"\n📁 出力ファイル:")
    print(f"   コース・プログラム一覧: {courses_file}")
    print(f"   立ち上げ戦略: {strategy_file}")
    print(f"   売上ポテンシャル: {potential_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
