"""
product_planner_agent.py - 商品企画エージェント
売上データとトレンドを基に、次に作るべき商品を提案する
Claude API使用（ANTHROPIC_API_KEY必須）
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

import anthropic

DATA_DIR = Path(__file__).parent.parent / "data"
PRODUCT_SPECS_DIR = Path(__file__).parent.parent / "product_specs"


PLANNING_PROMPT = """あなたはGumroadでデジタル商品を販売する専門家です。

以下の売上データと市場情報を基に、次に制作すべきデジタル商品を3つ提案してください。

## 現在の売上データ
{analysis_summary}

## 市場トレンド（2026年）
- AI活用ツール・プロンプト集の需要が急拡大
- Notionテンプレート市場は継続成長
- Python自動化・業務効率化コンテンツへの関心高
- ChatGPT・Claude活用法コンテンツの人気
- フリーランス向けビジネステンプレートの需要

## 現在の商品ラインナップ
{existing_products}

## 提案要件
- 制作日数: 1〜3日以内で作れるもの
- 価格帯: ¥980〜¥4,980
- 形式: PDF、テンプレート、スクリプト集のいずれか
- 既存商品と重複しないこと

以下のJSON形式で回答してください（説明文は不要、JSONのみ）：
```json
[
  {{
    "title": "商品タイトル",
    "price_jpy": 数値,
    "format": "PDF/テンプレート/スクリプト集",
    "target_audience": "ターゲット（1行）",
    "differentiator": "差別化ポイント（1行）",
    "estimated_days": 制作日数（数値）,
    "rationale": "提案理由（1〜2文）"
  }}
]
```"""


def load_analysis() -> dict:
    """最新の分析データを読み込む"""
    analysis_path = DATA_DIR / "latest_analysis.json"
    if not analysis_path.exists():
        return {"total_revenue": 0, "total_sales": 0, "products": {}, "recommendations": []}
    with open(analysis_path, encoding="utf-8") as f:
        return json.load(f)


def load_existing_products() -> list:
    """登録済み商品一覧を読み込む"""
    registry_path = DATA_DIR / "products" / "registry.json"
    if not registry_path.exists():
        return ["ChatGPTプロンプト集", "Notion業務テンプレートセット", "Python自動化スクリプト5選"]
    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)
    return [v["name"] for v in registry.values()]


def plan_products(analysis: dict, existing_products: list) -> list:
    """Claude APIを使って次の商品を企画する"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY が設定されていません。\n"
            "export ANTHROPIC_API_KEY=your_key"
        )

    client = anthropic.Anthropic(api_key=api_key)

    analysis_summary = (
        f"総売上: ¥{analysis['total_revenue']:,}\n"
        f"総販売数: {analysis['total_sales']}件\n"
        f"人気商品: {', '.join(list(analysis.get('products', {}).keys())[:3]) or 'なし'}\n"
        f"改善提案: {'; '.join(analysis.get('recommendations', [])[:2])}"
    )

    prompt = PLANNING_PROMPT.format(
        analysis_summary=analysis_summary,
        existing_products="\n".join(f"- {p}" for p in existing_products)
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    # JSONブロックを抽出
    if "```json" in response_text:
        json_str = response_text.split("```json")[1].split("```")[0].strip()
    elif "[" in response_text:
        start = response_text.index("[")
        end = response_text.rindex("]") + 1
        json_str = response_text[start:end]
    else:
        json_str = response_text

    return json.loads(json_str)


def save_specs(plans: list) -> list:
    """企画書をJSONファイルとして保存する"""
    PRODUCT_SPECS_DIR.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    spec_file = PRODUCT_SPECS_DIR / f"{date_str}.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "plans": plans
    }

    with open(spec_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"企画書保存: {spec_file}")
    return plans


def run():
    print("=== Product Planner Agent 起動 ===")

    analysis = load_analysis()
    existing_products = load_existing_products()

    print("Claude APIで商品企画を生成中...")
    plans = plan_products(analysis, existing_products)
    save_specs(plans)

    print(f"\n=== 商品企画（{len(plans)}件）===")
    for i, plan in enumerate(plans, 1):
        print(f"\n{i}. {plan['title']}")
        print(f"   価格: ¥{plan['price_jpy']:,} | 形式: {plan['format']} | 制作: {plan.get('estimated_days', '?')}日")
        print(f"   理由: {plan.get('rationale', '')}")

    return plans


if __name__ == "__main__":
    run()
