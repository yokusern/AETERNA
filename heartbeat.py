"""
heartbeat.py — AETERNA帝国の鼓動
このスクリプトを実行することで、CEO AIが自律サイクルを開始します。
"""
import time
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from core import brain

def main():
    print("AETERNA Eternal Execution Loop started.")
    print("Press Ctrl+C to stop the empire.")
    
    while True:
        try:
            brain.run()
            # 1サイクル終了後、2時間待機（調整可能）
            print("\nWaiting for the next strategic cycle (7200s)...")
            time.sleep(7200) 
        except KeyboardInterrupt:
            print("\nEmpire hibernation initiated.")
            break
        except Exception as e:
            print(f"\n[Heartbeat Error] {e}")
            time.sleep(60) # エラー時は少し待ってリトライ

if __name__ == "__main__":
    main()
