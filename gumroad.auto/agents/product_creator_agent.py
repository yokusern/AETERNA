"""
ProductCreatorAgent - デジタル製品自動生成エージェント
AIを使用して高品質なデジタル製品を自動生成
"""

import os
import json
import random
from datetime import datetime
from .base_agent import BaseAgent


class ProductCreatorAgent(BaseAgent):
    """デジタル製品自動生成エージェント"""
    
    def __init__(self):
        super().__init__("ProductCreatorAgent")
        
        # 製品カテゴリ
        self.product_categories = [
            'ebook',
            'course',
            'template',
            'toolkit'
        ]
        
        # 製品トピック
        self.product_topics = [
            'ITエンジニア転職',
            'AIプロンプトエンジニアリング',
            'Pythonプログラミング',
            'Web開発',
            'クラウドインフラ',
            'セキュリティ',
            'データ分析',
            'フリーランス'
        ]
        
        # 価格設定
        self.price_ranges = {
            'ebook': (1980, 4980),
            'course': (4980, 9980),
            'template': (980, 2980),
            'toolkit': (2980, 6980)
        }
    
    def generate_product_idea(self) -> dict:
        """製品アイデア生成"""
        category = random.choice(self.product_categories)
        topic = random.choice(self.product_topics)
        min_price, max_price = self.price_ranges[category]
        price = random.randint(min_price, max_price)
        
        product = {
            'title': f"{topic}完全ガイド",
            'description': f"{topic}の専門知識を体系的に学べるコンテンツです。",
            'price': price,
            'category': category,
            'topic': topic,
            'tags': [topic, category, 'ITエンジニア', 'スキルアップ'],
            'created_at': datetime.now().isoformat()
        }
        
        self.log(f"製品アイデア生成: {product['title']} (¥{product['price']})")
        return product
    
    def generate_product_content(self, product: dict) -> str:
        """製品コンテンツ生成"""
        topic = product['topic']
        category = product['category']
        
        content = f"# {product['title']}\n\n"
        content += f"## はじめに\n\n"
        content += f"本{self._get_category_name(category)}では、{topic}について体系的に学ぶことができます。\n\n"
        
        content += f"## 目次\n\n"
        content += f"1. 基礎知識\n"
        content += f"2. 実践的なスキル\n"
        content += f"3. 応用テクニック\n"
        content += f"4. まとめ\n\n"
        
        content += f"## 基礎知識\n\n"
        content += f"{topic}の基本概念と重要なポイントを解説します。\n\n"
        
        content += f"## 実践的なスキル\n\n"
        content += f"実際の業務で活用できるスキルを習得します。\n\n"
        
        content += f"## 応用テクニック\n\n"
        content += f"更にスキルアップするためのテクニックを紹介します。\n\n"
        
        content += f"## まとめ\n\n"
        content += f"本{self._get_category_name(category)}で学んだことを実践し、スキルアップを目指しましょう。\n\n"
        content += f"---\n\n"
        content += f"**著者**: AETERNA Holdings\n"
        content += f"**作成日**: {datetime.now().strftime('%Y年%m月%d日')}\n"
        
        return content
    
    def _get_category_name(self, category: str) -> str:
        """カテゴリ名取得"""
        names = {
            'ebook': '電子書籍',
            'course': 'コース',
            'template': 'テンプレート',
            'toolkit': 'ツールキット'
        }
        return names.get(category, '製品')
    
    def save_product(self, product: dict, content: str) -> bool:
        """製品保存"""
        try:
            # ディレクトリ作成
            products_dir = os.path.join('production_assets', product['category'])
            os.makedirs(products_dir, exist_ok=True)
            
            # ファイル名
            safe_title = product['title'].replace(' ', '_').replace('/', '_')
            file_path = os.path.join(products_dir, f"{safe_title}.md")
            
            # ファイル保存
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.log(f"製品保存完了: {file_path}")
            self.record_result('product_saved', True)
            self.record_result('product_path', file_path)
            return True
            
        except Exception as e:
            self.log(f"製品保存エラー: {e}", "error")
            self.record_result('product_saved', False)
            return False
    
    def execute(self) -> bool:
        """エージェント実行"""
        self.log("[1/3] 製品アイデア生成中...")
        product = self.generate_product_idea()
        self.record_result('product', product)
        
        self.log("[2/3] 製品コンテンツ生成中...")
        content = self.generate_product_content(product)
        self.record_result('content_length', len(content))
        
        self.log("[3/3] 製品保存中...")
        success = self.save_product(product, content)
        
        if success:
            self.log("✅ 製品生成完了")
            self.record_result('status', 'success')
        else:
            self.log("❌ 製品生成失敗", "error")
            self.record_result('status', 'failure')
        
        return success
