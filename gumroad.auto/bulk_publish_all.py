#!/usr/bin/env python3
"""
bulk_publish_all.py
===================
Gumroadの全非公開商品を一括公開する。
アカウントの支払い設定が完了した後に1回だけ実行する。

使い方:
  python bulk_publish_all.py

前提条件:
  - Gumroad アカウントで支払い設定 (Settings > Payouts) が完了していること
  - .env または環境変数に GUMROAD_ACCESS_TOKEN が設定されていること
"""
import os, time, requests, urllib.parse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN")
API = "https://api.gumroad.com/v2"


def h():
    return {"Authorization": f"Bearer {TOKEN}"}


def get_all_products() -> list:
    """全商品を取得（最大100件）"""
    all_products = []
    for page in range(1, 20):
        r = requests.get(f"{API}/products", headers=h(), params={"page": page}, timeout=15)
        products = r.json().get("products", [])
        if not products:
            break
        all_products.extend(products)
        if len(products) < 10:
            break
    return all_products


def publish_one(product_id: str) -> bool:
    enc = urllib.parse.quote(product_id, safe="")
    r = requests.patch(f"{API}/products/{enc}", headers=h(), data={"published": "true"}, timeout=15)
    if r.status_code == 200 and r.json().get("success"):
        return True
    return False


def main():
    print("=== Gumroad 全商品一括公開 ===\n")

    products = get_all_products()
    non_pub = [p for p in products if not p.get("published")]
    print(f"全商品: {len(products)}件  非公開: {len(non_pub)}件\n")

    if not non_pub:
        print("全商品が既に公開済みです。")
        return

    ok = 0
    for i, p in enumerate(non_pub, 1):
        pid = p["id"]
        name = p.get("name", "?")[:45]
        result = publish_one(pid)
        icon = "✅" if result else "⚫"
        print(f"[{i}/{len(non_pub)}] {icon} {name}")
        if result:
            ok += 1
        time.sleep(0.8)

    print(f"\n公開完了: {ok}/{len(non_pub)} 件")
    print("\n※ published=Falseのまま表示される場合でも、実際には公開されていることがあります。")
    print("  gumroad.com のダッシュボードで確認してください。")


if __name__ == "__main__":
    main()
