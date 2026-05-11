"""
product_agent.py — 帝国の第1の心臓（制作・改善）
builder と improver の機能を完全に統合。
"""
import sys
import os
import json
import zipfile
import ast
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import llm_client, state_manager
from agents import analyzer

JST = timezone(timedelta(hours=9))
PRODUCTS_DIR = ROOT / "products"

# --- Builder Logic ---
FORMAT_GUIDE = {
    "pdf": "Markdown形式で、目次・章立て・具体例を含む実用的なガイド（3,000〜6,000字）",
    "zip": "Pythonスクリプト群（各スクリプトにREADMEと動作コード付き）",
    "notion": "Notionテンプレートのガイドと各テンプレートの詳細説明",
}

CONTENT_PROMPT = """あなたは高品質なデジタル商品を制作する専門家です。
以下の仕様で、購入者が「買って良かった」と思える商品コンテンツを作成してください。

## 商品仕様
- テーマ: {theme}
- ターゲット: {target}
- 形式: {format}
- 差別化: {differentiator}

## 市場コンテキスト（最新トレンド）
{market_context}

## 制作ガイドライン
{format_guide}

## 追加要件
- すぐに使える実用的な内容
- 具体例・手順・コードを豊富に含める
- 日本語で読みやすく
- コピー&ペーストで使えるテンプレートを含める

コンテンツをMarkdown形式で出力してください（説明文なし、コンテンツのみ）:"""

CRITIQUE_PROMPT = """あなたは厳しい品質管理責任者です。
生成された以下の商品コンテンツを批判的にレビューし、改善点を挙げてください。

## 商品テーマ
{theme}

## レビュー対象
{content}

## チェック項目
- 実用性は十分か？（具体的な手順やコードがあるか）
- 読者のベネフィットが明確か？
- 日本語として自然で、読みやすいか？
- 商品としての付加価値（希少性）があるか？

改善点を箇条書きで出力してください。"""

REFINEMENT_PROMPT = """以下の改善指示に基づき、元のコンテンツを大幅にブラッシュアップしてください。

## 改善指示
{critique}

## 元のコンテンツ
{content}

改善後の最終的なMarkdownコンテンツのみ出力してください:"""

def create_product(spec: dict) -> str:
    theme = spec.get("theme", "デジタル商品")
    price = spec.get("price", 980)
    fmt = spec.get("format", "pdf").lower()
    
    product_id = f"{theme[:10]}_{datetime.now(JST).strftime('%Y%m%d_%H%M')}"
    product_dir = PRODUCTS_DIR / product_id
    (product_dir / "content").mkdir(parents=True, exist_ok=True)

    market_context = analyzer.get_market_context(theme)
    
    # 2. コンテンツ生成 (初期草案)
    content_prompt = CONTENT_PROMPT.format(
        theme=theme, target=spec.get("target", "ビジネスパーソン"), 
        format=fmt, differentiator=spec.get("differentiator", "実用性"),
        format_guide=FORMAT_GUIDE.get(fmt, FORMAT_GUIDE["pdf"]),
        market_context=market_context
    )
    draft = llm_client.call(content_prompt, max_tokens=4000)
    print(f"[ProductAgent] 草案生成完了。セルフクリティーク開始...")

    # 3. セルフクリティーク (自己批判)
    critique = llm_client.call(CRITIQUE_PROMPT.format(theme=theme, content=draft[:2000]), max_tokens=1000)
    print(f"[ProductAgent] 改善点特定: {len(critique)}文字")

    # 4. ブラッシュアップ (自己修正)
    final_content = llm_client.call(REFINEMENT_PROMPT.format(critique=critique, content=draft), max_tokens=4000)
    print(f"[ProductAgent] 最終版完成 ({len(final_content)}文字)")

    (product_dir / "content" / "main.md").write_text(final_content, encoding="utf-8")
    
    # spec.json
    with open(product_dir / "spec.json", "w", encoding="utf-8") as f:
        json.dump({"product_id": product_id, "name": theme, "price_jpy": price, "status": "ready_to_upload"}, f)
    
    state_manager.register_product(product_id, published=False)
    return str(product_dir)

# --- Improver Logic ---
def improve_product(target: str, spec: dict) -> str:
    product_dir = PRODUCTS_DIR / target
    if not product_dir.exists(): return "Target not found"
    
    prompt = f"以下の商品を改善してください: {target}\n理由: {spec.get('reason')}"
    improved_content = llm_client.call(prompt)
    
    with open(product_dir / "content" / "main_improved.md", "w") as f:
        f.write(improved_content)
    
    return f"改善完了: {target}"

def run(params: dict) -> dict:
    action_type = params.get("type")
    if action_type == "CREATE":
        return {"status": "ok", "path": create_product(params.get("spec", params))}
    elif action_type == "IMPROVE":
        return {"status": "ok", "detail": improve_product(params.get("target"), params)}
    return {"status": "error"}
