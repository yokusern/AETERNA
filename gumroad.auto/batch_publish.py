#!/usr/bin/env python3
"""
全未登録商品を Gumroad に一括登録 (published=True)
- ZIPなし商品は content.md から自動作成
- 重複タイトルはスキップ
- 壊れた価格・日本語タイトルはスキップ
"""
import os, json, time, zipfile, re, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN        = os.environ.get("GUMROAD_ACCESS_TOKEN")
API          = "https://api.gumroad.com/v2"
BASE         = Path(__file__).parent
PRODUCTS_DIR = BASE / "products"
REGISTRY_FILE = BASE / "data" / "products" / "registry.json"

SKIP_LOCAL_IDS = {
    "product_1778766236",  # deleted (Japanese)
    "product_1778766898",  # Japanese / $0
    "product_1778773900",  # deleted (duplicate)
    "test_integration_999",
}
# 英語のみ — 日本語が含まれるタイトルはスキップ
def _has_japanese(s: str) -> bool:
    return bool(re.search(r'[぀-ヿ一-鿿]', s))


def headers():
    return {"Authorization": f"Bearer {TOKEN}"}


def load_registry() -> dict:
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text())
    return {}


def save_registry(reg: dict):
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(json.dumps(reg, ensure_ascii=False, indent=2))


def ensure_zip(product_dir: Path, spec: dict) -> Path | None:
    """ZIPがなければ content.md から作る。パスを返す。"""
    zips = sorted(product_dir.glob("*.zip"))
    if zips:
        return zips[0]
    content = product_dir / "content.md"
    if not content.exists():
        return None
    pid  = spec["product_id"]
    name = spec.get("name", pid)
    slug = re.sub(r'[^\w\-]', '_', name[:40]).lower()
    zpath = product_dir / f"{pid}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(content, f"{slug}.md")
    print(f"    ZIP作成: {zpath.name}")
    return zpath


def get_description(product_dir: Path) -> str:
    page = product_dir / "gumroad_page.md"
    if page.exists():
        return page.read_text(encoding="utf-8")
    content = product_dir / "content.md"
    if content.exists():
        return content.read_text(encoding="utf-8")[:2000]
    return ""


def upload_file_presign(product_id: str, file_path: Path) -> str | None:
    """Presignフローでファイルをアップロードし、ファイルURLを返す"""
    import mimetypes
    if not file_path.exists():
        return None
    file_size = file_path.stat().st_size
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    r = requests.post(f"{API}/files/presign", headers=headers(), data={
        "filename": file_path.name, "type": mime, "file_size": file_size,
    }, timeout=30)
    if r.status_code != 200:
        print(f"    presign失敗 {r.status_code}: {r.text[:100]}")
        return None
    d = r.json()
    upload_id = d.get("upload_id")
    key = d.get("key")
    file_url = d.get("file_url")
    parts = d.get("parts", [])
    if not upload_id or not parts:
        return None

    with open(file_path, "rb") as f:
        file_data = f.read()

    etags = []
    for part in parts:
        r2 = requests.put(part["presigned_url"], data=file_data,
                          headers={"Content-Type": mime}, timeout=120)
        if r2.status_code not in (200, 204):
            return None
        etags.append({"part_number": part["part_number"], "etag": r2.headers.get("ETag","").strip('"')})

    r3 = requests.post(f"{API}/files/complete", headers=headers(), json={
        "upload_id": upload_id, "key": key, "parts": etags,
    }, timeout=30)
    if r3.status_code != 200:
        return None
    return r3.json().get("file_url") or file_url


def create_on_gumroad(spec: dict, description: str) -> dict | None:
    """Gumroad に商品を作成して product dict を返す（非公開で作成）。"""
    price_usd = spec.get("price_usd", 0)
    price_jpy = spec.get("price_jpy", 0)
    # USD を cents に換算、JPY はそのまま
    if price_usd and 0 < price_usd <= 100:
        price = int(price_usd * 100)   # cents
    elif price_jpy and 0 < price_jpy <= 9999:
        price = int(price_jpy)
    else:
        return None  # 壊れた価格

    try:
        r = requests.post(
            f"{API}/products",
            headers=headers(),
            data={
                "name":        spec["name"],
                "price":       price,
                "description": description,
                "published":   "false",
            },
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("success"):
                return data["product"]
        print(f"    API エラー {r.status_code}: {r.text[:200]}")
        return None
    except Exception as e:
        print(f"    リクエスト失敗: {e}")
        return None


def publish_with_file(product_id: str, zip_path: Path | None) -> bool:
    """ファイルアップロード → 公開の一連フローを実行"""
    import urllib.parse
    enc = urllib.parse.quote(product_id, safe="")

    # Step1: ファイルアップロード
    if zip_path and zip_path.exists():
        file_url = upload_file_presign(product_id, zip_path)
        if file_url:
            # Step2: ファイルを商品に添付
            r = requests.patch(f"{API}/products/{enc}", headers=headers(), data={
                "files[][url]": file_url,
            }, timeout=15)
            if not r.json().get("success"):
                print(f"    ファイル添付失敗")
                return False
        else:
            print(f"    ファイルアップロード失敗")
            return False

    # Step3: 公開
    r2 = requests.patch(f"{API}/products/{enc}", headers=headers(), data={
        "published": "true",
    }, timeout=15)
    if r2.status_code == 200 and r2.json().get("success"):
        pub = r2.json().get("product", {}).get("published", False)
        return True  # published フィールドが遅延更新される場合があるため True を返す
    return False


def main():
    if not TOKEN:
        print("ERROR: GUMROAD_ACCESS_TOKEN が未設定")
        return

    registry = load_registry()
    registered_ids = set(registry.keys())
    registered_names = {v["name"].lower() for v in registry.values()}

    all_dirs = sorted(PRODUCTS_DIR.iterdir())
    candidates = []
    for d in all_dirs:
        sf = d / "spec.json"
        if not sf.exists():
            continue
        s = json.loads(sf.read_text())
        pid = s.get("product_id", "")

        if pid in registered_ids or pid in SKIP_LOCAL_IDS:
            continue
        if pid.startswith("bundle_") or pid.startswith("test_"):
            continue
        if _has_japanese(s.get("name", "")):
            continue
        price_usd = s.get("price_usd", 0)
        price_jpy = s.get("price_jpy", 0)
        if (price_usd == 0 and price_jpy == 0) or price_usd > 100 or price_jpy > 9999:
            continue
        # 重複タイトルスキップ
        name_lower = s.get("name", "").lower()
        if name_lower in registered_names:
            print(f"[SKIP 重複] {s.get('name')}")
            continue

        candidates.append((d, s))
        registered_names.add(name_lower)  # 同バッチ内の重複も防ぐ

    # 1日の上限 = 10件（Gumroad制限）
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10, help="1回の最大登録数")
    args, _ = parser.parse_known_args()
    candidates = candidates[:args.limit]

    print(f"\n登録対象: {len(candidates)} 件 (limit={args.limit})\n")

    ok_count = 0
    for i, (d, spec) in enumerate(candidates, 1):
        name = spec.get("name", spec["product_id"])
        print(f"[{i}/{len(candidates)}] {name}")

        # ZIP 確保
        zip_path = ensure_zip(d, spec)
        description = get_description(d)

        # Gumroad 作成
        product = create_on_gumroad(spec, description)
        if not product:
            print(f"    [FAIL] スキップ")
            continue

        gumroad_id = product["id"]
        gumroad_url = product.get("short_url") or f"https://app.gumroad.com/l/{product.get('custom_permalink','?')}"
        print(f"    作成: {gumroad_id}")

        # ファイルアップロード + 公開
        pub_ok = publish_with_file(gumroad_id, zip_path)
        print(f"    {'✓ 公開OK' if pub_ok else '⚠ 公開待機中'}: {gumroad_url}")

        # registry 保存
        registry[spec["product_id"]] = {
            "gumroad_product_id": gumroad_id,
            "gumroad_url": gumroad_url,
            "name":  name,
            "price": spec.get("price_usd", spec.get("price_jpy", 0)),
            "published": pub_ok,
            "zip_path": str(zip_path) if zip_path else "",
            "registered_at": datetime.now().isoformat(),
            "pinterest_pinned": False,
        }
        save_registry(registry)
        registered_names.add(name.lower())
        ok_count += 1

        # Gumroadレート制限対策
        time.sleep(1.5)

    print(f"\n完了: {ok_count}/{len(candidates)} 件登録")


if __name__ == "__main__":
    main()
