#!/usr/bin/env python3
"""
gumroad.auto エージェント実行スクリプト
デジタル製品販売の完全自動化
"""

import os
import sys
import time
import argparse
from datetime import datetime


def run_master_agent():
    """マスターエージェント実行"""
    from agents.master_agent import MasterAgent
    
    master = MasterAgent()
    result = master.run()
    return result


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='gumroad.auto - デジタル製品販売自動化')
    parser.add_argument('--daemon', action='store_true', help='デーモンモードで連続実行')
    parser.add_argument('--interval', type=int, default=24, help='デーモンモードの実行間隔（時間）')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("  🤖 gumroad.auto - デジタル製品販売自動化エンジン")
    print("=" * 70)
    
    if args.daemon:
        print(f"📡 デーモンモード: {args.interval}時間ごとに実行")
        print("=" * 70)
        
        while True:
            try:
                result = run_master_agent()
                
                # 次回実行まで待機
                wait_seconds = args.interval * 3600
                next_run = datetime.now() + datetime.timedelta(hours=args.interval)
                print(f"\n⏰ 次回実行: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   (待機中: {wait_seconds}秒)\n")
                
                time.sleep(wait_seconds)
                
            except KeyboardInterrupt:
                print("\n👋 デーモンモード終了")
                break
            except Exception as e:
                print(f"❌ エラー発生: {e}")
                time.sleep(300)  # 5分待ってから再試行
    else:
        # 単発実行
        result = run_master_agent()
        
        if result['status'] == 'success':
            print("\n✅ gumroad.auto エージェント実行完了")
            sys.exit(0)
        else:
            print("\n❌ gumroad.auto エージェント実行でエラーが発生しました")
            sys.exit(1)


if __name__ == "__main__":
    main()
