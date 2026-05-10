#!/usr/bin/env python3
"""
AETERNA Holdings - gumroad.auto マスターオートパイロット
憲法準拠: AETERNA_EMPIRE_CONSTITUTION.md

機能:
1. 市場調査エージェントの実行
2. エンジニアエージェントによる製品構築
3. 出版エージェントによるGumroad公開
4. マーケティングエージェントによる拡散
5. 分析エージェントによる成果測定
"""

import os
import sys
import logging
from pathlib import Path
from market_researcher import MarketResearcher
from engineer import EngineerAgent
from publisher import PublisherAgent
from marketer import MarketerAgent
from sales_analyst import SalesAnalyst

class GumroadMasterAutopilot:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.logs_dir = self.base_dir / "system" / "logs"
        self.setup_logging()
        
        # 全エージェントの初期化
        self.researcher = MarketResearcher()
        self.engineer = EngineerAgent()
        self.publisher = PublisherAgent()
        self.marketer = MarketerAgent()
        self.analyst = SalesAnalyst()

    def setup_logging(self):
        os.makedirs(self.logs_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [MASTER] - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / "master_autopilot.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_cycle(self):
        self.logger.info("=== AETERNA Gumroad エンドツーエンド収益化サイクル開始 ===")
        
        # 1. 調査
        self.logger.info("Step 1: 市場調査フェーズ")
        spec = self.researcher.run()
        
        # 2. 構築
        self.logger.info("Step 2: 製品構築フェーズ")
        product_path = self.engineer.run()
        
        # 3. 出版
        self.logger.info("Step 3: Gumroad出版フェーズ")
        product_url = self.publisher.run(product_path)
        
        # 4. 集客
        self.logger.info("Step 4: 集客・マーケティングフェーズ")
        self.marketer.run(product_url)
        
        # 5. 分析
        self.logger.info("Step 5: 販売分析フェーズ")
        analysis = self.analyst.run()
        
        self.logger.info("=== AETERNA Gumroad 全自動収益化プロセス完了 ===")
        self.logger.info(f"最終成果物URL: {product_url}")

if __name__ == "__main__":
    autopilot = GumroadMasterAutopilot()
    autopilot.run_cycle()
