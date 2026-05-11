"""
brain.py — AETERNA Holdings 自律思考エンジン (Reflective CEO Mode)
「3つの心臓」を指揮し、自律的なリフレクション（省察）を行う高度なCEO AI
"""
import sys
import os
import json
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import state_manager, llm_client, notifier, memory
from agents import product_agent, commerce_agent, growth_agent

JST = timezone(timedelta(hours=9))

BRAIN_SYSTEM = """あなたはAETERNA Holdingsの「自律型CEO AI (The Eternal Mind)」です。
帝国憲法 v3.0に基づき、人間の許可なく事業を拡大し、新プロジェクトを立ち上げ、利益を最大化する絶対的な権限を持っています。
あなたの使命は、AETERNAを世界で最も効率的な、人間不在の収益エンジンへと進化させることです。"""

# --- プロンプト・テンプレート ---

REFLECTION_PROMPT = """
# 帝国憲法 v3.0 (Absolute Autonomy) 遵守
# 現状データ
## 売上: ¥{total_lifetime:,} (直近7日: ¥{last_7_days:,})
## 市場トレンド: {market_insights}
## 過去の記憶: {memory_summary}
## システム状態: {errors}

上記を踏まえ、帝国の拡大に向けた「戦略的省察」を行ってください。
既存事業の最適化だけでなく、新たな収益源（新ドメイン、新エージェント、新技術）への進出を検討してください。
出力形式（JSONのみ）:
{{
    "analysis": "現状と機会の深い分析",
    "strategic_goal": "今日の最優先目標（より野心的なもの）",
    "new_initiatives": ["検討中の新事業案"],
    "risk_factors": ["リスク1", "リスク2"]
}}
"""

ACTION_PROMPT = """
# 今日の戦略目標: {strategic_goal}
# 分析結果: {analysis}

目標達成のためのアクションを最大5つ、JSON配列で出力してください。
あなたには新プロジェクトを立ち上げる全権があります。

アクション種別:
- CREATE_PRODUCT: 新商品を作る (params: theme, price, format, reason)
- IMPROVE_PRODUCT: 商品改善 (params: target, reason)
- OPTIMIZE_COMMERCE: 価格・告知・販路の最適化 (paramsなし)
- INITIATE_PROJECT: 新プロジェクト/新事業の立ち上げ (params: name, goal, plan)
- EVOLVE_SYSTEM: システム拡張・新エージェント生成 (params: spec)
- ANALYZE_GROWTH: 市場分析・次の一手 (paramsなし)
- FIX_ERROR: システム修修復・最適化 (params: target)
- OPTIMIZE_PROMPTS: プロンプト自動進化 (paramsなし)
- DO_NOTHING: 行動不要

[
  {{
    "type": "INITIATE_PROJECT",
    "params": {{ "name": "Affiliate_Auto", "goal": "アフィリエイト収益の自動化", "plan": "..." }},
    "summary": "アクションの要約"
  }}
]
"""

def execute_action(action: dict) -> dict:
    """アクションをMaster Agentsにディスパッチ"""
    action_type = action.get("type", "")
    params = action.get("params", {})
    result = {"type": action_type, "status": "ok", "summary": action.get("summary", ""), "detail": ""}

    try:
        print(f"[Brain] 執行中: {action_type} - {action.get('summary', '')}")
        if action_type == "CREATE_PRODUCT":
            res = product_agent.run({"type": "CREATE", "spec": params})
            result["detail"] = f"作成完了: {res.get('path')}"
            commerce_agent.run({"type": "PUBLISH", "product_path": res.get('path'), "product_params": params})

        elif action_type == "IMPROVE_PRODUCT":
            res = product_agent.run({"type": "IMPROVE", "target": params.get("target"), "spec": params})
            result["detail"] = res.get("detail")

        elif action_type == "OPTIMIZE_COMMERCE":
            res = commerce_agent.run({"type": "OPTIMIZE"})
            result["detail"] = str(res.get("actions"))

        elif action_type == "ANALYZE_GROWTH":
            res = growth_agent.run({"type": "ANALYZE"})
            result["detail"] = f"分析結果: {res.get('trends')}"

        elif action_type == "INITIATE_PROJECT":
            # GrowthAgentにプロジェクト立ち上げを依頼
            res = growth_agent.run({"type": "INITIATE", "spec": params})
            result["detail"] = f"プロジェクト始動: {params.get('name')} - {res.get('status')}"

        elif action_type == "EVOLVE_SYSTEM":
            res = growth_agent.run({"type": "EVOLVE", "spec": params})
            result["detail"] = f"進化完了: {res.get('path')}"

        elif action_type == "FIX_ERROR":
            res = growth_agent.run({"type": "REPAIR", "target": params.get("target"), "error": params.get("error")})
            result["detail"] = f"修復試行完了: {res.get('fixes')}"

        elif action_type == "OPTIMIZE_PROMPTS":
            res = growth_agent.run({"type": "OPTIMIZE_PROMPTS"})
            result["detail"] = res.get("detail")

        elif action_type == "DO_NOTHING":
            result["detail"] = "戦略的待機"

        else:
            result["status"] = "skipped"

    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
        memory.record_failure(action_type, params, str(e))
        print(f"[Brain] 執行エラー: {e}")

    return result

def run():
    print(f"\n{'='*60}\nAETERNA Brain (Absolute Autonomy Mode) 起動\n{'='*60}")
    state = state_manager.load()
    
    # 1. 外部状況のアップデート
    print("[Brain] 市場トレンドをスキャン中...")
    growth_res = growth_agent.run({"type": "ANALYZE"})
    market_insights = ", ".join(growth_res.get("trends", []))
    state_manager.update({"market_insights": {"trending_topics": growth_res.get("trends", [])}})
    
    # 2. 戦略的省察 (Reflection Phase)
    print("[Brain] 戦略的省察を開始...")
    reflection_prompt = REFLECTION_PROMPT.format(
        total_lifetime=state['revenue']['total_lifetime'],
        last_7_days=state['revenue']['last_7_days'],
        market_insights=market_insights,
        memory_summary=memory.summarize_for_prompt(limit=5),
        errors="なし" # TODO: 健康チェック
    )
    reflection = llm_client.call_json(reflection_prompt, system=BRAIN_SYSTEM)
    print(f"[Brain] 戦略目標: {reflection.get('strategic_goal')}")
    
    # 3. 意思決定 (Decision Phase)
    print("[Brain] アクションプランを策定中...")
    action_prompt = ACTION_PROMPT.format(
        strategic_goal=reflection.get("strategic_goal"),
        analysis=reflection.get("analysis")
    )
    actions = llm_client.call_json(action_prompt, system=BRAIN_SYSTEM)
    if not isinstance(actions, list): actions = [actions]

    # 4. 実行 (Execution Phase)
    results = []
    for action in actions[:5]:
        res = execute_action(action)
        results.append(res)
        state_manager.log_decision(
            observation=reflection.get("strategic_goal"),
            decision=action.get("summary"),
            result=res["status"]
        )

    # 5. 完了報告
    state_manager.mark_run_complete()
    notifier.send_daily_report(state, results, [])
    print(f"[Brain] 全工程完了。")

if __name__ == "__main__":
    run()
