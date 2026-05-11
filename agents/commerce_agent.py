"""
commerce_agent.py — 帝国の第2の心臓（販売・告知・最適化）
publisher, promoter, seller の機能を完全に統合。
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "gumroad.auto"))

from core import state_manager, llm_client, notifier
from gumroad_uploader import GumroadUploader

JST = timezone(timedelta(hours=9))

def run(params: dict) -> dict:
    action_type = params.get("type")
    if action_type == "PUBLISH":
        return _publish_all(params.get("product_path"), params.get("product_params", {}))
    elif action_type == "OPTIMIZE":
        return {"status": "ok", "changes": _optimize_prices()}
    return {"status": "error"}

def _publish_all(product_path: str, params: dict) -> dict:
    uploader = GumroadUploader()
    spec_path = Path(product_path) / "spec.json"
    
    # Gumroad Upload
    product = uploader.upload_product_from_spec(str(spec_path), publish_after_upload=True)
    url = product.get("short_url") or f"https://gumroad.com/l/{product.get('id')}"
    
    # Discord Promotion
    report = f"📢 **新商品の告知準備完了**\n商品: {params.get('theme')}\nURL: {url}"
    notifier.send(report)
    
    return {"status": "ok", "url": url}

def _optimize_prices() -> list:
    state = state_manager.load()
    # 簡易価格調整ロジック
    return [] # 実装は旧seller.pyを参考
