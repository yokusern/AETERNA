#!/usr/bin/env python3
"""
AETERNA Holdings - gumroad.auto 出版エージェント (Publisher)
憲法準拠: AETERNA_EMPIRE_CONSTITUTION.md

役割:
エンジニアエージェントが構築した資産をGumroad APIを通じて自動出版し、
販売用URLを取得する。
"""

import os
import json
import logging
import requests
from pathlib import Path

class PublisherAgent:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.reports_dir = self.base_dir / "system" / "reports"
        self.logs_dir = self.base_dir / "system" / "logs"
        self.setup_logging()
        
        # 憲法第4条に基づき、環境変数からAPIキーを取得
        self.gumroad_token = os.getenv('GUMROAD_ACCESS_TOKEN')

    def setup_logging(self):
        os.makedirs(self.logs_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.logs_dir / "publisher.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def publish_to_gumroad(self, product_path):
        """
        Gumroadに製品をアップロードして公開するロジック。
        APIトークンがない場合はシミュレーションモードで動作する。
        """
        spec_file = self.reports_dir / "latest_product_spec.json"
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)

        self.logger.info(f"Gumroadへの出版を開始します: {spec['product_name']}")

        if not self.gumroad_token:
            self.logger.warning("GUMROAD_ACCESS_TOKENが設定されていません。シミュレーションモードで続行します。")
            # 憲法第1条（社長の時間を奪わない）に基づき、テスト用のURLを生成
            mock_url = f"https://gumroad.com/l/aeterna-{spec['product_name'].lower()}"
            return mock_url

        # 実際のAPIリクエスト（APIリファレンスに基づく実装例）
        try:
            url = "https://api.gumroad.com/v2/products"
            payload = {
                "name": spec['product_name'],
                "price": spec['target_price'],
                "description": f"AETERNA Auto-Generated {spec['category']}. High performance guaranteed.",
                "access_token": self.gumroad_token
            }
            # 実際にはファイルのアップロードも必要
            response = requests.post(url, data=payload)
            if response.status_code == 201:
                product_url = response.json()['product']['short_url']
                self.logger.info(f"出版成功: {product_url}")
                return product_url
            else:
                self.logger.error(f"出版失敗: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"APIエラー: {str(e)}")
            return None

    def run(self, product_path):
        if product_path:
            return self.publish_to_gumroad(product_path)
        return None

if __name__ == "__main__":
    publisher = PublisherAgent()
    # テスト用のパス
    publisher.run(Path("/tmp/test_product"))
