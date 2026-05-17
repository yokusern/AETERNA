#!/usr/bin/env python3
"""
全未登録商品を Gumroad に一括登録 (published=True)
- ZIPなし商品は content.md から自動作成
- 重複タイトルはスキップ
- 壊れた価格・日本語タイトルはスキップ
"""
import os, json, time, zipfile, re, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN        = os.environ.get("GUMROAD_ACCESS_TOKEN")
API          = "https://api.gumroad.com/v2"
BASE         = Path(__file__).parent
PRODUCTS_DIR = BASE / "products"
REGISTRY_FILE = BASE / "data" / "products" / "registry.json"

SKIP_LOCAL_IDS = {
    "product_1778766236",  # deleted (Japanese)
    "product_1778766898",  # Japanese / $0
    "product_1778773900",  # deleted (duplicate)
    "test_integration_999",
}
# 英語のみ — 日本語が含まれるタイトルはスキップ
def _has_japanese(s: str) -> bool:
    return bool(re.search(r'[぀-ヿ一-鿿]', s))


def headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {}


def save_registry(reg: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(reg, ensure_ascii=False, indent=2))


def ensure_zip(product_dir: Path, spec: dict) -> Path | None:
    """ZIPがなければ content.md から作る。パスを返す。"""
    zips = sorted(product_dir.glob("*.zip"))
    if zips:
        return zips[0]
    content = product_dir / "content.md"
    if not content.exists():
        return None
    pid  = spec["product_id"]
    name = spec.get("name", pid)
    slug = re.sub(r'[^\w\-]', '_', name[:40]).lower()
    zpath = product_dir / f"{pid}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(content, f"{slug}.md")
    print(f"    ZIP作成: {zpath.name}")
    return zpath


def get_description(product_dir: Path) -> str:
    page = product_dir / "gumroad_page.md"
    if page.exists():
        return page.read_text(encoding="utf-8")
    content = product_dir / "content.md"
    if content.exists():
        return content.read_text(encoding="utf-8")[:2000]
    return ""


def create_on_gumroad(spec: dict, description: str) -> dict | None:
    """Gumroad に商品を作成して product dict を返す。"""
    price_usd = spec.get("price_usd", 0)
    price_jpy = spec.get("price_jpy", 0)
    # USD を cents に換算、JPY はそのまま
    if price_usd and 0 < price_usd <= 100:
        price = int(price_usd * 100)   # cents
    elif price_jpy and 0 < price_jpy <= 9999:
        price = int(price_jpy)
    else:
        return None  # 壊れた価格

    try:
        r = requests.post(
            f"{API}/products",
            headers=headers(),
            data={
                "name":        spec["name"],
                "price":       price,
                "description": description,
                "published":   "true",
            },
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                return data["product"]
        print(f"    API エラー {r.status_code}: {r.text[:200]}")
        return None
    except Exception as e:
        print(f"    リクエスト失敗: {e}")
        return None


def main():
    if not TOKEN:
        print("ERROR: GUMROAD_ACCESS_TOKEN が未設定")
        return

    registry = load_registry()
    registered_ids = set(registry.keys())
    registered_names = {v["name"].lower() for v in registry.values()}

    all_dirs = sorted(PRODUCTS_DIR.iterdir())
    candidates = []
    for d in all_dirs:
        sf = d / "spec.json"
        if not sf.exists():
            continue
        s = json.loads(sf.read_text())
        pid = s.get("product_id", "")

        if pid in registered_ids or pid in SKIP_LOCAL_IDS:
            continue
        if pid.startswith("bundle_") or pid.startswith("test_"):
            continue
        if _has_japanese(s.get("name", "")):
            continue
        price_usd = s.get("price_usd", 0)
        price_jpy = s.get("price_jpy", 0)
        if (price_usd == 0 and price_jpy == 0) or price_usd > 100 or price_jpy > 9999:
            continue
        # 重複タイトルスキップ
        name_lower = s.get("name", "").lower()
        if name_lower in registered_names:
            print(f"[SKIP 重複] {s.get('name')}")
            continue

        candidates.append((d, s))
        registered_names.add(name_lower)  # 同バッチ内の重複も防ぐ

    # 1日の上限 = 10件（Gumroad制限）
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="1回の最大登録数")
    args, _ = parser.parse_known_args()
    candidates = candidates[:args.limit]

    print(f"\n登録対象: {len(candidates)} 件 (limit={args.limit})\n")

    ok_count = 0
    for i, (d, spec) in enumerate(candidates, 1):
        name = spec.get("name", spec["product_id"])
        print(f"[{i}/{len(candidates)}] {name}")

        # ZIP 確保
        zip_path = ensure_zip(d, spec)
        description = get_description(d)

        # Gumroad 作成
        product = create_on_gumroad(spec, description)
        if not product:
            print(f"    [FAIL] スキップ")
            continue

        gumroad_id = product["id"]
        gumroad_url = product.get("short_url") or f"https://app.gumroad.com/products/{gumroad_id}"
        print(f"    [OK] {gumroad_url}")

        # registry 保存
        registry[spec["product_id"]] = {
            "gumroad_product_id": gumroad_id,
            "gumroad_url": gumroad_url,
            "name":  name,
            "price": spec.get("price_usd", spec.get("price_jpy", 0)),
            "published": True,
            "zip_path": str(zip_path) if zip_path else "",
            "registered_at": datetime.now().isoformat(),
            "pinterest_pinned": False,
        }
        save_registry(registry)
        registered_names.add(name.lower())
        ok_count += 1

        # Gumroadレート制限対策
        time.sleep(1.2)

    print(f"\n完了: {ok_count}/{len(candidates)} 件登録")


if __name__ == "__main__":
    main()
