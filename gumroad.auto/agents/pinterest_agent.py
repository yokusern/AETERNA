#!/usr/bin/env python3
"""
Pinterest Auto-posting Agent
商品承認後にPinterestへ自動投稿する。
- 1商品につき3パターンのピンを作成
- カテゴリ別ボードへ振り分け（環境変数で設定）
- 投稿履歴を data/pinterest_posts.json に記録
"""
import os, sys, json, time, random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from pinterest_client import PinterestClient

BASE_DIR = Path(__file__).parent.parent
PIN_LOG   = BASE_DIR / "data" / "pinterest_posts.json"

# ── カテゴリ別ハッシュタグ ────────────────────────────────────────────────────
CATEGORY_TAGS = {
    "Productivity": ["productivity", "notiontemplate", "organization", "timemanagement", "workspace"],
    "AI":           ["artificialintelligence", "chatgpt", "promptengineering", "aitools", "openai"],
    "Finance":      ["budgeting", "personalfinance", "moneytips", "savingmoney", "financefreedom"],
    "Business":     ["entrepreneurship", "sidehustle", "smallbusiness", "onlinebusiness", "passiveincome"],
    "Marketing":    ["digitalmarketing", "socialmediatips", "contentmarketing", "marketing", "growthhacking"],
    "Programming":  ["coding", "python", "programming", "webdev", "developer"],
    "Design":       ["uidesign", "uxdesign", "designtips", "webdesign", "graphicdesign"],
}

# ── カテゴリ別ボードID（環境変数から取得、なければデフォルト）─────────────────
def _board_id(category: str) -> str:
    key = f"PINTEREST_BOARD_{category.upper()}"
    return os.environ.get(key) or os.environ.get("PINTEREST_BOARD_ID", "")

# ── 画像URL（picsum.photos — 常に有効、seedで商品ごとに固定）────────────────
def _image_url(product_id: str, variant: int = 0) -> str:
    seed = f"{product_id}-v{variant}"
    return f"https://picsum.photos/seed/{seed}/1000/1500"

# ── ピンコンテンツ生成 ─────────────────────────────────────────────────────────
PIN_TEMPLATES = [
    {
        "title_tpl": "{name}",
        "desc_tpl": (
            "Ready to level up your {subcategory} skills?\n\n"
            "This {product_type} gives you:\n"
            "✅ Step-by-step guidance\n"
            "✅ Real templates & frameworks\n"
            "✅ Actionable from day one\n"
            "✅ Instant digital download\n\n"
            "Only ${price} — save this pin!\n\n"
            "#{tag0} #{tag1} #{tag2} #digitaldownload #gumroad"
        ),
    },
    {
        "title_tpl": "Stop wasting time on {subcategory} — get the shortcut",
        "desc_tpl": (
            "I spent months figuring out {subcategory}.\n"
            "Now it's all packed into one {product_type}.\n\n"
            "📦 {name}\n"
            "💰 ${price} one-time purchase\n"
            "⚡ Instant download\n\n"
            "Link in bio or search Gumroad.\n\n"
            "#{tag0} #{tag1} #{tag3} #selfimprovement #learnonline"
        ),
    },
    {
        "title_tpl": "{name} — Digital Download",
        "desc_tpl": (
            "Everything you need to master {subcategory}, in one place.\n\n"
            "Perfect for beginners & intermediates who want:\n"
            "→ Clarity over confusion\n"
            "→ Templates they can use today\n"
            "→ No fluff, just results\n\n"
            "${price} · Instant access · Keep forever\n\n"
            "#{tag1} #{tag2} #{tag4} #gumroad #digitalproduct"
        ),
    },
]

def _make_pin(spec: dict, template: dict, image_url: str) -> dict:
    cat   = spec.get("category", "Business")
    tags  = CATEGORY_TAGS.get(cat, ["digitalproduct", "onlinelearning", "download"])
    ptype = spec.get("product_type", "guide").replace("_", " ")
    price = spec.get("price_usd", spec.get("price", 15))

    ctx = {
        "name": spec["name"][:80],
        "subcategory": spec.get("subcategory", ""),
        "product_type": ptype,
        "price": price,
        **{f"tag{i}": tags[i % len(tags)] for i in range(5)},
    }

    return {
        "title":       template["title_tpl"].format(**ctx)[:100],
        "description": template["desc_tpl"].format(**ctx)[:800],
        "image_url":   image_url,
    }


# ── メイン関数 ─────────────────────────────────────────────────────────────────

def auto_pin(spec: dict, gumroad_url: str, delay_between: float = 3.0) -> list:
    """
    商品を Pinterest に3パターン投稿する。
    Returns: list of created pin dicts (or empty if not configured)
    """
    client = PinterestClient()
    if not client.is_configured():
        print("[Pinterest] 未設定 — PINTEREST_ACCESS_TOKEN と PINTEREST_BOARD_ID を .env に追加してください")
        return []

    cat    = spec.get("category", "Business")
    board  = _board_id(cat)
    pid    = spec["product_id"]
    created = []

    for i, tmpl in enumerate(PIN_TEMPLATES):
        img = _image_url(pid, i)
        pin = _make_pin(spec, tmpl, img)
        try:
            result = client.create_pin(
                title=pin["title"],
                description=pin["description"],
                link=gumroad_url,
                image_url=pin["image_url"],
                board_id=board or None,
            )
            created.append({
                "pin_id":  result.get("id"),
                "title":   pin["title"],
                "url":     f"https://pinterest.com/pin/{result.get('id','')}",
                "created": datetime.now().isoformat(),
            })
            print(f"[Pinterest] ピン作成 ({i+1}/3): {pin['title'][:50]}")
            if i < len(PIN_TEMPLATES) - 1:
                time.sleep(delay_between)
        except Exception as e:
            print(f"[Pinterest] ピン作成失敗 ({i+1}/3): {e}")

    _save_log(pid, spec["name"], gumroad_url, created)
    return created


def _save_log(product_id: str, name: str, url: str, pins: list):
    PIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    log = {}
    if PIN_LOG.exists():
        log = json.loads(PIN_LOG.read_text())
    log[product_id] = {
        "name":    name,
        "url":     url,
        "pins":    pins,
        "pinned_at": datetime.now().isoformat(),
    }
    PIN_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=2))


def get_pin_status(product_id: str) -> dict:
    """商品のPinterest投稿状況を返す"""
    if not PIN_LOG.exists():
        return {}
    log = json.loads(PIN_LOG.read_text())
    return log.get(product_id, {})


def pin_unpinned(registry_path: Path, delay: float = 5.0):
    """
    registry.json に登録済みで未ピンの商品を全部ピンする（バッチ実行用）
    """
    if not registry_path.exists():
        print("[Pinterest] registry.json が見つかりません")
        return

    registry = json.loads(registry_path.read_text())
    log = json.loads(PIN_LOG.read_text()) if PIN_LOG.exists() else {}

    for product_id, entry in registry.items():
        if product_id in log:
            continue  # already pinned
        spec_file = registry_path.parent.parent.parent / "products" / entry.get("name", product_id) / "spec.json"
        # Try to find spec by product_id in products dir
        products_dir = registry_path.parent.parent.parent / "products"
        spec = None
        for d in products_dir.iterdir():
            sf = d / "spec.json"
            if sf.exists():
                s = json.loads(sf.read_text())
                if s.get("product_id") == product_id:
                    spec = s
                    break
        if not spec:
            continue

        url = entry.get("gumroad_url") or f"https://gumroad.com/l/{entry.get('gumroad_product_id','')}"
        if not url or "l/" not in url:
            continue

        print(f"[Pinterest] ピン中: {spec['name']}")
        auto_pin(spec, url, delay_between=delay)
        time.sleep(delay)


if __name__ == "__main__":
    print("Pinterest Agent — バッチモード")
    registry = BASE_DIR / "data" / "products" / "registry.json"
    pin_unpinned(registry)
