#!/usr/bin/env python3
"""
fix_and_publish_all.py
======================
全Gumroad商品の修正・公開スクリプト。

実行内容:
  1. 既存10商品: ZIPファイル添付 → カバー画像添付 → 公開
  2. ローカル未登録商品: 品質チェック → Gumroad登録 → ZIP/カバー添付 → 公開
"""
import os, json, time, zipfile, re, sys, mimetypes
from pathlib import Path
from datetime import datetime
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent / ".env")

TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN")
if not TOKEN:
    print("ERROR: GUMROAD_ACCESS_TOKEN not set"); sys.exit(1)

API          = "https://api.gumroad.com/v2"
BASE         = Path(__file__).parent
PRODUCTS_DIR = BASE / "products"
REGISTRY_FILE = BASE / "data" / "products" / "registry.json"

# ──────────────────────────────────────────────────────────────
# 既存10商品: ローカルIDとGumroad IDのマッピング
# ──────────────────────────────────────────────────────────────
EXISTING_MAP = {
    "email_templates_1778936023":    "bP-6n0lPUbaUDei2sEoA9g==",
    "notion_content_os_1778937037":  "hNg7UgAClwKGBjdEjI_mdA==",
    "content_cl_1778936021":         "g0FnlxiVb4pi85K1X12YIA==",
    "chatgpt_500_1778937036":        "0HBo1bZWlXJOh3550WyXxA==",
    "budget_tracker_1778936012":     "IbQABqBagIKlPRVrOcM-rg==",
    "budget_2026_1778937039":        "aFSW1pJTxN2ozvVbZfHkxw==",
    "biz_os_1778936028":             "1c2j5Xp8DvVbAnBZ65Wn7g==",
    "biz_launch_cl_1778936019":      "S5uhHZZsgPVxo2BnAxAmrA==",
    "ai_writing_prompts_1778937044": "uLCeEi1FUQudtoJfJyKD7A==",
    "ai_art_prompts_1778936031":     "5FeYSocxZ8xA50Mo982OzQ==",
}

# JPY価格 → USD cents のマッピング（直接換算ではなく価値ベース）
JPY_TO_USD_CENTS = {
    900:  700,    # ¥900  → $7
    1200: 900,    # ¥1200 → $9
    1400: 1000,   # ¥1400 → $10
    1700: 1200,   # ¥1700 → $12
    1900: 1400,   # ¥1900 → $14
    2200: 1500,   # ¥2200 → $15
}

SKIP_LOCAL_IDS = {
    "product_1778766236", "product_1778766898", "product_1778773900",
    "product_A", "product_B", "product_C",
    "test_integration_999", "bundle_1778936819", "bundle_1778936821",
    "product_1778774033", "product_1778774263", "product_1778767303",
}

session = requests.Session()


def h():
    return {"Authorization": f"Bearer {TOKEN}"}


def _enc(pid: str) -> str:
    return quote(pid, safe="")


def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {}


def save_registry(reg: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(reg, ensure_ascii=False, indent=2))


def has_japanese(s: str) -> bool:
    return bool(re.search(r'[぀-ヿ一-鿿]', s))


# ──────────────────────────────────────────────────────────────
# Presign file upload
# ──────────────────────────────────────────────────────────────
def upload_file_presign(product_id: str, file_path: Path) -> str | None:
    """Presignフローでファイルをアップロードし、ファイルURLを返す"""
    if not file_path.exists():
        print(f"  ⚠ ファイルなし: {file_path}")
        return None

    file_size = file_path.stat().st_size
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    print(f"  ↑ アップロード: {file_path.name} ({file_size//1024}KB)")

    # Step1: presign (フィールド名は 'filename')
    r = session.post(f"{API}/files/presign", headers=h(), data={
        "filename":  file_path.name,
        "type":      mime,
        "file_size": file_size,
    }, timeout=30)
    if r.status_code != 200:
        print(f"  ✗ presign失敗 {r.status_code}: {r.text[:200]}")
        return None
    presign_data = r.json()
    upload_id = presign_data.get("upload_id")
    key       = presign_data.get("key")
    file_url  = presign_data.get("file_url")
    parts     = presign_data.get("parts", [])

    if not upload_id or not parts:
        print(f"  ✗ presign レスポンス異常: {presign_data}")
        return None

    # Step2: S3 PUT（マルチパート; 小ファイルは1パート）
    with open(file_path, "rb") as f:
        file_data = f.read()

    etags = []
    for part in parts:
        r2 = session.put(
            part["presigned_url"],
            data=file_data,
            headers={"Content-Type": mime},
            timeout=120,
        )
        if r2.status_code not in (200, 204):
            print(f"  ✗ S3 PUT失敗 part={part['part_number']} {r2.status_code}")
            return None
        etag = r2.headers.get("ETag", "").strip('"')
        etags.append({"part_number": part["part_number"], "etag": etag})

    # Step3: complete (JSON body)
    r3 = session.post(f"{API}/files/complete", headers=h(), json={
        "upload_id": upload_id,
        "key":       key,
        "parts":     etags,
    }, timeout=30)
    if r3.status_code != 200:
        print(f"  ✗ complete失敗 {r3.status_code}: {r3.text[:200]}")
        return None

    complete_data = r3.json()
    final_url = complete_data.get("file_url") or file_url

    print(f"  ✓ アップロード完了: {final_url[:70] if final_url else '(URL未取得)'}")
    return final_url or "uploaded"


def attach_file_to_product(product_id: str, file_url: str) -> bool:
    """ファイルURLを商品に添付"""
    r = session.patch(f"{API}/products/{_enc(product_id)}", headers=h(), data={
        "files[][url]": file_url,
    }, timeout=15)
    if r.status_code == 200 and r.json().get("success"):
        print(f"  ✓ ファイル添付完了")
        return True
    print(f"  ✗ 添付失敗 {r.status_code}: {r.text[:200]}")
    return False


def upload_cover(product_id: str, cover_path: Path) -> bool:
    """
    カバー画像をGumroad APIでアップロード。
    Gumroad API v2はカバー画像のAPI設定をサポートしていないため、
    Web UIから手動で設定する必要がある。
    この関数はno-opとして残す。
    """
    if cover_path.exists():
        print(f"  ℹ カバー画像はWeb UIから手動設定が必要: {cover_path.name}")
    return False


def publish_product(product_id: str) -> bool:
    """商品を公開"""
    r = session.patch(f"{API}/products/{_enc(product_id)}", headers=h(), data={
        "published": "true",
    }, timeout=15)
    if r.status_code == 200:
        d = r.json()
        if d.get("success"):
            pub = d.get("product", {}).get("published", False)
            print(f"  ✓ 公開完了 (published={pub})")
            return True
    print(f"  ✗ 公開失敗 {r.status_code}: {r.text[:200]}")
    return False


def ensure_zip(product_dir: Path, spec: dict) -> Path | None:
    zips = sorted(product_dir.glob("*.zip"))
    if zips:
        return zips[0]
    content = product_dir / "content.md"
    if not content.exists():
        return None
    pid = spec["product_id"]
    name = spec.get("name", pid)
    slug = re.sub(r'[^\w\-]', '_', name[:40]).lower()
    zpath = product_dir / f"{pid}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(content, f"{slug}.md")
    print(f"  ZIP作成: {zpath.name}")
    return zpath


def get_description(product_dir: Path) -> str:
    for fname in ("gumroad_page.md", "content.md", "README.md"):
        f = product_dir / fname
        if f.exists():
            return f.read_text(encoding="utf-8")[:3000]
    return ""


def create_on_gumroad(spec: dict, description: str) -> dict | None:
    price_usd = spec.get("price_usd", 0)
    price_jpy = spec.get("price_jpy", 0)
    if price_usd and 0 < price_usd <= 100:
        price = int(price_usd * 100)
    elif price_jpy and 0 < price_jpy <= 9999:
        price = JPY_TO_USD_CENTS.get(price_jpy, int(price_jpy))
    else:
        return None

    r = session.post(f"{API}/products", headers=h(), data={
        "name":        spec["name"],
        "price":       price,
        "description": description,
        "published":   "false",
    }, timeout=15)
    if r.status_code == 200:
        d = r.json()
        if d.get("success"):
            return d["product"]
    print(f"  ✗ 作成失敗 {r.status_code}: {r.text[:200]}")
    return None


# ──────────────────────────────────────────────────────────────
# STEP 1: 既存10商品の修正
# ──────────────────────────────────────────────────────────────
def fix_existing_products():
    print("\n" + "="*60)
    print("STEP 1: 既存10商品の修正")
    print("="*60)

    ok = 0
    for local_id, gumroad_id in EXISTING_MAP.items():
        product_dir = PRODUCTS_DIR / local_id
        spec_file   = product_dir / "spec.json"
        if not spec_file.exists():
            print(f"\n[{local_id}] spec.json なし — スキップ")
            continue

        spec = json.loads(spec_file.read_text())
        print(f"\n[{local_id}]")
        print(f"  商品名: {spec.get('name','?')}")

        # ZIPアップロード
        zip_path = ensure_zip(product_dir, spec)
        if zip_path:
            file_url = upload_file_presign(gumroad_id, zip_path)
            if file_url and file_url != "uploaded":
                attach_file_to_product(gumroad_id, file_url)
            elif file_url == "uploaded":
                # presignフロー成功だがURLが返らない場合もある
                pass
        else:
            print(f"  ⚠ ZIPなし")

        # カバー画像
        cover = product_dir / "cover.png"
        upload_cover(gumroad_id, cover)

        # 公開
        if publish_product(gumroad_id):
            ok += 1
        time.sleep(1.5)

    print(f"\n既存商品: {ok}/{len(EXISTING_MAP)} 件公開完了")
    return ok


# ──────────────────────────────────────────────────────────────
# STEP 2: ローカル未登録商品の一括登録・公開
# ──────────────────────────────────────────────────────────────
def publish_local_products():
    print("\n" + "="*60)
    print("STEP 2: ローカル未登録商品の一括登録")
    print("="*60)

    registry = load_registry()
    registered_ids = set(registry.keys()) | set(EXISTING_MAP.keys())
    registered_names = {v.get("name","").lower() for v in registry.values()}
    # 既存10商品の名前も除外
    gumroad_names_lower = set()

    candidates = []
    for d in sorted(PRODUCTS_DIR.iterdir()):
        sf = d / "spec.json"
        if not sf.exists():
            continue
        s = json.loads(sf.read_text())
        pid = s.get("product_id", d.name)

        # スキップ条件
        if pid in registered_ids or pid in SKIP_LOCAL_IDS:
            continue
        if pid.startswith("bundle_") or pid.startswith("test_"):
            continue
        if has_japanese(s.get("name", "")):
            print(f"[SKIP 日本語] {s.get('name','?')}")
            continue
        name_lower = s.get("name", "").lower()
        if not name_lower or name_lower in registered_names:
            continue

        # 価格チェック
        price_usd = s.get("price_usd", 0)
        price_jpy = s.get("price_jpy", 0)
        if price_usd > 100 or price_jpy > 9999:
            print(f"[SKIP 価格異常] {s.get('name','?')}")
            continue
        if price_usd == 0 and price_jpy == 0:
            print(f"[SKIP 価格0] {s.get('name','?')}")
            continue

        # ZIPがなければ作れるか確認
        zips = list(d.glob("*.zip"))
        content = d / "content.md"
        if not zips and not content.exists():
            print(f"[SKIP コンテンツなし] {s.get('name','?')}")
            continue

        candidates.append((d, s))
        registered_names.add(name_lower)

    print(f"\n登録対象: {len(candidates)} 件\n")

    ok = 0
    for i, (d, spec) in enumerate(candidates, 1):
        name = spec.get("name", spec["product_id"])
        print(f"[{i}/{len(candidates)}] {name}")

        description = get_description(d)
        product = create_on_gumroad(spec, description)
        if not product:
            print(f"  [FAIL] スキップ")
            continue

        gumroad_id  = product["id"]
        gumroad_url = product.get("short_url") or f"https://app.gumroad.com/l/{product.get('custom_permalink','?')}"
        print(f"  作成: {gumroad_id}")

        # registry に保存（途中失敗に備え）
        registry[spec["product_id"]] = {
            "gumroad_product_id": gumroad_id,
            "gumroad_url":        gumroad_url,
            "name":               name,
            "price":              spec.get("price_usd", spec.get("price_jpy", 0)),
            "published":          False,
            "registered_at":      datetime.now().isoformat(),
            "pinterest_pinned":   False,
        }
        save_registry(registry)

        # ZIP添付
        zip_path = ensure_zip(d, spec)
        if zip_path:
            file_url = upload_file_presign(gumroad_id, zip_path)
            if file_url and file_url != "uploaded":
                attach_file_to_product(gumroad_id, file_url)

        # カバー
        cover = d / "cover.png"
        upload_cover(gumroad_id, cover)

        # 公開
        if publish_product(gumroad_id):
            registry[spec["product_id"]]["published"] = True
            save_registry(registry)
            ok += 1

        time.sleep(1.5)

    print(f"\n新規商品: {ok}/{len(candidates)} 件登録・公開完了")
    return ok


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"AETERNA Gumroad 全商品修正・公開スクリプト")
    print(f"開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    step1_ok = fix_existing_products()
    step2_ok = publish_local_products()

    print("\n" + "="*60)
    print(f"完了!")
    print(f"  既存商品: {step1_ok}/{len(EXISTING_MAP)} 公開")
    print(f"  新規商品: {step2_ok} 件登録・公開")
    print(f"終了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
