#!/usr/bin/env python3
"""
Gumroad 商品クリーンアップツール
- ファイルなし/価格不正の商品を一覧表示して削除できる
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN")
API = "https://api.gumroad.com/v2"


def headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def list_products():
    r = requests.get(f"{API}/products", headers=headers())
    r.raise_for_status()
    return r.json().get("products", [])


def delete_product(product_id: str):
    r = requests.delete(f"{API}/products/{product_id}", headers=headers())
    r.raise_for_status()
    return r.json()


def main():
    if not TOKEN:
        print("ERROR: GUMROAD_ACCESS_TOKEN が未設定")
        sys.exit(1)

    products = list_products()
    if not products:
        print("Gumroadに商品がありません")
        return

    print(f"\n=== Gumroad 商品一覧 ({len(products)}件) ===\n")

    flagged = []
    for i, p in enumerate(products):
        has_files = len(p.get("product_files", [])) > 0
        published = p.get("published", False)
        price = p.get("price", 0)
        sales = p.get("sales_count", 0)

        issues = []
        if not has_files:
            issues.append("ファイルなし")
        if price < 100:
            issues.append(f"価格が低すぎる(¥{price})")

        status = "公開中" if published else "下書き"
        issue_str = f"  ⚠ {', '.join(issues)}" if issues else ""
        print(f"[{i+1}] [{status}] {p['name'][:50]}")
        print(f"     ID: {p['id']} | ¥{price} | 売上: {sales}件 | ファイル: {'あり' if has_files else 'なし'}{issue_str}")

        if issues:
            flagged.append(p)

    if not flagged:
        print("\n問題のある商品はありません")
        return

    print(f"\n⚠  問題のある商品: {len(flagged)}件")
    print("="*50)

    # 削除対象を選択
    print("\n削除する商品を選んでください（複数可）")
    print("例: 1 3 5  または  all  または  Enter でスキップ")

    for i, p in enumerate(flagged):
        published = "公開中" if p.get("published") else "下書き"
        print(f"  [{i+1}] [{published}] {p['name'][:50]} (¥{p.get('price',0)})")

    choice = input("\n番号を入力 (Enter=スキップ): ").strip()

    if not choice:
        print("何も削除しませんでした")
        return

    to_delete = []
    if choice.lower() == "all":
        to_delete = flagged
    else:
        for token in choice.split():
            try:
                idx = int(token) - 1
                if 0 <= idx < len(flagged):
                    to_delete.append(flagged[idx])
            except ValueError:
                pass

    if not to_delete:
        print("有効な番号がありませんでした")
        return

    print(f"\n以下の {len(to_delete)}件 を削除します:")
    for p in to_delete:
        print(f"  - {p['name']}")

    confirm = input("本当に削除しますか? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("キャンセルしました")
        return

    for p in to_delete:
        try:
            delete_product(p["id"])
            print(f"  ✓ 削除: {p['name']}")
        except Exception as e:
            print(f"  ✗ 削除失敗: {p['name']} — {e}")

    print("\n完了")


if __name__ == "__main__":
    main()
