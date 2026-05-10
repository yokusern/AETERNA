#!/usr/bin/env python3
"""
Gumroad.auto - 日次自動パイロット

役割: 毎日20時に全てのエージェント処理を自動実行
出力: 各エージェントの処理結果、CEO向けダッシュボード
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_agent(script_name, agent_name):
    """エージェントスクリプトを実行"""
    print(f"\n▶️  {agent_name}を実行中...")
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(f"✅ {agent_name}完了")
            return True
        else:
            print(f"❌ {agent_name}失敗")
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  {agent_name}タイムアウト")
        return False
    except Exception as e:
        print(f"❌ {agent_name}エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🤖 Gumroad.auto - 日次自動パイロット")
    print("=" * 60)
    print(f"実行時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
    print("=" * 60)
    
    # エージェント実行順序
    agents = [
        ("market_analyzer.py", "市場分析エージェント"),
        ("content_planner.py", "コンテンツ企画エージェント"),
        ("meeting_system.py", "AIエージェント会議システム"),
        ("autonomous_improvement.py", "自律的改善ロジック"),
        ("dashboard_generator.py", "CEO向けダッシュボード生成")
    ]
    
    # 各エージェントを実行
    results = {}
    for script, agent_name in agents:
        results[script] = run_agent(script, agent_name)
    
    # 実行結果をサマリー
    print("\n" + "=" * 60)
    print("📊 実行結果サマリー")
    print("=" * 60)
    
    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n✅ 成功: {success_count}/{total_count}")
    
    for script, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {script}")
    
    # 最終メッセージ
    print("\n" + "=" * 60)
    if success_count == total_count:
        print("🎉 全てのエージェント処理が正常に完了しました！")
        print("CEO向けダッシュボードが更新されました。")
    else:
        print(f"⚠️  {total_count - success_count}個のエージェント処理に失敗しました。")
        print("ログを確認してください。")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
