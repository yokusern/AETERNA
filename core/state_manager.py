"""
state_manager.py — 会社の記憶 state.json の読み書きユーティリティ
全エージェントはこれを通じて状態を共有する
"""
import json
import fcntl
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

JST = timezone(timedelta(hours=9))
STATE_PATH = Path(__file__).parent.parent / "data" / "state.json"


def load() -> dict:
    """state.jsonを読み込む（ファイルが壊れていればデフォルト値を返す）"""
    if not STATE_PATH.exists():
        return _default_state()
    try:
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return _default_state()


def save(state: dict) -> None:
    """state.jsonをアトミックに書き込む（同時書き込みを防ぐ）"""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STATE_PATH.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp_path.replace(STATE_PATH)


def update(updates: dict) -> dict:
    """state.jsonの一部を更新して保存する"""
    state = load()
    _deep_merge(state, updates)
    save(state)
    return state


def log_decision(observation: str, decision: str, result: str = "pending") -> None:
    """意思決定をdecisions_logに追記する"""
    state = load()
    entry = {
        "date": datetime.now(JST).strftime("%Y-%m-%d"),
        "observation": observation,
        "decision": decision,
        "result": result,
        "timestamp": datetime.now(JST).isoformat(),
    }
    state.setdefault("decisions_log", []).append(entry)
    # 直近100件のみ保持
    state["decisions_log"] = state["decisions_log"][-100:]
    save(state)


def log_error(error: str, agent: str = "unknown") -> None:
    """エラーをstate.errorsに追記する"""
    state = load()
    state.setdefault("errors", []).append({
        "timestamp": datetime.now(JST).isoformat(),
        "agent": agent,
        "error": error,
    })
    state["errors"] = state["errors"][-50:]
    save(state)


def mark_run_complete() -> None:
    """実行完了を記録する"""
    state = load()
    state["last_run"] = datetime.now(JST).isoformat()
    state["run_count"] = state.get("run_count", 0) + 1
    state["errors"] = []  # 毎回クリア
    save(state)


def update_revenue(sales: list) -> None:
    """売上データをstate.revenueに反映する"""
    state = load()
    now = datetime.now(JST)
    cutoff_30 = now.timestamp() - 30 * 86400
    cutoff_7 = now.timestamp() - 7 * 86400

    total = 0
    last_30 = 0
    last_7 = 0
    by_product: dict = {}

    for sale in sales:
        price = sale.get("price", 0)
        product_name = sale.get("product_name", "unknown")
        created_at = sale.get("created_at", "")

        total += price
        try:
            ts = datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
            if ts >= cutoff_30:
                last_30 += price
            if ts >= cutoff_7:
                last_7 += price
        except Exception:
            last_30 += price
            last_7 += price

        if product_name not in by_product:
            by_product[product_name] = {"sales": 0, "revenue": 0}
        by_product[product_name]["sales"] += 1
        by_product[product_name]["revenue"] += price

    state["revenue"] = {
        "total_lifetime": total,
        "last_30_days": last_30,
        "last_7_days": last_7,
        "by_product": by_product,
    }
    save(state)


def register_product(product_id: str, published: bool = False) -> None:
    """新商品をstate.productsに登録する"""
    state = load()
    products = state.setdefault("products", {"published": [], "drafts": [], "total": 0})
    if published:
        if product_id not in products.get("published", []):
            products.setdefault("published", []).append(product_id)
        drafts = products.get("drafts", [])
        if product_id in drafts:
            drafts.remove(product_id)
    else:
        if product_id not in products.get("drafts", []) and product_id not in products.get("published", []):
            products.setdefault("drafts", []).append(product_id)
    products["total"] = len(products.get("published", [])) + len(products.get("drafts", []))
    save(state)


def register_agent(name: str, created_by_evolver: bool = False) -> None:
    """新エージェントをstate.agentsに登録する"""
    state = load()
    agents = state.setdefault("agents", {"active": [], "created_by_evolver": [], "total": 0})
    if name not in agents.get("active", []):
        agents.setdefault("active", []).append(name)
    if created_by_evolver and name not in agents.get("created_by_evolver", []):
        agents.setdefault("created_by_evolver", []).append(name)
    agents["total"] = len(agents.get("active", []))
    save(state)


def _deep_merge(base: dict, updates: dict) -> None:
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


def _default_state() -> dict:
    return {
        "last_run": None,
        "run_count": 0,
        "revenue": {"total_lifetime": 0, "last_30_days": 0, "last_7_days": 0, "by_product": {}},
        "products": {"published": [], "drafts": [], "total": 0},
        "agents": {"active": [], "created_by_evolver": [], "total": 0},
        "decisions_log": [],
        "market_insights": {"trending_topics": [], "last_scan": None},
        "errors": [],
        "next_actions": [],
    }
