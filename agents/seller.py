"""
seller.py — 販売管理エージェント
Gumroad API連携・商品登録・価格最適化・A/Bテストを担当
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gumroad.auto"))
from core import state_manager, llm_client

JST = timezone(timedelta(hours=9))
PRODUCTS_DIR = ROOT / "products"
REGISTRY_PATH = ROOT / "data" / "products_registry.json"


def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {}
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_registry(registry: dict) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def _get_uploader():
    from gumroad_uploader import GumroadUploader
    return GumroadUploader()


def upload_new_products(publish: bool = False) -> list[dict]:
    """未登録の ready_to_upload 商品をGumroadに登録する"""
    registry = _load_registry()
    registered_ids = set(registry.keys())
    uploaded = []

    for product_dir in PRODUCTS_DIR.iterdir():
        if not product_dir.is_dir():
            continue
        spec_path = product_dir / "spec.json"
        if not spec_path.exists():
            continue

        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)

        if spec.get("status") != "ready_to_upload":
            continue
        if spec["product_id"] in registered_ids:
            continue

        try:
            uploader = _get_uploader()
            product = uploader.upload_product_from_spec(str(spec_path), publish_after_upload=publish)
            registry[spec["product_id"]] = {
                "gumroad_product_id": product["id"],
                "name": product["name"],
                "price_jpy": spec.get("price_jpy", 0),
                "registered_at": datetime.now(JST).isoformat(),
                "published": publish,
            }
            _save_registry(registry)
            if publish:
                state_manager.register_product(spec["product_id"], published=True)
            print(f"[Seller] 登録完了: {product['name']}")
            uploaded.append({"product_id": spec["product_id"], "name": product["name"]})
        except Exception as e:
            print(f"[Seller] 登録失敗 ({product_dir.name}): {e}")

    return uploaded


def adjust_price(product_id: str, new_price: int) -> bool:
    """Gumroadの商品価格を変更する"""
    registry = _load_registry()
    entry = registry.get(product_id)
    if not entry:
        print(f"[Seller] 商品未登録: {product_id}")
        return False

    gumroad_id = entry.get("gumroad_product_id")
    if not gumroad_id:
        return False

    try:
        uploader = _get_uploader()
        uploader.update_product(gumroad_id, price=new_price)
        entry["price_jpy"] = new_price
        entry["price_updated_at"] = datetime.now(JST).isoformat()
        _save_registry(registry)
        print(f"[Seller] 価格変更: {product_id} → ¥{new_price:,}")
        return True
    except Exception as e:
        print(f"[Seller] 価格変更失敗: {e}")
        return False


def optimize_prices(state: dict) -> list[dict]:
    """売上データに基づいて価格を自動最適化する"""
    revenue = state.get("revenue", {})
    by_product = revenue.get("by_product", {})
    registry = _load_registry()
    changes = []

    for product_id, entry in registry.items():
        name = entry.get("name", product_id)
        stats = by_product.get(name, {})
        sales_count = stats.get("sales", 0)
        current_price = entry.get("price_jpy", 980)

        # 10件以上売れたら値上げ（上限¥4,980）
        if sales_count >= 10 and current_price < 4980:
            new_price = min(current_price + 300, 4980)
            if adjust_price(product_id, new_price):
                changes.append({"product_id": product_id, "old": current_price, "new": new_price, "reason": f"売上{sales_count}件で値上げ"})

        # 14日間0件なら値下げ（下限¥480）
        elif sales_count == 0 and current_price > 480:
            new_price = max(current_price - 200, 480)
            if adjust_price(product_id, new_price):
                changes.append({"product_id": product_id, "old": current_price, "new": new_price, "reason": "14日間売上ゼロで値下げ"})

    return changes


def run_ab_test(product_id: str) -> dict:
    """商品説明文のA/Bテストを実施する（2パターンを交互に設定）"""
    registry = _load_registry()
    entry = registry.get(product_id)
    if not entry:
        return {"error": "商品未登録"}

    gumroad_id = entry.get("gumroad_product_id")
    product_dir = PRODUCTS_DIR / product_id
    spec_path = product_dir / "spec.json"
    if not spec_path.exists():
        return {"error": "spec.jsonなし"}

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)

    # 現在のパターン番号を取得
    current_pattern = entry.get("ab_pattern", 0)
    next_pattern = 1 - current_pattern

    # LLMで別パターンの説明文を生成
    prompt = f"""以下の商品の説明文を、{'シンプル・数値重視' if next_pattern == 0 else 'ストーリー・感情訴求'}スタイルで書き直してください。
商品名: {spec.get('name', '')}
現在の説明文: （既存のものとは異なるアプローチで）
200〜300字で出力:"""

    try:
        new_description = llm_client.call(prompt, max_tokens=400, fast=True)
        uploader = _get_uploader()
        uploader.update_product(gumroad_id, description=new_description)
        entry["ab_pattern"] = next_pattern
        entry["ab_updated_at"] = datetime.now(JST).isoformat()
        _save_registry(registry)
        print(f"[Seller] A/Bテスト更新: {product_id} パターン{next_pattern}")
        return {"product_id": product_id, "pattern": next_pattern}
    except Exception as e:
        print(f"[Seller] A/Bテスト失敗: {e}")
        return {"error": str(e)}


def list_products() -> list[dict]:
    """登録済み商品一覧を返す"""
    try:
        uploader = _get_uploader()
        return uploader.list_products()
    except Exception as e:
        print(f"[Seller] 商品一覧取得失敗: {e}")
        return []
