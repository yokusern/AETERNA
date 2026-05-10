from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
import yaml
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth


class WordPressConfigError(RuntimeError):
    pass


@dataclass(frozen=True)
class WordPressPost:
    title: str
    content: str
    excerpt: str = ""
    status: str = "draft"
    categories: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    featured_media_id: int | None = None
    slug: str | None = None
    meta: dict[str, Any] | None = None
    locale: str = "ja-JP"


class WordPressClient:
    """Small WordPress REST API client for the Engineer/Publisher role."""

    def __init__(
        self,
        base_url: str,
        username: str,
        app_password: str,
        dry_run: bool = True,
        payload_archive: Path = Path("data/wp_payloads"),
        timeout: int = 20,
    ) -> None:
        # URL末尾の / や /wp-json を自動的に除去し、二重付与を防止
        self.base_url = base_url.rstrip("/").removesuffix("/wp-json")
        self.username = username
        self.app_password = app_password
        self.dry_run = dry_run
        self.payload_archive = payload_archive
        self.timeout = timeout
        self.payload_archive.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls, config_path: str | Path | None = None) -> "WordPressClient":
        load_dotenv()
        config = _load_config(config_path)
        archive = Path(
            config.get("organization_flow", {}).get("wp_payload_archive", "data/wp_payloads")
        )
        base_url = os.getenv("WP_BASE_URL", "").strip()
        username = os.getenv("WP_USERNAME", "").strip()
        password = os.getenv("WP_APP_PASSWORD", "").strip()
        dry_run = os.getenv("WP_DRY_RUN", "true").lower() in {"1", "true", "yes", "on"}

        if not dry_run and (not base_url or not username or not password):
            raise WordPressConfigError("WP_BASE_URL, WP_USERNAME, and WP_APP_PASSWORD are required when WP_DRY_RUN=false")

        return cls(
            base_url=base_url or "https://example.com",
            username=username,
            app_password=password,
            dry_run=dry_run,
            payload_archive=archive,
        )

    def test_connection(self) -> dict[str, Any]:
        if self.dry_run:
            return {"ok": True, "mode": "dry_run", "endpoint": self._url("wp/v2/users/me")}

        response = self._request("GET", "wp/v2/users/me")
        return {
            "ok": True,
            "mode": "live",
            "user_id": response.get("id"),
            "name": response.get("name"),
            "endpoint": self._url("wp/v2/users/me"),
        }

    def create_post(self, post: WordPressPost) -> dict[str, Any]:
        payload = self._post_payload(post)
        if self.dry_run:
            res = self._archive_payload("create_post", payload)
            res["id"] = 99999  # 開発用モックID
            return res
        return self._request("POST", "wp/v2/posts", json=payload)

    def update_post(self, post_id: int, updates: dict[str, Any]) -> dict[str, Any]:
        payload = {key: value for key, value in updates.items() if value not in (None, "", [], {})}
        if self.dry_run:
            payload["id_to_update"] = post_id
            return self._archive_payload("update_post", payload)
        return self._request("POST", f"wp/v2/posts/{post_id}", json=payload)

    def ensure_term(self, taxonomy: str, name: str) -> int | str:
        if self.dry_run:
            return name
        endpoint = "wp/v2/categories" if taxonomy == "category" else "wp/v2/tags"
        existing = self._request("GET", endpoint, params={"search": name})
        for term in existing:
            if term.get("name", "").lower() == name.lower():
                return int(term["id"])
        created = self._request("POST", endpoint, json={"name": name})
        return int(created["id"])

    def build_affiliate_content(self, title: str, summary: str, links: dict[str, str]) -> str:
        link_lines = "\n".join(f'- [{label}]({url})' for label, url in links.items())
        return f"""<!-- wp:heading -->
<h2>{title}</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>{summary}</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
{link_lines}
<!-- /wp:list -->
"""

    def _post_payload(self, post: WordPressPost) -> dict[str, Any]:
        category_ids = [self.ensure_term("category", item) for item in post.categories]
        tag_ids = [self.ensure_term("tag", item) for item in post.tags]
        payload: dict[str, Any] = {
            "title": post.title,
            "content": post.content,
            "excerpt": post.excerpt,
            "status": post.status,
            "categories": category_ids,
            "tags": tag_ids,
            "meta": {"locale": post.locale, **(post.meta or {})},
        }
        if post.slug:
            payload["slug"] = post.slug
        if post.featured_media_id:
            payload["featured_media"] = post.featured_media_id
        return payload

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        response = requests.request(
            method,
            self._url(endpoint),
            auth=HTTPBasicAuth(self.username, self.app_password),
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}/wp-json/{endpoint.lstrip('/')}"

    def _archive_payload(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        index = len(list(self.payload_archive.glob(f"{action}_*.json"))) + 1
        path = self.payload_archive / f"{action}_{index:03d}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "mode": "dry_run", "action": action, "payload_path": str(path), "payload": payload}


def sample_post_from_env(config_path: str | Path | None = None) -> WordPressPost:
    load_dotenv()
    config = _load_config(config_path)
    publisher_config = config.get("publisher", {})
    status = os.getenv("WP_POST_STATUS", "draft").strip().lower()
    if status not in {"draft", "publish", "private", "pending"}:
        status = "draft"

    category = os.getenv("WP_DEFAULT_CATEGORY", publisher_config.get("default_category", "Electronics"))
    featured_media = os.getenv("WP_FEATURED_MEDIA_ID", "").strip()
    featured_media_id = int(featured_media) if featured_media.isdigit() else None

    amazon_url = _amazon_link("開発用ノートPC")
    content = WordPressClient("https://example.com", "", "", dry_run=True).build_affiliate_content(
        title="開発用ノートPC 自動投稿テスト",
        summary="Researcherの市場データを元に、EngineerがWordPress REST APIへ送信する最小プロトタイプです。",
        links={
            "Amazonで価格を見る": amazon_url,
            "楽天で比較する": _rakuten_link("開発用ノートPC"),
        },
    )
    return WordPressPost(
        title="【自動投稿テスト】開発用ノートPCの選び方",
        content=content,
        excerpt="Project GearMaster WordPress REST API prototype.",
        status=status,
        categories=(category,),
        tags=tuple(publisher_config.get("default_tags", ["electronics", "affiliate"])),
        featured_media_id=featured_media_id,
        slug="gearmaster-wp-api-test",
        meta={"source": "project-gearmaster", "role": "engineer"},
        locale=config.get("system", {}).get("locale_default", "ja-JP"),
    )


def _amazon_link(keyword: str) -> str:
    from urllib.parse import quote_plus

    url = f"https://www.amazon.co.jp/s?k={quote_plus(keyword)}"
    if tag := os.getenv("AMAZON_ASSOCIATE_ID"):
        url += f"&tag={quote_plus(tag)}"
    return url


def _rakuten_link(keyword: str) -> str:
    from urllib.parse import quote_plus

    return f"https://search.rakuten.co.jp/search/mall/{quote_plus(keyword)}/"


def _load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    load_dotenv()
    path = Path(config_path or os.getenv("GEARMASTER_CONFIG", "config/config.yml"))
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WordPress REST API prototype for Project GearMaster")
    parser.add_argument("--config", default=None, help="Path to config/config.yml")
    parser.add_argument("--test-connection", action="store_true", help="Test WordPress connection")
    parser.add_argument("--post-sample", action="store_true", help="Create a sample WordPress post")
    parser.add_argument("--rewrite-post-id", type=int, help="Update an existing WordPress post")
    parser.add_argument("--title", help="Replacement title for --rewrite-post-id")
    parser.add_argument("--meta-description", help="Replacement meta description for --rewrite-post-id")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    client = WordPressClient.from_env(args.config)
    results: list[dict[str, Any]] = []

    if args.test_connection:
        results.append(client.test_connection())
    if args.post_sample:
        results.append(client.create_post(sample_post_from_env(args.config)))
    if args.rewrite_post_id:
        updates = {
            "title": args.title,
            "meta": {"description": args.meta_description} if args.meta_description else None,
        }
        results.append(client.update_post(args.rewrite_post_id, updates))
    if not results:
        results.append(client.test_connection())

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
