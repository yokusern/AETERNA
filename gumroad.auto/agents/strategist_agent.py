"""
strategist_agent.py - 参謀エージェント
全エージェントの出力データを統合し、次の実行計画を決定する
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
PRODUCT_SPECS_DIR = Path(__file__).parent.parent / "product_specs"
PRODUCTS_DIR = Path(__file__).parent.parent / "products"


def load_state() -> dict:
    """現在の事業状態を読み込む"""
    state = {
        "total_revenue": 0,
        "total_sales": 0,
        "registered_products": 0,
        "unregistered_products": 0,
        "pending_specs": 0,
        "recommendations": [],
    }

    # 分析データ
    analysis_path = DATA_DIR / "latest_analysis.json"
    if analysis_path.exists():
        with open(analysis_path, encoding="utf-8") as f:
            analysis = json.load(f)
        state["total_revenue"] = analysis.get("total_revenue", 0)
        state["total_sales"] = analysis.get("total_sales", 0)
        state["recommendations"] = analysis.get("recommendations", [])

    # 登録済み商品数
    registry_path = DATA_DIR / "products" / "registry.json"
    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as f:
            state["registered_products"] = len(json.load(f))

    # 未登録商品数（ready_to_upload状態）
    if PRODUCTS_DIR.exists():
        for d in PRODUCTS_DIR.iterdir():
            spec = d / "spec.json"
            if spec.exists():
                with open(spec, encoding="utf-8") as f:
                    s = json.load(f)
                if s.get("status") == "ready_to_upload":
                    state["unregistered_products"] += 1

    # 未実行の企画書数
    if PRODUCT_SPECS_DIR.exists():
        state["pending_specs"] = len(list(PRODUCT_SPECS_DIR.glob("*.json")))

    return state


def decide_plan(state: dict) -> dict:
    """状態に基づいて今日のアクション計画を決定する"""
    actions = []
    priority = "high"

    # 未登録商品があれば最優先でアップロード
    if state["unregistered_products"] > 0:
        actions.append({
            "action": "upload_products",
            "reason": f"未登録商品が{state['unregistered_products']}件ある",
            "agent": "sales_optimizer_agent",
            "priority": "critical",
        })

    # 商品が5件未満なら新商品企画
    if state["registered_products"] < 5:
        actions.append({
            "action": "plan_new_product",
            "reason": f"商品数が{state['registered_products']}件と少ない（目標: 5件）",
            "agent": "product_planner_agent",
            "priority": "high",
        })

    # 企画書があれば商品制作
    if state["pending_specs"] > 0:
        actions.append({
            "action": "build_product",
            "reason": f"未制作の企画書が{state['pending_specs']}件ある",
            "agent": "product_builder_agent",
            "priority": "high",
        })

    # 売上分析は毎日実行
    actions.append({
        "action": "analyze_sales",
        "reason": "日次売上分析",
        "agent": "analytics_agent",
        "priority": "normal",
    })

    # 月収目標フェーズを判定
    revenue = state["total_revenue"]
    if revenue == 0:
        phase = "phase_1_first_sale"
        focus = "最初の1件の売上を達成する"
    elif revenue < 30000:
        phase = "phase_2_grow"
        focus = "月商¥30,000を目指す"
    elif revenue < 100000:
        phase = "phase_3_scale"
        focus = "月商¥100,000を目指す（Affiliate.auto再始動準備）"
    else:
        phase = "phase_4_expand"
        focus = "Affiliate.auto再始動"

    plan = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "phase": phase,
        "focus": focus,
        "state_summary": {
            "revenue": f"¥{state['total_revenue']:,}",
            "sales": state["total_sales"],
            "products": state["registered_products"],
        },
        "actions": sorted(actions, key=lambda x: {"critical": 0, "high": 1, "normal": 2}[x["priority"]]),
        "generated_at": datetime.now().isoformat(),
    }

    return plan


def save_plan(plan: dict) -> str:
    """実行計画をファイルに保存する"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    plan_path = DATA_DIR / "daily_plan.json"
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    print(f"実行計画保存: {plan_path}")
    return str(plan_path)


def run():
    print("=== Strategist Agent 起動 ===")

    state = load_state()
    plan = decide_plan(state)
    save_plan(plan)

    print(f"\n=== 今日の実行計画 ===")
    print(f"フェーズ: {plan['phase']}")
    print(f"フォーカス: {plan['focus']}")
    print(f"現状: 売上¥{state['total_revenue']:,} | 販売{state['total_sales']}件 | 商品{state['registered_products']}件")
    print(f"\nアクション（優先度順）:")
    for i, action in enumerate(plan["actions"], 1):
        print(f"  {i}. [{action['priority'].upper()}] {action['action']} → {action['agent']}")
        print(f"      理由: {action['reason']}")

    return plan


if __name__ == "__main__":
    run()
