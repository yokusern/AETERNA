"""
SalesTrackerAgent - 販売追跡エージェント
販売データの追跡と分析
"""

import os
import json
import random
from datetime import datetime, timedelta
from .base_agent import BaseAgent


class SalesTrackerAgent(BaseAgent):
    """販売追跡エージェント"""
    
    def __init__(self):
        super().__init__("SalesTrackerAgent")
        
        # 販売データファイル
        self.sales_data_file = os.path.join('agents', 'logs', 'sales_data.json')
        
        # 初期販売データ
        self.products = [
            {'id': 'prod_001', 'name': 'ITエンジニア転職完全ガイド', 'category': 'ebook', 'price': 2980},
            {'id': 'prod_002', 'name': 'AIプロンプトエンジニアリング', 'category': 'course', 'price': 4980},
            {'id': 'prod_003', 'name': 'Pythonテンプレートセット', 'category': 'template', 'price': 1980}
        ]
    
    def load_sales_data(self) -> dict:
        """販売データ読み込み"""
        try:
            if os.path.exists(self.sales_data_file):
                with open(self.sales_data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"販売データ読み込みエラー: {e}", "error")
        
        return {'sales': [], 'daily_totals': {}}
    
    def save_sales_data(self, sales_data: dict):
        """販売データ保存"""
        try:
            os.makedirs(os.path.dirname(self.sales_data_file), exist_ok=True)
            with open(self.sales_data_file, 'w', encoding='utf-8') as f:
                json.dump(sales_data, f, ensure_ascii=False, indent=2)
            self.log("販売データ保存完了")
        except Exception as e:
            self.log(f"販売データ保存エラー: {e}", "error")
    
    def generate_simulated_sales(self) -> list:
        """シミュレーション販売データ生成"""
        sales = []
        today = datetime.now()
        
        # 過去30日分のデータ
        for i in range(30):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # 1日あたりの販売数
            daily_sales = random.randint(0, 5)
            
            for _ in range(daily_sales):
                product = random.choice(self.products)
                sale = {
                    'id': f"sale_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
                    'product_id': product['id'],
                    'product_name': product['name'],
                    'price': product['price'],
                    'date': date_str,
                    'time': date.strftime('%H:%M:%S'),
                    'customer_email': f"customer_{random.randint(1000, 9999)}@example.com"
                }
                sales.append(sale)
        
        return sales
    
    def analyze_sales(self, sales_data: dict) -> dict:
        """販売分析"""
        sales = sales_data.get('sales', [])
        
        if not sales:
            return {
                'total_sales': 0,
                'total_revenue': 0,
                'best_selling': None,
                'daily_average': 0
            }
        
        # 総販売数
        total_sales = len(sales)
        
        # 総収益
        total_revenue = sum(sale['price'] for sale in sales)
        
        # 製品別売上
        product_sales = {}
        for sale in sales:
            pid = sale['product_id']
            if pid not in product_sales:
                product_sales[pid] = {'count': 0, 'revenue': 0, 'name': sale['product_name']}
            product_sales[pid]['count'] += 1
            product_sales[pid]['revenue'] += sale['price']
        
        # ベストセラー
        best_selling = None
        max_count = 0
        for pid, data in product_sales.items():
            if data['count'] > max_count:
                max_count = data['count']
                best_selling = data
        
        # 日別平均
        dates = set(sale['date'] for sale in sales)
        daily_average = total_sales / len(dates) if dates else 0
        
        return {
            'total_sales': total_sales,
            'total_revenue': total_revenue,
            'product_sales': product_sales,
            'best_selling': best_selling,
            'daily_average': daily_average,
            'active_days': len(dates)
        }
    
    def execute(self) -> bool:
        """エージェント実行"""
        self.log("[1/3] 販売データ読み込み中...")
        sales_data = self.load_sales_data()
        
        # データがなければシミュレーション
        if not sales_data.get('sales'):
            self.log("販売データがないため、シミュレーションデータを生成します")
            sales_data['sales'] = self.generate_simulated_sales()
        
        self.record_result('sales_count', len(sales_data['sales']))
        
        self.log("[2/3] 販売分析中...")
        analysis = self.analyze_sales(sales_data)
        
        self.record_result('total_sales', analysis['total_sales'])
        self.record_result('total_revenue', analysis['total_revenue'])
        self.record_result('best_selling', analysis['best_selling'])
        self.record_result('daily_average', analysis['daily_average'])
        
        self.log(f"総販売数: {analysis['total_sales']}件")
        self.log(f"総収益: ¥{analysis['total_revenue']:,}")
        if analysis['best_selling']:
            self.log(f"ベストセラー: {analysis['best_selling']['name']} ({analysis['best_selling']['count']}件)")
        
        self.log("[3/3] 販売データ保存中...")
        self.save_sales_data(sales_data)
        
        self.log("✅ 販売追跡完了")
        self.record_result('status', 'success')
        
        return True
