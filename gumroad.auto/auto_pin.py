#!/usr/bin/env python3
"""
auto_pin.py — Gumroadに公開済みの商品をPinterestに自動投稿

GitHub Actionsから毎日 batch_publish.py の後に実行される。
registry.json を読み、pinterest_pinned=False の商品をピン投稿して
pinterest_pinned=True に更新する。
"""

import json
import time
from pathlib import Path
from dotenv import load_dotenv
from pinterest_client import PinterestClient

load_dotenv()

BASE_DIR      = Path(__file__).parent
REGISTRY_FILE = BASE_DIR / "data" / "products" / "registry.json"
PRODUCTS_DIR  = BASE_DIR / "products"

# GitHub raw URL（コミット後に有効になる）
GITHUB_RAW = "https://raw.githubusercontent.com/yokusern/AETERNA/main/gumroad.auto/products"


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {}
    return json.loads(REGISTRY_FILE.read_text())


def save_registry(reg: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(reg, ensure_ascii=False, indent=2))


def get_cover_image(product_id: str) -> str | None:
    """GitHub raw URL でカバー画像を返す（Actions実行時はコミット済みなので有効）"""
    for ext in ("png", "jpg", "jpeg", "webp"):
        path = PRODUCTS_DIR / product_id / f"cover.{ext}"
        if path.exists():
            return f"{GITHUB_RAW}/{product_id}/cover.{ext}"
    return None


def build_pin_content(entry: dict) -> dict:
    name  = entry.get("name", "Digital Product")
    price = entry.get("price", 0)
    price_str = f"${price:.0f}" if isinstance(price, (int, float)) else str(price)

    title = f"{name[:90]} — Only {price_str}"

    description = (
        f"✅ {name}\n\n"
        f"💡 A digital resource to help you level up your skills.\n"
        f"📥 Instant download — {price_str} on Gumroad\n\n"
        f"#digitalproduct #gumroad #sidehustle #aitools #passiveincome"
    )

    return {"title": title[:100], "description": description[:800]}


def main():
    client = PinterestClient()

    if not client.is_configured():
        print("[auto_pin] Pinterest未設定 — PINTEREST_ACCESS_TOKEN と PINTEREST_BOARD_ID を確認")
        return

    registry = load_registry()
    targets = [
        (pid, entry)
        for pid, entry in registry.items()
        if entry.get("published") and not entry.get("pinterest_pinned")
        and entry.get("gumroad_url")
    ]

    if not targets:
        print("[auto_pin] ピン投稿するものなし（全件投稿済みか、未公開）")
        return

    print(f"[auto_pin] {len(targets)} 件をPinterestに投稿します")

    pinned = 0
    for pid, entry in targets:
        content = build_pin_content(entry)
        image_url = get_cover_image(pid)
        if not image_url:
            print(f"  ⚠ {entry['name'][:40]} — カバー画像なし、スキップ")
            continue

        try:
            pin = client.create_pin(
                title=content["title"],
                description=content["description"],
                link=entry["gumroad_url"],
                image_url=image_url,
            )
            registry[pid]["pinterest_pinned"] = True
            registry[pid]["pinterest_pin_id"] = pin["id"]
            save_registry(registry)
            pinned += 1
            print(f"  ✓ {entry['name']} → pin/{pin['id']}")
            time.sleep(2)  # Pinterest レート制限対策
        except Exception as e:
            print(f"  ✗ {entry['name']} — {e}")

    print(f"\n[auto_pin] 完了: {pinned}/{len(targets)} 件")


if __name__ == "__main__":
    main()
