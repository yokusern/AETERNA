#!/usr/bin/env python3
"""
Retroactive fix for published Gumroad products:
  1. Delete 3 garbage products (duplicate/corrupt/Japanese-only)
  2. Upload ZIP files to the 7 good products
  3. Update product descriptions from local gumroad_page.md

Run: ./venv/bin/python3 fix_uploads.py
"""
import os, json, sys, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TOKEN   = os.environ.get("GUMROAD_ACCESS_TOKEN")
API     = "https://api.gumroad.com/v2"
BASE    = Path(__file__).parent
PRODUCTS_DIR = BASE / "products"
REGISTRY_FILE = BASE / "data" / "products" / "registry.json"

# ── Products to DELETE from Gumroad (duplicate / corrupt price / Japanese title) ──
DELETE_LOCAL_IDS = {
    "product_1778773900",  # Quick Start Python (duplicate, $16)
    "product_1778767303",  # Master データ分析 ($3501 corrupt price)
    "product_1778766236",  # データ分析完全ガイド (Japanese title, $37)
}

# ── Products to KEEP: upload ZIP + update description ──
KEEP_LOCAL_IDS = [
    "chatgpt_biz_1778936029",
    "prompt_pack_content_001",
    "notion_life_os_001",
    "biz_finance_1778936014",
    "client_kit_1778936024",
    "product_1778767394",
    "product_1778767945",
]


def headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {}


def save_registry(reg: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(reg, ensure_ascii=False, indent=2))


def delete_product(gumroad_id: str, name: str):
    r = requests.delete(f"{API}/products/{gumroad_id}", headers=headers())
    if r.status_code == 200 and r.json().get("success"):
        print(f"  [DELETED] {name} ({gumroad_id})")
        return True
    else:
        print(f"  [FAIL] Delete {name}: {r.status_code} {r.text[:200]}")
        return False


def upload_zip(gumroad_id: str, zip_path: Path) -> bool:
    print(f"  Uploading {zip_path.name} …", end=" ", flush=True)
    with open(zip_path, "rb") as f:
        r = requests.post(
            f"{API}/products/{gumroad_id}/product_files",
            headers=headers(),
            files={"file": (zip_path.name, f)},
        )
    if r.status_code == 200:
        data = r.json()
        if data.get("success"):
            print("OK")
            return True
        else:
            print(f"FAIL (API) — {data}")
            return False
    else:
        print(f"FAIL ({r.status_code}) — {r.text[:300]}")
        return False


def update_description(gumroad_id: str, description: str, name: str) -> bool:
    r = requests.patch(
        f"{API}/products/{gumroad_id}",
        headers=headers(),
        data={"description": description},
    )
    if r.status_code == 200 and r.json().get("success"):
        print(f"  [DESC OK] {name}")
        return True
    else:
        print(f"  [DESC FAIL] {name}: {r.status_code} {r.text[:200]}")
        return False


def get_description(product_dir: Path) -> str:
    page = product_dir / "gumroad_page.md"
    if page.exists():
        return page.read_text(encoding="utf-8")
    content = product_dir / "content.md"
    if content.exists():
        return content.read_text(encoding="utf-8")[:2000]
    return ""


def find_zip(product_dir: Path) -> Path | None:
    zips = sorted(product_dir.glob("*.zip"))
    return zips[0] if zips else None


def main():
    if not TOKEN:
        print("ERROR: GUMROAD_ACCESS_TOKEN is not set. Check your .env file.")
        sys.exit(1)

    registry = load_registry()
    print(f"\nLoaded registry: {len(registry)} products\n")

    # ── STEP 1: Delete garbage products ────────────────────────────────────────
    print("=" * 60)
    print("STEP 1: Deleting garbage products")
    print("=" * 60)
    for local_id in DELETE_LOCAL_IDS:
        entry = registry.get(local_id)
        if not entry:
            print(f"  [SKIP] {local_id} — not in registry")
            continue
        gumroad_id = entry["gumroad_product_id"]
        name = entry["name"]
        print(f"\n  Deleting: {name} ({local_id})")
        ok = delete_product(gumroad_id, name)
        if ok:
            del registry[local_id]
            save_registry(registry)

    # ── STEP 2: Upload ZIPs + update descriptions ──────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Uploading files + updating descriptions")
    print("=" * 60)

    for local_id in KEEP_LOCAL_IDS:
        entry = registry.get(local_id)
        if not entry:
            print(f"\n  [SKIP] {local_id} — not in registry")
            continue

        gumroad_id = entry["gumroad_product_id"]
        name = entry["name"]
        product_dir = PRODUCTS_DIR / local_id

        print(f"\n  [{name}]")

        # Upload ZIP
        zip_path = find_zip(product_dir)
        if zip_path:
            upload_zip(gumroad_id, zip_path)
        else:
            print(f"  [WARN] No ZIP found in {product_dir}")

        # Update description
        description = get_description(product_dir)
        if description:
            update_description(gumroad_id, description, name)
        else:
            print(f"  [WARN] No description found for {name}")

    print("\n" + "=" * 60)
    print("Done. Check your Gumroad dashboard to verify.")
    print("=" * 60)


if __name__ == "__main__":
    main()
