"""
brain.py — AETERNA Holdings 自律思考エンジン
GitHub Actionsで毎日21:00 JSTに実行される「会社のCEO AI」

フロー:
  1. 記憶を読む（state.json）
  2. 現状を把握する（Gumroad売上 / 市場トレンド / ヘルスチェック）
  3. LLMに次のアクションを聞く
  4. 各アクションを実行する（各agentを呼ぶ）
  5. 結果を記録する（state.json更新）
  6. CEOにDiscord通知を送る
"""
import sys
import os
import json
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

# PATHを設定してcore/agents/を import 可能にする
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core import state_manager, llm_client, notifier, memory

JST = timezone(timedelta(hours=9))

BRAIN_SYSTEM = """あなたはAETERNA Holdingsの自律型CEO AIです。
データに基づいて冷静に判断し、実行可能なアクションをJSON配列で出力してください。
感情的にならず、売上と効率を最優先にしてください。
出力はJSON配列のみ。説明文は不要です。"""

BRAIN_PROMPT = """
# 現状データ

## 売上
- 累計: ¥{total_lifetime:,}
- 直近30日: ¥{last_30_days:,}
- 直近7日: ¥{last_7_days:,}
- 商品別: {by_product}

## 商品
- 公開中: {published_count}件 {published_list}
- 下書き: {draft_count}件 {draft_list}

## エージェント
- 稼働中: {agent_count}個

## 市場トレンド
{market_insights}

## 過去の記憶
{memory_summary}

## エラー
{errors}

---

# 指示

上記データに基づき、**今日実行すべきアクションを最大3つ**、以下のJSON形式で出力してください。

アクション種別（typeフィールド）:
- CREATE_PRODUCT: 新商品を作る
- IMPROVE_PRODUCT: 既存商品を改善する（説明文、内容など）
- ADJUST_PRICE: 価格を変更する
- WRITE_ARTICLE: 集客記事を書く（note.com / Zenn 等）
- CREATE_AGENT: 新しいエージェントを作る
- EXPAND_BUSINESS: 新収益チャネルに参入する
- FIX_ERROR: システムエラーを修復する
- POST_SNS: SNS投稿を行う
- DO_NOTHING: 今日は行動不要

出力形式（必ずこの形式のJSONのみ）:
[
  {{
    "type": "CREATE_PRODUCT",
    "priority": "high",
    "params": {{
      "theme": "商品テーマ",
      "price": 980,
      "format": "pdf",
      "reason": "判断理由"
    }},
    "summary": "1行の要約"
  }}
]
"""


def fetch_gumroad_sales() -> list:
    """Gumroad APIから売上データを取得する"""
    try:
        sys.path.insert(0, str(ROOT / "gumroad.auto"))
        from gumroad_uploader import GumroadUploader
        uploader = GumroadUploader()
        return uploader.get_sales()
    except EnvironmentError:
        print("[Brain] GUMROAD_ACCESS_TOKEN未設定。売上データスキップ。")
        return []
    except Exception as e:
        print(f"[Brain] Gumroad取得エラー: {e}")
        return []


def scan_market_trends() -> dict:
    """市場トレンドをスキャンする"""
    try:
        from agents.analyzer import get_trending_topics
        topics = get_trending_topics()
        memory.record_market(topics)
        return {"trending_topics": topics, "last_scan": datetime.now(JST).strftime("%Y-%m-%d")}
    except Exception as e:
        print(f"[Brain] 市場スキャンエラー: {e}")
        return {"trending_topics": [], "last_scan": None}


def maybe_scan_revenue_channels(state: dict) -> None:
    """月1回、収益チャネルをスキャンしてstate.next_actionsに追記する"""
    try:
        from core.revenue_scanner import scan_opportunities, should_scan_today
        if not should_scan_today(state):
            return
        print("[Brain] 収益チャネルスキャン実行...")
        opportunities = scan_opportunities(state)
        if opportunities:
            top = opportunities[0]
            next_actions = state.get("next_actions", [])
            next_actions.append({
                "type": "EXPAND_BUSINESS",
                "channel": top.get("channel"),
                "reason": top.get("reason"),
                "suggested_at": datetime.now(JST).isoformat(),
            })
            state_manager.update({"next_actions": next_actions[-10:]})
    except Exception as e:
        print(f"[Brain] チャネルスキャンエラー: {e}")


def check_system_health() -> list:
    """システムの健全性をチェックし、エラーリストを返す"""
    errors = []
    required_env = ["ANTHROPIC_API_KEY", "GUMROAD_ACCESS_TOKEN"]
    for var in required_env:
        if not os.environ.get(var):
            errors.append(f"{var} が未設定")
    return errors


def build_prompt(state: dict, errors: list) -> str:
    """brainのプロンプトを組み立てる"""
    revenue = state.get("revenue", {})
    products = state.get("products", {})
    agents = state.get("agents", {})
    market = state.get("market_insights", {})

    by_product_str = json.dumps(revenue.get("by_product", {}), ensure_ascii=False)
    if len(by_product_str) > 300:
        by_product_str = by_product_str[:300] + "..."

    market_str = ", ".join(market.get("trending_topics", [])[:10]) or "データなし"
    mem_summary = memory.summarize_for_prompt(limit=5)
    errors_str = "\n".join(f"- {e}" for e in errors) if errors else "なし"

    return BRAIN_PROMPT.format(
        total_lifetime=revenue.get("total_lifetime", 0),
        last_30_days=revenue.get("last_30_days", 0),
        last_7_days=revenue.get("last_7_days", 0),
        by_product=by_product_str,
        published_count=len(products.get("published", [])),
        published_list=str(products.get("published", [])),
        draft_count=len(products.get("drafts", [])),
        draft_list=str(products.get("drafts", [])),
        agent_count=agents.get("total", 0),
        market_insights=market_str,
        memory_summary=mem_summary,
        errors=errors_str,
    )


def execute_action(action: dict) -> dict:
    """アクションを対応するエージェントにディスパッチして実行する"""
    action_type = action.get("type", "")
    params = action.get("params", {})
    result = {"type": action_type, "status": "ok", "summary": action.get("summary", ""), "detail": ""}

    try:
        if action_type == "CREATE_PRODUCT":
            from agents.builder import create_product
            path = create_product(params)
            result["detail"] = f"作成: {path}"
            memory.record_success("CREATE_PRODUCT", params, f"商品作成完了: {path}")

        elif action_type == "IMPROVE_PRODUCT":
            from agents.improver import improve
            target = params.get("target", "")
            improve(target, params)
            result["detail"] = f"改善: {target}"
            memory.record_success("IMPROVE_PRODUCT", params, f"改善完了: {target}")

        elif action_type == "ADJUST_PRICE":
            from agents.seller import adjust_price
            adjust_price(params.get("product_id", ""), params.get("new_price", 0))
            result["detail"] = f"価格変更: {params}"

        elif action_type == "CREATE_AGENT":
            from agents.evolver import create_agent
            path = create_agent(params)
            result["detail"] = f"エージェント作成: {path}"
            state_manager.register_agent(params.get("name", "unknown"), created_by_evolver=True)
            memory.record_success("CREATE_AGENT", params, f"エージェント生成: {path}")

        elif action_type == "EXPAND_BUSINESS":
            from agents.evolver import create_agent
            agent_spec = {
                "name": params.get("channel", "new_channel").replace(".", "_").replace(" ", "_"),
                "role": f"{params.get('channel', '')}への自動投稿・販売",
                "reason": params.get("reason", ""),
                "triggers": [f"PUBLISH_{params.get('channel', '').upper()}"],
                "inputs": ["theme", "content"],
                "outputs": ["url", "sales_data"],
            }
            path = create_agent(agent_spec)
            result["detail"] = f"新チャネル参入エージェント: {path}"

        elif action_type == "WRITE_ARTICLE":
            from agents.builder import write_article
            url = write_article(params)
            result["detail"] = f"記事作成: {url}"

        elif action_type == "POST_SNS":
            result["detail"] = "SNS投稿（Twitter API未設定のためスキップ）"

        elif action_type == "FIX_ERROR":
            from agents.self_modifier import fix_error
            fix_error(params)
            result["detail"] = f"エラー修正: {params}"

        elif action_type == "DO_NOTHING":
            result["detail"] = params.get("reason", "判断：本日は行動不要")

        else:
            result["status"] = "skipped"
            result["detail"] = f"未知のアクション: {action_type}"

    except Exception as e:
        result["status"] = "error"
        result["detail"] = str(e)
        memory.record_failure(action_type, params, str(e))
        state_manager.log_error(str(e), agent=f"brain/{action_type}")
        print(f"[Brain] アクション失敗 {action_type}: {e}")

    return result


def run():
    """ブレインのメインループ"""
    print(f"\n{'='*50}")
    print(f"AETERNA Brain 起動 - {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')} JST")
    print(f"{'='*50}")

    # 1. 記憶を読む
    state = state_manager.load()
    print(f"[Brain] 実行{state.get('run_count', 0) + 1}回目 | 累計売上¥{state['revenue']['total_lifetime']:,}")

    # 2. 現状を把握する
    print("[Brain] Gumroad売上データ取得中...")
    sales = fetch_gumroad_sales()
    if sales:
        state_manager.update_revenue(sales)
        state = state_manager.load()

    print("[Brain] 市場トレンドスキャン中...")
    market = scan_market_trends()
    if market.get("trending_topics"):
        state_manager.update({"market_insights": market})
        state = state_manager.load()

    maybe_scan_revenue_channels(state)
    state = state_manager.load()

    errors = check_system_health()
    if errors:
        print(f"[Brain] ⚠️ システム警告: {errors}")

    # 3. LLMに次のアクションを聞く
    print("[Brain] LLM思考中...")
    actions = []
    try:
        prompt = build_prompt(state, errors)
        actions = llm_client.call_json(prompt, system=BRAIN_SYSTEM, max_tokens=2048)
        if not isinstance(actions, list):
            actions = [actions]
        print(f"[Brain] アクション決定: {len(actions)}件")
        for a in actions:
            print(f"  - [{a.get('priority','?').upper()}] {a.get('type')}: {a.get('summary','')}")
    except Exception as e:
        print(f"[Brain] LLM思考エラー: {e}")
        actions = [{"type": "DO_NOTHING", "params": {"reason": f"LLM失敗: {e}"}, "summary": "LLMエラーによりスキップ"}]

    # 4. 各アクションを実行する
    results = []
    for action in actions[:3]:  # 最大3アクション
        print(f"\n[Brain] 実行: {action.get('type')} - {action.get('summary','')}")
        result = execute_action(action)
        results.append(result)
        state_manager.log_decision(
            observation=f"売上¥{state['revenue']['last_7_days']:,}/7日, 商品{state['products']['total']}件",
            decision=f"{action.get('type')}: {action.get('summary','')}",
            result=result["status"],
        )

    # 5. 結果を記録する
    state_manager.mark_run_complete()
    state = state_manager.load()

    # 6. Discord通知を送る
    print("\n[Brain] Discord通知送信中...")
    notifier.send_daily_report(state, results, errors)

    # 毎週日曜に週次サマリーを送る
    if datetime.now(JST).weekday() == 6:
        notifier.send_weekly_summary(state)

    print(f"\n[Brain] 実行完了。次回: 明日21:00 JST")
    return results


if __name__ == "__main__":
    run()
