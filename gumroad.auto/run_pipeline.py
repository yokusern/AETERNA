"""
run_pipeline.py - パイプライン手動実行エントリポイント
ローカルで全エージェントを順番に実行する
"""
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="AETERNA Gumroadパイプライン")
    parser.add_argument("command", nargs="?", default="all",
                        choices=["all", "analyze", "plan", "build", "upload", "strategy"],
                        help="実行するコマンド（デフォルト: all）")
    parser.add_argument("--publish", action="store_true", help="Gumroadに公開する")
    parser.add_argument("--skip-build", action="store_true", help="商品制作をスキップ")
    args = parser.parse_args()

    print("=" * 50)
    print("AETERNA Gumroad Pipeline")
    print("=" * 50)

    from agents.analytics_agent import run as run_analytics
    from agents.strategist_agent import run as run_strategy
    from agents.product_planner_agent import run as run_planner
    from agents.product_builder_agent import run as run_builder
    from agents.sales_optimizer_agent import run as run_optimizer

    if args.command in ("all", "analyze"):
        print("\n[1/5] Analytics Agent")
        run_analytics()

    if args.command in ("all", "strategy"):
        print("\n[2/5] Strategist Agent")
        run_strategy()

    if args.command in ("all", "plan"):
        print("\n[3/5] Product Planner Agent")
        run_planner()

    if args.command in ("all", "build") and not args.skip_build:
        print("\n[4/5] Product Builder Agent")
        run_builder()

    if args.command in ("all", "upload"):
        print("\n[5/5] Sales Optimizer Agent")
        run_optimizer(publish=args.publish)

    print("\n" + "=" * 50)
    print("パイプライン完了")
    print("=" * 50)


if __name__ == "__main__":
    main()
