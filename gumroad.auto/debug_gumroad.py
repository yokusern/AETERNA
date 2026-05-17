#!/usr/bin/env python3
"""
Gumroad API Debug Script
Verify product creation works correctly
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from gumroad_uploader import GumroadUploader
from dotenv import load_dotenv
import requests
import json

load_dotenv()


def main():
    print("=" * 70)
    print("  🔍 Gumroad API Debug")
    print("=" * 70)
    
    uploader = GumroadUploader()
    token = uploader.token
    
    # 1. 現在の商品一覧
    print("\n[1/3] Getting current products...")
    products = uploader.list_products()
    print(f"  Found {len(products)} products")
    
    # 2. テスト商品作成（正しいセント単位）
    print("\n[2/3] Creating test product...")
    price_cents = 1500  # $15
    
    product_data = {
        "name": "Debug Test - Quick Start Python",
        "price": price_cents,
        "description": "Debug test product. Quick start guide to Python.",
        "published": "false"
    }
    
    print(f"  Product: {product_data['name']}")
    print(f"  Price: {price_cents} cents (${price_cents/100})")
    
    resp = requests.post(
        "https://api.gumroad.com/v2/products",
        headers={"Authorization": f"Bearer {token}"},
        data=product_data
    )
    
    print(f"\n  Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success"):
            product = data["product"]
            print(f"\n  ✅ SUCCESS!")
            print(f"  Product ID: {product['id']}")
            print(f"  URL: https://app.gumroad.com/products/{product['id']}")
            print(f"  Published: {product['published']}")
            
            # 3. 確認
            print("\n[3/3] Verifying...")
            products_after = uploader.list_products()
            print(f"  Now have {len(products_after)} products")
            
            found = any(p["id"] == product["id"] for p in products_after)
            if found:
                print("  ✅ Product found in list!")
            else:
                print("  ❌ Product NOT found!")
        else:
            print(f"\n  ❌ API Error: {data}")
    else:
        print(f"\n  ❌ HTTP Error: {resp.status_code}")
        print(f"  Response: {resp.text}")


if __name__ == "__main__":
    main()
