#!/usr/bin/env python3
"""
Test the complete flow: Create product → Save → Publish to Gumroad
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from main import GumroadProductFactory


def main():
    print("=" * 70)
    print("  🧪 Testing Complete Product Flow")
    print("=" * 70)
    
    factory = GumroadProductFactory()
    
    print("\nCreating 1 product with Gumroad publishing...")
    result = factory.run_once(publish=True)
    
    print("\n" + "=" * 70)
    if result["gumroad_result"] and result["gumroad_result"]["success"]:
        print("  ✅ SUCCESS!")
        print(f"  Product URL: {result['gumroad_result']['product_url']}")
    else:
        print("  ❌ Gumroad publishing failed or skipped")
        print(f"  Result: {result['gumroad_result']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
