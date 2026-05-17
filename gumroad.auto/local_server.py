#!/usr/bin/env python3
"""
Local Server for Gumroad Product Factory
- Approve → Gumroad publish + Pinterest pin + marketing content generation
"""

import os
import json
import threading
import requests as _requests
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

import sys
sys.path.insert(0, str(Path(__file__).parent))
from gumroad_uploader import GumroadUploader
from agents.pinterest_agent import auto_pin, get_pin_status
from agents.traffic_agent    import generate_all as generate_marketing, get_marketing_content
from agents.bundle_creator   import find_bundle_candidates, create_bundle, auto_create_bundles

app = Flask(__name__, static_folder='.')
CORS(app)

BASE_DIR = Path(__file__).parent
PRODUCTS_DIR = BASE_DIR / "products"
FEEDBACK_DIR = BASE_DIR / "system" / "feedback"
REGISTRY_FILE = BASE_DIR / "data" / "products" / "registry.json"


@app.route('/')
def index():
    return app.send_static_file('admin_dashboard_server.html')


@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')


def load_product_spec(product_dir_name):
    if not product_dir_name:
        return None
    spec_file = PRODUCTS_DIR / product_dir_name / "spec.json"
    if spec_file.exists():
        with open(spec_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def extract_gumroad_description(product_dir: Path) -> str:
    """gumroad_page.md から説明文を取得。なければ content.md の冒頭を使う"""
    page_file = product_dir / "gumroad_page.md"
    if page_file.exists():
        with open(page_file, 'r', encoding='utf-8') as f:
            return f.read()
    content_file = product_dir / "content.md"
    if content_file.exists():
        with open(content_file, 'r', encoding='utf-8') as f:
            text = f.read()
        # 長すぎる場合は先頭2000文字
        return text[:2000]
    return ""


def get_price_for_gumroad(spec: dict) -> int:
    """Gumroad APIに渡す price 値を返す
    - price_jpy が있으면 そのまま（円、cents換算なし）
    - price_usd があれば セント換算（×100）
    - どちらもなければデフォルト980円
    """
    if "price_jpy" in spec:
        return int(spec["price_jpy"])
    if "price_usd" in spec:
        return int(spec["price_usd"] * 100)
    if "price" in spec:
        return int(spec["price"] * 100)
    return 980


def notify_discord(product: dict, price: int, published: bool):
    """Discord Webhook で出品/下書き保存を通知する"""
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return
    status = "出品完了" if published else "下書き保存"
    url = product.get("short_url") or f"https://app.gumroad.com/products/{product.get('id','')}"
    try:
        _requests.post(webhook_url, json={
            "content": f"**[AETERNA] {status}**\n商品名: {product.get('name','')}\n価格: ¥{price:,}\nURL: {url}"
        }, timeout=5)
    except Exception as e:
        print(f"[Discord通知失敗] {e}")


def save_feedback(feedback_data: dict):
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    feedback_file = FEEDBACK_DIR / "product_feedback.json"

    existing = {"approved": [], "rejected": []}
    if feedback_file.exists():
        with open(feedback_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)

    status = feedback_data.get("status", "approved")
    if status == "approved":
        existing["approved"].append(feedback_data)
    else:
        existing["rejected"].append(feedback_data)

    with open(feedback_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    return existing


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Server is running"})


@app.route('/api/products', methods=['GET'])
def list_products():
    """products/ ディレクトリを走査して未公開商品一覧を返す"""
    registry = load_registry()
    products = []

    if not PRODUCTS_DIR.exists():
        return jsonify({"success": True, "products": []})

    for product_dir in sorted(PRODUCTS_DIR.iterdir()):
        if not product_dir.is_dir():
            continue
        spec_file = product_dir / "spec.json"
        if not spec_file.exists():
            continue
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
        spec["_directory"] = product_dir.name

        # registry に登録済みなら published フラグを付ける
        reg_entry = registry.get(spec.get("product_id", ""))
        if reg_entry:
            spec["_gumroad_id"] = reg_entry.get("gumroad_product_id")
            spec["_published"] = True
        else:
            spec["_published"] = False

        products.append(spec)

    # 未公開を先に並べる
    products.sort(key=lambda p: (p.get("_published", False), -p.get("trend_score", 0)))
    return jsonify({"success": True, "products": products})


@app.route('/api/approve', methods=['POST'])
def approve_product():
    """商品を承認して Gumroad に出品する"""
    try:
        data = request.json
        product_dir_name = data.get("product_dir")
        publish = data.get("publish", False)
        reason = data.get("reason", "")
        notes = data.get("notes", "")

        if not product_dir_name:
            return jsonify({"success": False, "error": "product_dir が指定されていません"}), 400

        spec = load_product_spec(product_dir_name)
        if not spec:
            return jsonify({"success": False, "error": f"spec.json が見つかりません: {product_dir_name}"}), 404

        product_dir = PRODUCTS_DIR / product_dir_name
        uploader = GumroadUploader()

        price = get_price_for_gumroad(spec)
        description = extract_gumroad_description(product_dir)

        product = uploader.create_product(
            name=spec["name"],
            price_cents=price,
            description=description,
            published=publish
        )
        gumroad_id = product["id"]

        # コンテンツファイル（ZIP優先）を探す
        # NOTE: Gumroad API v2 は binary file upload 非対応 (404) のため
        # ファイルはダッシュボードの upload_url 経由で手動アップロードが必要。
        # ここでは ZIP の存在をチェックしてレスポンスに含めるだけ。
        skip_files = {"spec.json", "gumroad_page.md"}
        zip_files = sorted(product_dir.glob("*.zip"))
        upload_pending = [str(z) for z in zip_files]
        if not upload_pending:
            for ext in ["pdf", "md"]:
                for f in sorted(product_dir.glob(f"*.{ext}")):
                    if f.name not in skip_files:
                        upload_pending.append(str(f))
        print(f"[INFO] ファイルアップロードはGumroad UIから手動で行ってください: {[Path(p).name for p in upload_pending]}")

        # registry に保存
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        registry = load_registry()
        registry[spec["product_id"]] = {
            "gumroad_product_id": gumroad_id,
            "name": spec["name"],
            "price": price,
            "published": publish,
            "registered_at": datetime.now().isoformat(),
        }
        with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

        notify_discord(product, price, publish)

        gumroad_url = product.get("short_url") or f"https://app.gumroad.com/products/{gumroad_id}"

        # ── バックグラウンドで Pinterest + マーケティングコンテンツ生成 ────────
        def _post_approve_tasks():
            # 1. マーケティングコンテンツ生成（Reddit/Twitter/Email/SEO）
            try:
                generate_marketing(spec, gumroad_url)
            except Exception as e:
                print(f"[TrafficAgent] 生成失敗: {e}")
            # 2. Pinterest 自動投稿
            try:
                auto_pin(spec, gumroad_url)
            except Exception as e:
                print(f"[Pinterest] 投稿失敗: {e}")
            # 3. バンドル候補が揃っていれば自動作成
            try:
                new_bundles = auto_create_bundles(published_only=False, max_bundles=2)
                if new_bundles:
                    print(f"[Bundle] 自動作成: {[b['name'] for b in new_bundles]}")
            except Exception as e:
                print(f"[Bundle] 作成失敗: {e}")

        threading.Thread(target=_post_approve_tasks, daemon=True).start()

        feedback_data = {
            "status": "approved",
            "product_id": spec["product_id"],
            "name": spec["name"],
            "category": spec.get("category", ""),
            "subcategory": spec.get("subcategory", ""),
            "product_type": spec.get("product_type", ""),
            "price": price,
            "trend_score": spec.get("trend_score"),
            "reason": reason,
            "notes": notes,
            "gumroad_product_id": gumroad_id,
            "gumroad_url": gumroad_url,
            "recorded_at": datetime.now().isoformat(),
        }
        save_feedback(feedback_data)

        gumroad_edit_url = f"https://app.gumroad.com/products/{gumroad_id}/edit"
        return jsonify({
            "success": True,
            "product": product,
            "feedback": feedback_data,
            "gumroad_url": gumroad_url,
            "gumroad_edit_url": gumroad_edit_url,
            "upload_pending": [Path(p).name for p in upload_pending],
            "upload_note": "Gumroad APIはファイルアップロード非対応。上記ファイルをGumroad UIから手動アップロードしてください。",
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/reject', methods=['POST'])
def reject_product():
    """商品を却下してフィードバックを保存する"""
    try:
        data = request.json
        product_dir_name = data.get("product_dir")
        reason = data.get("reason", "")
        notes = data.get("notes", "")

        if not product_dir_name:
            return jsonify({"success": False, "error": "product_dir が指定されていません"}), 400

        spec = load_product_spec(product_dir_name)
        if not spec:
            return jsonify({"success": False, "error": f"spec.json が見つかりません: {product_dir_name}"}), 404

        feedback_data = {
            "status": "rejected",
            "product_id": spec["product_id"],
            "name": spec["name"],
            "category": spec.get("category", ""),
            "subcategory": spec.get("subcategory", ""),
            "product_type": spec.get("product_type", ""),
            "price": get_price_for_gumroad(spec),
            "trend_score": spec.get("trend_score"),
            "reason": reason,
            "notes": notes,
            "recorded_at": datetime.now().isoformat(),
        }
        save_feedback(feedback_data)

        return jsonify({"success": True, "feedback": feedback_data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/feedback/summary', methods=['GET'])
def feedback_summary():
    from feedback_tracker import FeedbackTracker
    tracker = FeedbackTracker()
    insights = tracker.get_insights()
    return jsonify({"success": True, "insights": insights})


@app.route('/api/marketing/<product_id>', methods=['GET'])
def marketing_content(product_id):
    """商品のマーケティングコンテンツを返す"""
    content = get_marketing_content(product_id)
    pin_status = get_pin_status(product_id)
    return jsonify({"success": True, "content": content, "pinterest": pin_status})


@app.route('/api/bundles', methods=['GET'])
def list_bundles():
    """バンドル候補一覧を返す"""
    candidates = find_bundle_candidates(published_only=False)
    return jsonify({"success": True, "candidates": [
        {
            "bundle_name":      c["bundle_name"],
            "product_count":    c["product_count"],
            "individual_total": c["individual_total"],
            "bundle_price":     c["bundle_price"],
            "savings":          c["savings"],
            "discount_pct":     c["discount_pct"],
            "products":         [{"name": p["name"], "type": p.get("product_type"),
                                  "price": p.get("_usd_price", p.get("price_usd", p.get("price", 0)))}
                                 for p in c["products"]],
        }
        for c in candidates
    ]})


@app.route('/api/bundles/create', methods=['POST'])
def create_bundle_endpoint():
    """バンドル商品を作成する"""
    try:
        data = request.json
        bundle_name = data.get("bundle_name")
        candidates = find_bundle_candidates()
        candidate = next((c for c in candidates if c["bundle_name"] == bundle_name), None)
        if not candidate:
            return jsonify({"success": False, "error": "Bundle not found"}), 404
        spec = create_bundle(candidate)
        return jsonify({"success": True, "bundle": spec})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """ダッシュボード統計"""
    registry = load_registry()
    all_products = []
    if PRODUCTS_DIR.exists():
        for d in PRODUCTS_DIR.iterdir():
            sf = d / "spec.json"
            if sf.exists():
                with open(sf) as f:
                    s = json.load(f)
                all_products.append(s)

    published_ids = set(registry.keys())
    published = [p for p in all_products if p.get("product_id") in published_ids]
    pending   = [p for p in all_products if p.get("product_id") not in published_ids
                 and not p.get("is_bundle")]

    # Pinterest 投稿数
    pin_log_path = BASE_DIR / "data" / "pinterest_posts.json"
    pin_count = len(json.loads(pin_log_path.read_text())) if pin_log_path.exists() else 0

    # マーケティングコンテンツ生成数
    mkt_count = sum(1 for p in all_products
                    if (PRODUCTS_DIR / p.get("product_id","") / "marketing" / "summary.json").exists())

    # 売上データ（あれば）
    analysis_file = BASE_DIR / "data" / "latest_analysis.json"
    revenue = 0
    sales_count = 0
    if analysis_file.exists():
        analysis = json.loads(analysis_file.read_text())
        revenue = analysis.get("total_revenue", 0)
        sales_count = analysis.get("total_sales", 0)

    return jsonify({
        "success": True,
        "total_products":    len(all_products),
        "published":         len(published),
        "pending_approval":  len(pending),
        "pinterest_pins":    pin_count,
        "marketing_ready":   mkt_count,
        "total_revenue":     revenue,
        "total_sales":       sales_count,
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  Gumroad Factory - Local Server")
    print("=" * 60)
    print(f"  Dashboard: http://localhost:8001")
    print(f"  Products : {PRODUCTS_DIR}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8001, debug=False)
