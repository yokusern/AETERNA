"""
MasterAgent - gumroad.auto マスターエージェント
全エージェントの統括と実行
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any
from .base_agent import BaseAgent
from .product_creator_agent import ProductCreatorAgent
from .sales_tracker_agent import SalesTrackerAgent
from .marketing_agent import MarketingAgent


class MasterAgent(BaseAgent):
    """gumroad.auto マスターエージェント"""
    
    def __init__(self):
        super().__init__("MasterAgent")
        
        # エージェントリスト
        self.agents = [
            ProductCreatorAgent(),
            SalesTrackerAgent(),
            MarketingAgent()
        ]
        
        # 状態ファイル
        self.state_file = os.path.join('agents', 'logs', 'master_state.json')
        
        # サイクルカウンター
        self.cycle = self._load_cycle()
    
    def _load_cycle(self) -> int:
        """サイクル読み込み"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    return state.get('cycle', 0)
        except Exception as e:
            self.log(f"状態読み込みエラー: {e}", "error")
        return 0
    
    def _save_cycle(self):
        """サイクル保存"""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({'cycle': self.cycle, 'last_run': datetime.now().isoformat()}, f)
        except Exception as e:
            self.log(f"状態保存エラー: {e}", "error")
    
    def run_all_agents(self) -> Dict[str, Any]:
        """全エージェント実行"""
        results = {}
        success_count = 0
        
        for agent in self.agents:
            self.log("─" * 60)
            self.log(f"▶ {agent.name} 起動")
            self.log("─" * 60)
            
            result = agent.run()
            results[agent.name] = result
            
            if result['status'] == 'success':
                success_count += 1
                self.log(f"✓ {agent.name} 完了")
            else:
                self.log(f"✗ {agent.name} 失敗", "error")
        
        return {
            'cycle': self.cycle,
            'timestamp': datetime.now().isoformat(),
            'agents': results,
            'success_count': success_count,
            'total_count': len(self.agents)
        }
    
    def save_cycle_report(self, results: Dict[str, Any]):
        """サイクルレポート保存"""
        try:
            log_dir = os.path.join('agents', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            report_file = os.path.join(
                log_dir,
                f"cycle_{self.cycle:04d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            self.log(f"サイクルレポート保存: {report_file}")
            
        except Exception as e:
            self.log(f"レポート保存エラー: {e}", "error")
    
    def execute(self) -> bool:
        """エージェント実行"""
        self.cycle += 1
        self.log("=" * 60)
        self.log(f"  gumroad.auto サイクル #{self.cycle} 開始")
        self.log("=" * 60)
        
        # 全エージェント実行
        results = self.run_all_agents()
        
        # レポート保存
        self.save_cycle_report(results)
        
        # サイクル保存
        self._save_cycle()
        
        # 結果表示
        self.log("=" * 60)
        self.log(f"  サイクル #{self.cycle} 完了")
        self.log(f"  成功: {results['success_count']}/{results['total_count']} エージェント")
        self.log("  次回実行: 手動またはcron/launchdで設定")
        self.log("=" * 60)
        
        self.record_result('cycle', self.cycle)
        self.record_result('success_count', results['success_count'])
        self.record_result('total_count', results['total_count'])
        self.record_result('all_results', results)
        
        return results['success_count'] == results['total_count']


def main():
    """メイン実行"""
    master = MasterAgent()
    result = master.run()
    return result


if __name__ == "__main__":
    main()
