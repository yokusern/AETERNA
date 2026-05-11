"""
product_builder_agent.py - 商品制作エージェント
企画書JSONを受け取り、Claude APIで実際のコンテンツを生成する
Claude API使用（ANTHROPIC_API_KEY必須）
"""
import os
import sys
import json
import zipfile
from datetime import datetime
from pathlib import Path

import anthropic

PRODUCTS_DIR = Path(__file__).parent.parent / "products"
PRODUCT_SPECS_DIR = Path(__file__).parent.parent / "product_specs"
DATA_DIR = Path(__file__).parent.parent / "data"


BUILD_PROMPT = """あなたはデジタル商品の制作専門家です。
以下の商品仕様に基づいて、実際に販売できる高品質なコンテンツを生成してください。

## 商品仕様
タイトル: {title}
形式: {format}
ターゲット: {target_audience}
差別化ポイント: {differentiator}

## 要件
- すぐに使える実用的な内容にする
- 具体的な例や手順を含める
- 日本語で、読みやすく・わかりやすく書く
- 購入して「良かった」と思ってもらえる品質

{format_instructions}

コンテンツを出力してください（マークダウン形式）："""

FORMAT_INSTRUCTIONS = {
    "PDF": """
コンテンツはMarkdown形式で以下の構成で書いてください：
- はじめに（目的・対象読者）
- メインコンテンツ（章立て・見出し付き）
- まとめ・活用方法
文字数: 3,000〜5,000字程度
""",
    "テンプレート": """
テンプレートの内容と使い方ガイドをMarkdown形式で書いてください：
- テンプレートの概要と使い方
- 各セクションの説明
- カスタマイズのポイント
- 実際のテンプレート本文（そのままコピーして使えるもの）
""",
    "スクリプト集": """
以下を含むMarkdown形式のドキュメントを書いてください：
- 概要と動作環境
- インストール方法（requirements.txt）
- 各スクリプトの使い方（コード例付き）
実際のPythonコードも含めてください（動作するもの）
""",
}


def load_latest_spec() -> dict:
    """最新の企画書から1件取得する"""
    spec_files = sorted(PRODUCT_SPECS_DIR.glob("*.json"), reverse=True)
    if not spec_files:
        raise FileNotFoundError("企画書が見つかりません。product_planner_agentを先に実行してください。")

    with open(spec_files[0], encoding="utf-8") as f:
        data = json.load(f)

    plans = data.get("plans", [])
    if not plans:
        raise ValueError("企画書に商品案がありません")

    # 未制作の最初の1件を返す
    built_ids = {d.name for d in PRODUCTS_DIR.iterdir() if d.is_dir()} if PRODUCTS_DIR.exists() else set()
    for plan in plans:
        product_id = _make_product_id(plan["title"])
        if product_id not in built_ids:
            return plan

    return plans[0]


def _make_product_id(title: str) -> str:
    """タイトルからIDを生成する"""
    import re
    cleaned = re.sub(r"[^\w぀-鿿]", "_", title)
    return cleaned[:30] + f"_{datetime.now().strftime('%Y%m%d')}"


def build_product(plan: dict) -> str:
    """Claude APIでコンテンツを生成し、商品ディレクトリに保存する"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY が設定されていません")

    client = anthropic.Anthropic(api_key=api_key)

    fmt = plan.get("format", "PDF")
    format_instr = FORMAT_INSTRUCTIONS.get(fmt, FORMAT_INSTRUCTIONS["PDF"])

    prompt = BUILD_PROMPT.format(
        title=plan["title"],
        format=fmt,
        target_audience=plan.get("target_audience", "ビジネスパーソン"),
        differentiator=plan.get("differentiator", ""),
        format_instructions=format_instr,
    )

    print(f"コンテンツ生成中: {plan['title']}...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    content = message.content[0].text

    # 商品ディレクトリを作成
    product_id = _make_product_id(plan["title"])
    product_dir = PRODUCTS_DIR / product_id
    (product_dir / "content").mkdir(parents=True, exist_ok=True)

    # コンテンツ保存
    content_file = product_dir / "content" / "main.md"
    content_file.write_text(content, encoding="utf-8")

    # spec.json保存
    spec = {
        "product_id": product_id,
        "name": plan["title"],
        "price_jpy": plan.get("price_jpy", 980),
        "currency": "JPY",
        "format": fmt,
        "tags": [],
        "content_file": "content/main.md",
        "file_format": "PDF" if fmt == "PDF" else "ZIP",
        "status": "ready_to_upload",
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "plan": plan,
    }
    with open(product_dir / "spec.json", "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    # 商品ページ説明文生成
    _generate_gumroad_page(client, plan, product_dir)

    print(f"商品制作完了: {product_dir}")
    return str(product_dir)


def _generate_gumroad_page(client: anthropic.Anthropic, plan: dict, product_dir: Path):
    """Gumroad商品ページの説明文を生成する"""
    prompt = f"""
Gumroadで販売するデジタル商品の商品ページ説明文を書いてください。

商品名: {plan['title']}
ターゲット: {plan.get('target_audience', '')}
差別化: {plan.get('differentiator', '')}
価格: ¥{plan.get('price_jpy', 980):,}

以下の形式でMarkdown出力してください：
1. 冒頭のキャッチフレーズ（1行・インパクト重視）
2. 説明文（特典・含まれる内容・こんな人に最適）
3. タグ（カンマ区切り5〜8個）
"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    page_content = message.content[0].text
    (product_dir / "gumroad_page.md").write_text(page_content, encoding="utf-8")


def run(spec_file: str = None):
    print("=== Product Builder Agent 起動 ===")

    if spec_file:
        with open(spec_file, encoding="utf-8") as f:
            plan = json.load(f)
    else:
        plan = load_latest_spec()

    print(f"制作対象: {plan['title']}")
    product_dir = build_product(plan)
    print(f"\n制作完了 → {product_dir}")
    return product_dir


if __name__ == "__main__":
    spec = sys.argv[1] if len(sys.argv) > 1 else None
    run(spec)
