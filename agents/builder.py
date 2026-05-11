"""
builder.py — 商品制作エージェント
brainからCREATE_PRODUCTが来たとき呼ばれる
Claude APIで商品コンテンツを生成し、products/に保存する
"""
import sys
import os
import json
import zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from core import llm_client, state_manager

JST = timezone(timedelta(hours=9))
PRODUCTS_DIR = ROOT / "products"

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

## 制作ガイドライン
{format_guide}

## 追加要件
- すぐに使える実用的な内容
- 具体例・手順・コードを豊富に含める
- 日本語で読みやすく
- コピー&ペーストで使えるテンプレートを含める

コンテンツをMarkdown形式で出力してください（説明文なし、コンテンツのみ）:"""

PAGE_PROMPT = """以下の商品のGumroad販売ページ説明文を作成してください。

商品名: {name}
ターゲット: {target}
内容の特徴: {highlight}
価格: ¥{price:,}

以下の形式で出力（JSON）:
{{
  "title": "Gumroadタイトル（70文字以内・キーワード含む）",
  "description": "説明文（Markdown、400字程度・ベネフィット重視）",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"]
}}"""


def _make_product_id(theme: str) -> str:
    import re
    ts = datetime.now(JST).strftime("%Y%m%d_%H%M")
    cleaned = re.sub(r"[^\w]", "_", theme)[:20]
    return f"{cleaned}_{ts}"


def create_product(spec: dict) -> str:
    """商品を制作してproducts/{product_id}/に保存する。返り値はディレクトリパス。"""
    theme = spec.get("theme", "デジタル商品")
    price = spec.get("price", 980)
    fmt = spec.get("format", "pdf").lower()
    target = spec.get("target", "ビジネスパーソン")
    differentiator = spec.get("differentiator", "実用的な内容")
    reason = spec.get("reason", "")

    product_id = _make_product_id(theme)
    product_dir = PRODUCTS_DIR / product_id
    (product_dir / "content").mkdir(parents=True, exist_ok=True)

    print(f"[Builder] 商品制作開始: {theme} (¥{price:,} / {fmt})")

    # 1. コンテンツ生成
    content_prompt = CONTENT_PROMPT.format(
        theme=theme, target=target, format=fmt,
        differentiator=differentiator,
        format_guide=FORMAT_GUIDE.get(fmt, FORMAT_GUIDE["pdf"]),
    )
    content = llm_client.call(content_prompt, max_tokens=4096)
    print(f"[Builder] コンテンツ生成完了 ({len(content)}文字)")

    # 2. ファイル保存
    main_file = product_dir / "content" / "main.md"
    main_file.write_text(content, encoding="utf-8")

    if fmt == "zip":
        _package_zip(product_dir, content, theme)

    # 3. 商品ページ説明文生成
    page_data = _generate_page(theme, target, content[:500], price)

    # 4. spec.json保存
    spec_data = {
        "product_id": product_id,
        "name": page_data.get("title", theme),
        "price_jpy": price,
        "currency": "JPY",
        "format": fmt,
        "tags": page_data.get("tags", []),
        "content_file": "content/main.md",
        "file_format": "PDF" if fmt == "pdf" else "ZIP",
        "status": "ready_to_upload",
        "created_at": datetime.now(JST).strftime("%Y-%m-%d"),
        "creation_reason": reason,
    }
    with open(product_dir / "spec.json", "w", encoding="utf-8") as f:
        json.dump(spec_data, f, ensure_ascii=False, indent=2)

    # 5. gumroad_page.md保存
    (product_dir / "gumroad_page.md").write_text(
        f"# {page_data.get('title', theme)}\n\n{page_data.get('description', '')}\n\n"
        f"**タグ**: {', '.join(page_data.get('tags', []))}",
        encoding="utf-8",
    )

    # 6. state.jsonに登録
    state_manager.register_product(product_id, published=False)
    print(f"[Builder] 完成: {product_dir}")
    return str(product_dir)


def _package_zip(product_dir: Path, content: str, theme: str) -> None:
    """コンテンツをZIPファイルにまとめる"""
    zip_path = product_dir / "content" / "package.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README.md", content)
    print(f"[Builder] ZIP生成: {zip_path}")


def _generate_page(theme: str, target: str, highlight: str, price: int) -> dict:
    try:
        prompt = PAGE_PROMPT.format(
            name=theme, target=target, highlight=highlight[:200], price=price
        )
        return llm_client.call_json(prompt, max_tokens=800)
    except Exception as e:
        print(f"[Builder] ページ生成エラー: {e}")
        return {"title": theme, "description": f"## {theme}\n\n実用的なデジタル商品です。", "tags": ["AI", "効率化"]}


def write_article(spec: dict) -> str:
    """集客記事を生成してdata/articles/に保存する"""
    theme = spec.get("theme", "AI活用法")
    platform = spec.get("platform", "note.com")

    prompt = f"""「{theme}」についての集客記事を書いてください。
掲載先: {platform}
目的: デジタル商品購入への自然な誘導
構成: タイトル・リード・本文（5章）・まとめ・商品案内
文字数: 2,000〜3,000字
読者: {spec.get('target', 'AIに興味があるビジネスパーソン')}

Markdown形式で出力:"""

    content = llm_client.call(prompt, max_tokens=3000)

    articles_dir = ROOT / "data" / "articles"
    articles_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(JST).strftime("%Y%m%d_%H%M")
    article_path = articles_dir / f"{ts}_{theme[:20]}.md"
    article_path.write_text(content, encoding="utf-8")

    print(f"[Builder] 記事保存: {article_path}")
    return str(article_path)
