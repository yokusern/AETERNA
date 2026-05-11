"""
analyzer.py — 帝国の知性（市場分析・文脈把握）
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import llm_client

def get_market_context(theme: str) -> str:
    """指定されたテーマに関する最新の市場トレンドと、売れるための文脈を取得する"""
    prompt = f"""あなたは鋭い市場分析家です。テーマ「{theme}」について、今この瞬間に売れるための市場文脈を分析してください。
以下の観点を含めてください：
- 現在のトレンド（何が求められているか）
- 競合との差別化ポイント
- ターゲットが抱えている深い悩み
- 「今」買うべき理由

分析結果を200文字程度の要約として出力してください。"""
    
    try:
        context = llm_client.call(prompt, max_tokens=500)
        return context
    except Exception as e:
        return f"市場分析エラー: {e}。一般的な高品質コンテンツを目指してください。"

if __name__ == "__main__":
    print(get_market_context("ChatGPTプロンプト"))
