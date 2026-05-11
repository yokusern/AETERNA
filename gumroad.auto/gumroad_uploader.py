"""
Gumroad API連携スクリプト
商品情報とファイルをGumroadに自動登録する
API Docs: https://app.gumroad.com/api
"""
import os
import sys
import json
import zipfile
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


class GumroadUploader:
    API_BASE = "https://api.gumroad.com/v2"

    def __init__(self, access_token: str = None):
        self.token = access_token or os.environ.get("GUMROAD_ACCESS_TOKEN")
        if not self.token:
            raise ValueError(
                "GUMROAD_ACCESS_TOKENが設定されていません。\n"
                "export GUMROAD_ACCESS_TOKEN=your_token"
            )

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def list_products(self) -> list:
        """登録済み商品一覧を取得する"""
        resp = requests.get(f"{self.API_BASE}/products", headers=self._headers())
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"API Error: {data}")
        return data["products"]

    def create_product(self, name: str, price_cents: int, description: str,
                       published: bool = False) -> dict:
        """新商品を作成する（ファイルなし）"""
        resp = requests.post(
            f"{self.API_BASE}/products",
            headers=self._headers(),
            data={
                "name": name,
                "price": price_cents,  # セント単位（日本円の場合は円×100 / 1 = 円をセントとして扱う）
                "description": description,
                "published": str(published).lower(),
            }
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"商品作成エラー: {data}")
        print(f"[作成] {name} (ID: {data['product']['id']})")
        return data["product"]

    def upload_file(self, product_id: str, file_path: str) -> dict:
        """商品にファイルを添付する"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        with open(path, "rb") as f:
            resp = requests.put(
                f"{self.API_BASE}/products/{product_id}/product_files",
                headers=self._headers(),
                files={"file": (path.name, f)},
            )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"ファイルアップロードエラー: {data}")
        print(f"[アップロード] {path.name} → 商品 {product_id}")
        return data

    def update_product(self, product_id: str, **kwargs) -> dict:
        """商品情報を更新する（価格変更・公開・非公開など）"""
        resp = requests.patch(
            f"{self.API_BASE}/products/{product_id}",
            headers=self._headers(),
            data=kwargs
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"更新エラー: {data}")
        return data["product"]

    def publish(self, product_id: str) -> dict:
        """商品を公開する"""
        result = self.update_product(product_id, published="true")
        print(f"[公開] 商品 {product_id} を公開しました")
        return result

    def get_sales(self, product_id: str = None, after: str = None) -> list:
        """売上データを取得する
        after: "2026-01-01" 形式の日付文字列
        """
        params = {}
        if product_id:
            params["product_id"] = product_id
        if after:
            params["after"] = after

        resp = requests.get(
            f"{self.API_BASE}/sales",
            headers=self._headers(),
            params=params
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"売上取得エラー: {data}")
        return data.get("sales", [])

    def upload_product_from_spec(self, spec_file: str, publish_after_upload: bool = False) -> dict:
        """spec.jsonから商品を自動登録する"""
        spec_path = Path(spec_file)
        with open(spec_path, encoding="utf-8") as f:
            spec = json.load(f)

        product_dir = spec_path.parent

        # 商品ページ説明文を読み込む
        page_file = product_dir / "gumroad_page.md"
        description = ""
        if page_file.exists():
            with open(page_file, encoding="utf-8") as f:
                content = f.read()
            # "## 説明文" セクションを抽出
            lines = content.split("\n")
            in_desc = False
            desc_lines = []
            for line in lines:
                if line.startswith("## 説明文"):
                    in_desc = True
                    continue
                if in_desc and line.startswith("## "):
                    break
                if in_desc:
                    desc_lines.append(line)
            description = "\n".join(desc_lines).strip("---\n").strip()

        # 価格（Gumroadは円でも"price"フィールドは整数）
        price_cents = spec.get("price_jpy", 980)

        # 商品作成
        product = self.create_product(
            name=spec["name"],
            price_cents=price_cents,
            description=description,
            published=False
        )
        product_id = product["id"]

        # ファイルの準備とアップロード
        file_format = spec.get("file_format", "").upper()
        content_files = spec.get("content_files") or ([spec.get("content_file")] if spec.get("content_file") else [])

        if file_format == "ZIP" or len(content_files) > 1:
            zip_path = product_dir / f"{spec['product_id']}.zip"
            self._create_zip(product_dir, content_files, str(zip_path))
            self.upload_file(product_id, str(zip_path))
        elif content_files:
            for cf in content_files:
                full_path = product_dir / cf
                if full_path.exists():
                    self.upload_file(product_id, str(full_path))

        # 公開
        if publish_after_upload:
            self.publish(product_id)

        # 登録情報を保存
        registry_path = Path(__file__).parent / "data" / "products" / "registry.json"
        self._update_registry(registry_path, spec, product_id)

        return product

    def _create_zip(self, base_dir: Path, file_paths: list, output_zip: str):
        """複数ファイルをZIPにまとめる"""
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel_path in file_paths:
                full_path = base_dir / rel_path
                if full_path.exists():
                    zf.write(full_path, arcname=full_path.name)
                    print(f"  ZIP追加: {full_path.name}")
        print(f"ZIP作成: {output_zip}")

    def _update_registry(self, registry_path: Path, spec: dict, product_id: str):
        """商品登録情報をregistryに記録する"""
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry = {}
        if registry_path.exists():
            with open(registry_path, encoding="utf-8") as f:
                registry = json.load(f)

        registry[spec["product_id"]] = {
            "gumroad_product_id": product_id,
            "name": spec["name"],
            "price_jpy": spec.get("price_jpy"),
            "registered_at": datetime.now().isoformat(),
        }

        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)
        print(f"Registry更新: {registry_path}")


def main():
    """CLIエントリポイント"""
    import argparse
    parser = argparse.ArgumentParser(description="Gumroad商品自動登録ツール")
    parser.add_argument("command", choices=["list", "upload", "sales"])
    parser.add_argument("--spec", help="spec.jsonのパス（uploadコマンド用）")
    parser.add_argument("--publish", action="store_true", help="アップロード後に公開する")
    args = parser.parse_args()

    uploader = GumroadUploader()

    if args.command == "list":
        products = uploader.list_products()
        print(f"\n=== 登録済み商品 ({len(products)}件) ===")
        for p in products:
            status = "公開中" if p.get("published") else "非公開"
            print(f"  [{status}] {p['name']} (¥{p['price']}) ID: {p['id']}")

    elif args.command == "upload":
        if not args.spec:
            print("--spec に spec.jsonのパスを指定してください")
            sys.exit(1)
        product = uploader.upload_product_from_spec(args.spec, publish_after_upload=args.publish)
        print(f"\n登録完了: {product['name']}")
        print(f"URL: https://app.gumroad.com/products/{product['id']}")

    elif args.command == "sales":
        sales = uploader.get_sales()
        total = sum(s.get("price", 0) for s in sales)
        print(f"\n=== 売上データ ({len(sales)}件) ===")
        print(f"合計: ¥{total:,}")
        for s in sales[-10:]:
            print(f"  {s.get('created_at', '?')} ¥{s.get('price', 0):,} - {s.get('product_name', '?')}")


if __name__ == "__main__":
    main()
