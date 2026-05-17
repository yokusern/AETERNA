#!/usr/bin/env python3
"""
Pin products to Pinterest - Manual script for pinning approved products
"""

import os
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pinterest_client import PinterestClient

load_dotenv()

BASE_DIR = Path(__file__).parent
PRODUCTS_DIR = BASE_DIR / "products"


def get_approved_products():
    """Get list of approved products from LocalStorage (if available) or prompt user"""
    print("📋 Getting products...")
    products = []
    
    if not PRODUCTS_DIR.exists():
        print("⚠️ No products directory found")
        return products
    
    product_dirs = sorted(
        [d for d in PRODUCTS_DIR.iterdir() if d.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    for dir_path in product_dirs:
        spec_file = dir_path / "spec.json"
        if spec_file.exists():
            with open(spec_file, 'r', encoding='utf-8') as f:
                spec = json.load(f)
            products.append({
                "dir": dir_path,
                "spec": spec
            })
    
    return products


def generate_pin_content(product_spec):
    """Generate Pinterest pin content from product spec"""
    price = product_spec.get('price_usd', product_spec.get('price', 15))
    name = product_spec['name']
    subcategory = product_spec['subcategory']
    product_type = product_spec['product_type']
    
    titles = [
        f"{name}: Your Ultimate Guide",
        f"Get {name} Now",
        f"Master {subcategory} with {name}",
        f"{name} - Everything You Need",
        f"Transform Your {subcategory} Skills"
    ]
    
    descriptions = [
        f"Discover the ultimate guide to {subcategory}. This {product_type} is perfect for beginners and intermediate learners. Get yours today for ${price}!",
        f"Ready to master {subcategory}? This comprehensive {product_type} has everything you need. Download now and start learning!",
        f"Looking for the best {subcategory} resource? Look no further! This {product_type} is packed with value. Get it for ${price}!"
    ]
    
    return {
        "title": titles[0],
        "description": descriptions[0]
    }


def main():
    parser = argparse.ArgumentParser(description='Pin products to Pinterest')
    parser.add_argument('--product', type=str, help='Product ID to pin (optional)')
    parser.add_argument('--image', type=str, help='Image URL for pin (optional)')
    parser.add_argument('--link', type=str, help='Gumroad product link (optional)')
    
    args = parser.parse_args()
    
    client = PinterestClient()
    
    if not client.is_configured():
        print("❌ Pinterest API not configured!")
        print("\n📝 Setup Instructions:")
        print("1. Copy .env.example to .env")
        print("2. Fill in PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID")
        print("3. Get your credentials from https://developers.pinterest.com/")
        return
    
    print("✅ Pinterest API configured!")
    
    try:
        boards = client.get_boards()
        print("\n📋 Your Boards:")
        for board in boards:
            print(f"  - {board['name']} (ID: {board['id']})")
    except Exception as e:
        print(f"\n⚠️ Could not fetch boards: {e}")
    
    products = get_approved_products()
    
    if not products:
        print("❌ No products found")
        return
    
    print(f"\n📦 Found {len(products)} products")
    
    if args.product:
        product = next((p for p in products if p['spec']['product_id'] == args.product), None)
        if not product:
            print(f"❌ Product {args.product} not found")
            return
        products_to_pin = [product]
    else:
        print("\n🗂️ Recent Products:")
        for i, p in enumerate(products[:10], 1):
            print(f"  [{i}] {p['spec']['name']}")
        
        choice = input("\nEnter product number to pin (or 'all' for all): ").strip()
        
        if choice.lower() == 'all':
            products_to_pin = products
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(products):
                products_to_pin = [products[idx]]
            else:
                print("❌ Invalid choice")
                return
        else:
            print("❌ Invalid choice")
            return
    
    for product in products_to_pin:
        spec = product['spec']
        print(f"\n📍 Pinning: {spec['name']}")
        
        content = generate_pin_content(spec)
        
        link = args.link or input("Enter Gumroad product link (or press Enter to skip): ").strip()
        
        if not link:
            print("⚠️ No link provided - skipping")
            continue
        
        image_url = args.image or input("Enter image URL (2:3 ratio recommended, or press Enter to skip): ").strip()
        
        try:
            pin = client.create_pin(
                title=content['title'],
                description=content['description'],
                link=link,
                image_url=image_url if image_url else None,
            )
            print(f"✅ Successfully pinned! Pin ID: {pin['id']}")
            print(f"🔗 View: https://pinterest.com/pin/{pin['id']}")
        except Exception as e:
            print(f"❌ Failed to pin: {e}")


if __name__ == "__main__":
    main()
