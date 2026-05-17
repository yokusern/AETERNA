#!/usr/bin/env python3
"""
Bundle Creator Agent
関連商品を1つのバンドル商品にまとめ、高単価で出品する。
- 同カテゴリ/タイプの商品を自動グルーピング
- 30% ディスカウントで提示（体感お得感あり、実際のAOVは向上）
- バンドル用 ZIP + gumroad_page.md を生成
"""
import json, zipfile, shutil
from pathlib import Path
from datetime import datetime
import time

BASE_DIR     = Path(__file__).parent.parent
PRODUCTS_DIR = BASE_DIR / "products"
REGISTRY     = BASE_DIR / "data" / "products" / "registry.json"

# ── バンドル定義 ──────────────────────────────────────────────────────────────
# (名前, 対象タイプリスト, 最小商品数, 最大商品数)
BUNDLE_BLUEPRINTS = [
    ("Ultimate Notion Template Bundle",  ["notion_template", "template"], 3, 6),
    ("Complete Prompt Pack Collection",  ["prompt_pack"],                 3, 5),
    ("Python & Script Automation Pack",  ["script_pack", "toolkit"],      2, 5),
    ("Business Starter Kit",             ["business_template", "guide"],  3, 5),
    ("Finance Tracker Mega Bundle",      ["spreadsheet_pack"],            2, 4),
    ("Productivity OS Bundle",           ["notion_template", "checklist_pack", "html_tool"], 3, 6),
    ("Freelancer Complete Toolkit",      ["business_template", "checklist_pack", "guide"], 3, 5),
    ("AI & Prompt Engineering Bundle",   ["prompt_pack", "guide"],        3, 5),
]


def _load_registry() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {}


def _usd_price(spec: dict) -> float:
    """スペックから USD 価格を取得（price_jpy は無視、USD のみ対象）"""
    p = spec.get("price_usd") or spec.get("price")
    try:
        p = float(p)
        # price_jpy が price に混入している場合 ($100超は除外)
        return p if 1 <= p <= 100 else 0
    except (TypeError, ValueError):
        return 0


def _all_products() -> list:
    """products/ ディレクトリの全 spec を返す（価格が有効なものだけ）"""
    specs = []
    if not PRODUCTS_DIR.exists():
        return specs
    for d in PRODUCTS_DIR.iterdir():
        sf = d / "spec.json"
        if sf.exists():
            s = json.loads(sf.read_text())
            s["_dir"] = d
            s["_usd_price"] = _usd_price(s)
            if s["_usd_price"] > 0:  # 価格が無効なものはスキップ
                specs.append(s)
    return specs


def _get_published_products() -> list:
    """Gumroadに出品済みの商品のみ返す"""
    registry = _load_registry()
    published_ids = set(registry.keys())
    return [s for s in _all_products() if s.get("product_id") in published_ids]


def find_bundle_candidates(published_only: bool = False) -> list:
    """
    BUNDLE_BLUEPRINTS に基づいてバンドル候補を返す。
    Returns: list of {blueprint_name, products, suggested_price, discount_pct}
    """
    products = _get_published_products() if published_only else _all_products()
    # 既にバンドルのものは除外
    products = [p for p in products if not p.get("product_id", "").startswith("bundle_")]

    candidates = []
    for (bundle_name, types, min_count, max_count) in BUNDLE_BLUEPRINTS:
        matching = [p for p in products if p.get("product_type") in types]
        if len(matching) < min_count:
            continue
        # スコア順に並べてmax_countまで取る
        matching.sort(key=lambda p: p.get("trend_score", 0), reverse=True)
        selected = matching[:max_count]

        individual_total = sum(p.get("_usd_price", p.get("price_usd", p.get("price", 15))) for p in selected)
        bundle_price = round(individual_total * 0.65, 0)  # 35% off
        bundle_price = max(bundle_price, 19)               # 最低 $19
        bundle_price = min(bundle_price, 79)               # 最高 $79

        candidates.append({
            "bundle_name":      bundle_name,
            "types":            types,
            "products":         selected,
            "product_count":    len(selected),
            "individual_total": individual_total,
            "bundle_price":     int(bundle_price),
            "savings":          int(individual_total - bundle_price),
            "discount_pct":     round((1 - bundle_price / max(individual_total, 1)) * 100),
        })

    return candidates


def create_bundle(candidate: dict) -> dict:
    """
    バンドル商品ディレクトリを作成し spec.json + ZIP + gumroad_page.md を生成する。
    Returns: spec dict
    """
    bundle_id  = f"bundle_{int(time.time())}"
    bundle_dir = PRODUCTS_DIR / bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    name       = candidate["bundle_name"]
    price      = candidate["bundle_price"]
    products   = candidate["products"]
    savings    = candidate["savings"]
    disc_pct   = candidate["discount_pct"]

    spec = {
        "product_id":   bundle_id,
        "name":         name,
        "category":     "Bundle",
        "subcategory":  "Bundle Pack",
        "product_type": "bundle",
        "price_usd":    price,
        "trend_score":  90,
        "is_bundle":    True,
        "bundle_items": [p.get("product_id") for p in products],
        "created_at":   datetime.now().isoformat(),
    }

    with open(bundle_dir / "spec.json", "w") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    # ── ZIP: 各商品の ZIP を1つのアーカイブに収録 ────────────────────────
    bundle_zip = bundle_dir / f"{bundle_id}.zip"
    with zipfile.ZipFile(bundle_zip, "w", zipfile.ZIP_DEFLATED) as master_zip:
        for p in products:
            pdir = p.get("_dir") or PRODUCTS_DIR / p["product_id"]
            folder_name = p["name"][:40].strip().replace(" ", "_").replace("/", "-")
            # 個別 ZIP があれば収録
            zips = list(pdir.glob("*.zip")) if pdir.exists() else []
            if zips:
                with open(zips[0], "rb") as zf:
                    master_zip.writestr(f"{folder_name}/{zips[0].name}", zf.read())
            else:
                # ZIP なければ content.md を収録
                cm = pdir / "content.md"
                if cm.exists():
                    master_zip.writestr(f"{folder_name}/content.md", cm.read_text(encoding="utf-8"))

        # README.md をバンドルに追加
        readme = _build_readme(name, products, price, savings, disc_pct)
        master_zip.writestr("README.md", readme)

    # ── Gumroad 販売ページ ─────────────────────────────────────────────────
    page = _build_gumroad_page(name, products, price, savings, disc_pct)
    (bundle_dir / "gumroad_page.md").write_text(page, encoding="utf-8")

    print(f"[Bundle] 作成完了: {name} (${price}, {len(products)}商品 ZIP)")
    return spec


def _build_readme(name, products, price, savings, disc_pct) -> str:
    lines = [
        f"# {name}",
        "",
        f"**{len(products)} products bundled together — ${price} (save ${savings}, {disc_pct}% off)**",
        "",
        "## What's Included",
        "",
    ]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. **{p['name']}** (normally ${p.get('_usd_price', p.get('price_usd', p.get('price', 15)))})")
        lines.append(f"   Type: {p.get('product_type','').replace('_',' ')}")
        lines.append("")

    lines += [
        "## How to Use",
        "",
        "Each product is in its own folder inside this ZIP.",
        "Open each folder to find the files — ZIPs, spreadsheets, guides, etc.",
        "",
        "For Notion templates: import the CSV files via Notion's Import feature.",
        "For HTML tools: double-click the .html file to open in your browser.",
        "For spreadsheets: open the .xlsx file in Excel or Google Sheets.",
        "",
        "*© AETERNA Holdings*",
    ]
    return "\n".join(lines)


def _build_gumroad_page(name, products, price, savings, disc_pct) -> str:
    product_list = "\n".join(
        f"- **{p['name']}** (${p.get('_usd_price', p.get('price_usd', p.get('price', 15)))} individually)"
        for p in products
    )
    individual_total = sum(p.get("_usd_price", p.get("price_usd", p.get("price", 15))) for p in products)

    return f"""## {name}

### Get {len(products)} premium products for the price of {max(1, len(products)-1)}

Buying everything individually would cost you **${individual_total}**.
Grab this bundle today for just **${price}** — that's **${savings} off** ({disc_pct}% discount).

### What's in the Bundle

{product_list}

### Why This Bundle?

These products work together. Each one builds on the others.
You get the complete picture, not just one piece of the puzzle.

### Who Is This For?

- You've been wanting to buy a few of these anyway
- You want maximum value for minimum spend
- You're serious about leveling up fast

### One-time purchase. Instant download. Keep forever.

**${price}** — no subscription, no recurring fees.

*30-day money-back guarantee. If you're not happy, you get a full refund.*
"""


def auto_create_bundles(published_only: bool = False, max_bundles: int = 3) -> list:
    """
    バンドル候補を見つけて自動作成する。heartbeat / main から呼ぶ。
    Returns: list of created bundle specs
    """
    # 既存バンドル名を取得（重複作成防止）
    existing_bundle_names = set()
    for d in PRODUCTS_DIR.iterdir():
        sf = d / "spec.json"
        if sf.exists():
            s = json.loads(sf.read_text())
            if s.get("is_bundle"):
                existing_bundle_names.add(s["name"])

    candidates = find_bundle_candidates(published_only)
    created = []
    for c in candidates[:max_bundles]:
        if c["bundle_name"] in existing_bundle_names:
            continue
        spec = create_bundle(c)
        created.append(spec)

    return created


if __name__ == "__main__":
    print("=== Bundle Creator ===")
    candidates = find_bundle_candidates()
    print(f"バンドル候補: {len(candidates)}件")
    for c in candidates:
        print(f"  {c['bundle_name']}: {c['product_count']}商品, ${c['bundle_price']} ({c['discount_pct']}% off)")

    if candidates:
        print("\n最初の候補を作成...")
        spec = create_bundle(candidates[0])
        print(f"作成完了: {spec['name']} (${spec['price_usd']})")
