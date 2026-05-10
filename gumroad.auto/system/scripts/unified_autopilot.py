#!/usr/bin/env python3
"""
Gumroad.auto - 統一自動化パイロット

役割: 全AIエージェントを統合し、完全自動化されたパイプラインを実行
出力: 日次実行ログ、実行結果レポート、次のアクション
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_agent(agent_script_path, agent_name):
    """エージェントスクリプトを実行"""
    
    print(f"\n⏳ {agent_name} を実行中...")
    
    try:
        result = subprocess.run(
            [sys.executable, agent_script_path],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {agent_name} 完了")
            return True
        else:
            print(f"❌ {agent_name} 失敗: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ {agent_name} タイムアウト")
        return False
    except Exception as e:
        print(f"❌ {agent_name} エラー: {str(e)}")
        return False

def execute_unified_pipeline():
    """統一自動化パイプラインを実行"""
    
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 実行ログ
    execution_log = {
        "execution_date": datetime.now().isoformat(),
        "agents": [],
        "total_agents": 0,
        "successful_agents": 0,
        "failed_agents": 0,
        "total_execution_time": 0
    }
    
    start_time = datetime.now()
    
    # 実行するエージェント一覧
    agents = [
        (script_dir / "market_analyzer.py", "市場分析エージェント"),
        (script_dir / "content_planner.py", "コンテンツ企画エージェント"),
        (script_dir / "high_price_agent.py", "高単価化エージェント"),
        (script_dir / "template_creator.py", "テンプレート・ツール制作エージェント"),
        (script_dir / "business_model_agent.py", "ビジネスモデル設計エージェント"),
        (script_dir / "course_planner.py", "コース・プログラム企画エージェント"),
        (script_dir / "integration_coordinator.py", "統合調整エージェント"),
    ]
    
    # 各エージェントを実行
    for agent_script, agent_name in agents:
        if agent_script.exists():
            success = run_agent(str(agent_script), agent_name)
            
            execution_log["agents"].append({
                "name": agent_name,
                "script": agent_script.name,
                "status": "success" if success else "failed",
                "timestamp": datetime.now().isoformat()
            })
            
            execution_log["total_agents"] += 1
            if success:
                execution_log["successful_agents"] += 1
            else:
                execution_log["failed_agents"] += 1
        else:
            print(f"⚠️ {agent_name} スクリプトが見つかりません: {agent_script}")
    
    end_time = datetime.now()
    execution_log["total_execution_time"] = (end_time - start_time).total_seconds()
    
    return execution_log

def load_all_results():
    """全エージェントの結果を読み込む"""
    
    data_dir = Path(__file__).parent.parent / "data"
    
    results = {
        "high_price_potential": 0,
        "template_potential": 0,
        "business_model_potential": 0,
        "course_potential": 0,
        "total_potential": 0
    }
    
    # 高単価商品の売上ポテンシャル
    high_price_file = data_dir / "high_price_revenue_potential.json"
    if high_price_file.exists():
        with open(high_price_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            results["high_price_potential"] = data.get("potential", {}).get("total_monthly_revenue", 0)
    
    # テンプレートの売上ポテンシャル
    template_file = data_dir / "template_revenue_potential.json"
    if template_file.exists():
        with open(template_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            results["template_potential"] = data.get("potential", {}).get("total_monthly_revenue", 0)
    
    # ビジネスモデルの売上ポテンシャル
    business_file = data_dir / "business_model_revenue_potential.json"
    if business_file.exists():
        with open(business_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            results["business_model_potential"] = data.get("potential", {}).get("total_monthly_revenue", 0)
    
    # コース・プログラムの売上ポテンシャル
    course_file = data_dir / "course_revenue_potential.json"
    if course_file.exists():
        with open(course_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            results["course_potential"] = data.get("potential", {}).get("total_monthly_revenue", 0)
    
    results["total_potential"] = (
        results["high_price_potential"] +
        results["template_potential"] +
        results["business_model_potential"] +
        results["course_potential"]
    )
    
    return results

def generate_execution_report(execution_log, results):
    """実行レポートを生成"""
    
    report = {
        "report_date": datetime.now().isoformat(),
        "execution_summary": {
            "total_agents": execution_log["total_agents"],
            "successful_agents": execution_log["successful_agents"],
            "failed_agents": execution_log["failed_agents"],
            "success_rate": f"{(execution_log['successful_agents'] / execution_log['total_agents'] * 100):.1f}%" if execution_log["total_agents"] > 0 else "0%",
            "total_execution_time_seconds": execution_log["total_execution_time"]
        },
        "revenue_potential": {
            "high_price_products": f"¥{results['high_price_potential']:,}",
            "templates_tools": f"¥{results['template_potential']:,}",
            "business_models": f"¥{results['business_model_potential']:,}",
            "courses_programs": f"¥{results['course_potential']:,}",
            "total_monthly_potential": f"¥{results['total_potential']:,}"
        },
        "key_metrics": {
            "average_revenue_per_agent": f"¥{results['total_potential'] / execution_log['total_agents']:,.0f}" if execution_log["total_agents"] > 0 else "¥0",
            "total_products_services": "27+",
            "business_models_count": 6,
            "courses_programs_count": 5
        },
        "next_actions": [
            "高単価商品の実装を開始（Python講座、コンサルティング）",
            "テンプレート・ツール制作を並列実行（Google Apps Script優先）",
            "ビジネスモデル実装を段階的に進める（サブスク、アフィリエイト優先）",
            "コース・プログラムの企画を確定（営業・マーケティング効率化コース優先）",
            "Gumroad内でのマーケティング・SEO対策を強化"
        ],
        "risk_assessment": {
            "implementation_speed": "medium",
            "market_demand": "high",
            "resource_availability": "high",
            "competition": "medium"
        }
    }
    
    return report

def save_execution_results(execution_log, report):
    """実行結果を保存"""
    
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 実行ログ
    log_file = output_dir / "unified_autopilot_execution_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(execution_log, f, ensure_ascii=False, indent=2)
    
    # 実行レポート
    report_file = output_dir / "unified_autopilot_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return log_file, report_file

def main():
    """メイン処理"""
    print("🚀 Gumroad.auto - 統一自動化パイロット")
    print("=" * 60)
    print(f"実行開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 統一自動化パイプラインを実行
    print("\n⏳ 統一自動化パイプラインを実行中...")
    execution_log = execute_unified_pipeline()
    
    # 全エージェントの結果を読み込む
    print("\n⏳ 全エージェントの結果を集計中...")
    results = load_all_results()
    
    # 実行レポートを生成
    print("⏳ 実行レポートを生成中...")
    report = generate_execution_report(execution_log, results)
    
    # 結果を保存
    log_file, report_file = save_execution_results(execution_log, report)
    
    # 結果を表示
    print("\n" + "=" * 60)
    print("✅ 統一自動化パイロット完了")
    print("=" * 60)
    
    print(f"\n📊 実行サマリー:")
    print(f"   実行エージェント数: {execution_log['total_agents']}個")
    print(f"   成功: {execution_log['successful_agents']}個")
    print(f"   失敗: {execution_log['failed_agents']}個")
    print(f"   成功率: {report['execution_summary']['success_rate']}")
    print(f"   実行時間: {execution_log['total_execution_time']:.1f}秒")
    
    print(f"\n💰 売上ポテンシャル:")
    print(f"   高単価商品: {report['revenue_potential']['high_price_products']}")
    print(f"   テンプレート・ツール: {report['revenue_potential']['templates_tools']}")
    print(f"   ビジネスモデル: {report['revenue_potential']['business_models']}")
    print(f"   コース・プログラム: {report['revenue_potential']['courses_programs']}")
    print(f"   月間合計ポテンシャル: {report['revenue_potential']['total_monthly_potential']}")
    
    print(f"\n📈 主要指標:")
    print(f"   エージェント当たり平均売上: {report['key_metrics']['average_revenue_per_agent']}")
    print(f"   総商品・サービス数: {report['key_metrics']['total_products_services']}")
    
    print(f"\n📋 次のアクション:")
    for i, action in enumerate(report["next_actions"], 1):
        print(f"   {i}. {action}")
    
    print(f"\n📁 出力ファイル:")
    print(f"   実行ログ: {log_file}")
    print(f"   実行レポート: {report_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
