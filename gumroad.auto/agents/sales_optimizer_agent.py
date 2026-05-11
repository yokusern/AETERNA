"""
sales_optimizer_agent.py - 販売・価格最適化エージェント
完成品をGumroadに登録し、売上データに基づいて価格・説明文を最適化する
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from gumroad_uploader import GumroadUploader

PRODUCTS_DIR = Path(__file__).parent.parent / "products"
DATA_DIR = Path(__file__).parent.parent / "data"


def find_unregistered_products() -> list:
    """未登録の完成品を探す"""
    registry_path = DATA_DIR / "products" / "registry.json"
    registered_ids = set()
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            registered_ids = set(json.load(f).keys())

    unregistered = []
    for product_dir in PRODUCTS_DIR.iterdir():
        if not product_dir.is_dir():
            continue
        spec_file = product_dir / "spec.json"
        if not spec_file.exists():
            continue
        with open(spec_file, encoding="utf-8") as f:
            spec = json.load(f)
        if spec.get("status") == "ready_to_upload" and spec["product_id"] not in registered_ids:
            unregistered.append(str(spec_file))

    return unregistered


def optimize_prices(uploader: GumroadUploader, analysis: dict):
    """売上データに基づいて価格を最適化する"""
    if not analysis or analysis.get("total_sales", 0) < 10:
        print("価格最適化: データ不足のためスキップ（10件以上の売上が必要）")
        return

    registry_path = DATA_DIR / "products" / "registry.json"
    if not registry_path.exists():
        return

    with open(registry_path, encoding="utf-8") as f:
        registry = json.load(f)

    product_stats = analysis.get("products", {})

    for product_id, info in registry.items():
        gumroad_id = info.get("gumroad_product_id")
        name = info.get("name", "")
        if not gumroad_id:
            continue

        stats = product_stats.get(name, {})
        sales_count = stats.get("count", 0)
        current_price = info.get("price_jpy", 980)

        # 10件以上売れている商品は値上げ（最大2倍まで）
        if sales_count >= 10 and current_price < 4980:
            new_price = min(current_price + 200, 4980)
            uploader.update_product(gumroad_id, price=new_price)
            info["price_jpy"] = new_price
            print(f"価格調整: {name} ¥{current_price} → ¥{new_price}")

        # 7日間で0件の商品は値下げ（最低¥480）
        elif sales_count == 0 and current_price > 480:
            new_price = max(current_price - 200, 480)
            uploader.update_product(gumroad_id, price=new_price)
            info["price_jpy"] = new_price
            print(f"値下げ: {name} ¥{current_price} → ¥{new_price}")

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def run(publish: bool = False):
    print("=== Sales Optimizer Agent 起動 ===")

    uploader = GumroadUploader()

    # 未登録商品のアップロード
    unregistered = find_unregistered_products()
    if unregistered:
        print(f"未登録商品: {len(unregistered)}件")
        for spec_file in unregistered:
            try:
                product = uploader.upload_product_from_spec(spec_file, publish_after_upload=publish)
                print(f"登録完了: {product['name']}")
            except Exception as e:
                print(f"登録エラー ({spec_file}): {e}")
    else:
        print("未登録商品なし")

    # 価格最適化
    analysis_path = DATA_DIR / "latest_analysis.json"
    if analysis_path.exists():
        with open(analysis_path, encoding="utf-8") as f:
            analysis = json.load(f)
        optimize_prices(uploader, analysis)

    # 登録商品一覧を表示
    products = uploader.list_products()
    print(f"\n=== 登録済み商品 ({len(products)}件) ===")
    for p in products:
        status = "公開中" if p.get("published") else "非公開"
        print(f"  [{status}] {p['name']} ¥{p.get('price', 0):,}")

    return products


if __name__ == "__main__":
    publish_flag = "--publish" in sys.argv
    run(publish=publish_flag)
