#!/usr/bin/env python3
"""
Gumroad Product Factory - Full Workflow Runner
Runs the complete workflow: Create products → Generate social content
"""

import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent


def run_command(cmd, description):
    """Run a command and show output"""
    print(f"\n{'='*70}")
    print(f"  🚀 {description}")
    print(f"{'='*70}\n")
    return os.system(f"cd {BASE_DIR} && {cmd}")


def main():
    print("="*70)
    print("  🏭 Gumroad Product Factory - Full Workflow")
    print("="*70)
    print("\nThis will:")
    print("  1. Create 5 new products")
    print("  2. Generate social media content (Pinterest & Twitter)")
    print("\nLet's go!\n")

    # Step 1: Create products
    result1 = run_command(
        "source venv/bin/activate && python main.py --count 5",
        "Creating 5 products..."
    )

    if result1 != 0:
        print("\n⚠️  Product creation had issues, but continuing...")
    else:
        print("\n✅ Products created successfully!")

    time.sleep(2)

    # Step 2: Generate social content
    result2 = run_command(
        "source venv/bin/activate && python social_content_generator.py",
        "Generating social media content..."
    )

    print("\n" + "="*70)
    print("  ✅ Workflow Complete!")
    print("="*70)
    print("\nNext steps:")
    print("  1. Check the products/ directory for new products")
    print("  2. Check social_content/ directory for generated posts")
    print("  3. Copy-paste social content into Buffer/Later/Tailwind")
    print("  4. Create visuals in Canva for Pinterest")
    print("\nGood luck! 🎉")


if __name__ == "__main__":
    main()
