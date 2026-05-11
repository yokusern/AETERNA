from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

from .wp_client import WordPressClient, WordPressPost


class PublisherAutomation:
    """Engineer role: publish Researcher output and apply Analyst rewrite instructions."""

    def __init__(self, config: dict[str, Any], wp_client: WordPressClient) -> None:
        self.config = config
        self.wp = wp_client
        self.mapping_path = Path("data/post_mapping.json")
        self.mapping_path.parent.mkdir(parents=True, exist_ok=True)
        self.jinja_env = Environment(loader=FileSystemLoader("templates"))

    def _load_mapping(self) -> dict[str, int]:
        if not self.mapping_path.exists():
            return {}
        try:
            data = json.loads(self.mapping_path.read_text(encoding="utf-8"))
            return {str(k): int(v) for k, v in data.items()}
        except (json.JSONDecodeError, ValueError):
            return {}

    def _save_mapping(self, mapping: dict[str, int]) -> None:
        current = self._load_mapping()
        current.update(mapping)
        self.mapping_path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")

    def publish_from_research(self, research_json_path: str | Path) -> list[dict[str, Any]]:
        data = json.loads(Path(research_json_path).read_text(encoding="utf-8"))
        publisher_config = self.config.get("publisher", {})
        status = os.getenv("WP_POST_STATUS", "draft").lower()
        default_category = os.getenv("WP_DEFAULT_CATEGORY", publisher_config.get("default_category", "Electronics"))
        featured_media_id = self._featured_media_id()
        results = []
        new_mappings = {}

        for signal in data.get("signals", []):
            slug = self._slug(signal["title"])
            links = self._affiliate_links(signal)
            
            # テンプレートを使用してエンジニア品質のコンテンツを生成
            template = self.jinja_env.get_template("article.md.j2")
            content = template.render(
                title=signal["title"],
                summary=signal["summary"],
                recommendation_score=signal["recommendation_score"],
                scores=signal,
                links=links,
            )

            post = WordPressPost(
                title=f"{signal['title']}導入の技術的メリットと投資対効果【エンジニア向けレビュー】",
                content=content,
                excerpt=signal["summary"],
                status=status if status in {"draft", "publish", "private", "pending"} else "draft",
                categories=(default_category, signal["category"]),
                tags=tuple(dict.fromkeys([*publisher_config.get("default_tags", []), *signal.get("tags", [])])),
                featured_media_id=featured_media_id,
                slug=slug,
                meta={
                    "source": "researcher",
                    "recommendation_score": signal["recommendation_score"],
                    "market": signal["market"],
                },
                locale=signal.get("locale", self.config.get("system", {}).get("locale_default", "ja-JP")),
            )
            res = self.wp.create_post(post)
            if res.get("id"):
                new_mappings[slug] = int(res["id"])
            results.append(res)

        if new_mappings:
            self._save_mapping(new_mappings)
        return results

    def apply_rewrite_instructions(self, instruction_json_path: str | Path) -> list[dict[str, Any]]:
        path = Path(instruction_json_path)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        results = []
        mapping = self._load_mapping()

        for instruction in data.get("instructions", []):
            slug = instruction.get("slug")
            post_id = instruction.get("post_id") or mapping.get(slug)

            if not post_id:
                results.append(
                    {
                        "ok": False,
                        "skipped": True,
                        "reason": "post_id is missing; cannot update live WordPress post",
                        "slug": instruction.get("slug"),
                    }
                )
                continue
            results.append(
                self.wp.update_post(
                    int(post_id),
                    {
                        "title": instruction.get("new_title"),
                        "meta": {
                            "description": instruction.get("meta_description"),
                            "gearmaster_rewrite_reason": instruction.get("reason"),
                        },
                    },
                )
            )
        return results

    def _affiliate_links(self, signal: dict[str, Any]) -> dict[str, str]:
        from urllib.parse import quote_plus

        keyword = quote_plus(signal["title"])
        amazon = f"https://www.amazon.co.jp/s?k={keyword}"
        if tag := os.getenv("AMAZON_ASSOCIATE_ID"):
            amazon += f"&tag={quote_plus(tag)}"
        rakuten = f"https://search.rakuten.co.jp/search/mall/{keyword}/"
        if rakuten_id := os.getenv("RAKUTEN_AFFILIATE_ID"):
            rakuten += f"?scid=af_pc_etc&rafct=i_{quote_plus(rakuten_id)}"
        links = {"Amazon": amazon, "Rakuten": rakuten}
        if a8_id := os.getenv("A8_TRACKING_ID"):
            links["A8"] = f"https://px.a8.net/?a8mat={quote_plus(a8_id)}"
        return links

    def _article_summary(self, signal: dict[str, Any]) -> str:
        return (
            f"{signal['title']}を{signal['market']}市場向けに分析。"
            f"需要{signal['demand_score']}、トレンド{signal['trend_score']}、"
            f"セール{signal['sale_score']}を元に購入判断と比較リンクを提示します。"
        )

    def _featured_media_id(self) -> int | None:
        value = os.getenv("WP_FEATURED_MEDIA_ID", "").strip()
        return int(value) if value.isdigit() else None

    def _slug(self, value: str) -> str:
        import re
        # 英数字、ハイフンのみを許容し、日本語が含まれる場合はMD5ハッシュでユニークなSlugを生成するなどの対策が必要だが、
        # ここでは簡易的に置換のみ行う
        s = value.lower().replace(" ", "-").replace("　", "-")
        return re.sub(r"[^a-z0-9\-]", "", s).strip("-") or "product-review"


def load_config(config_path: str | Path = "config/config.yml") -> dict[str, Any]:
    return yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Engineer publisher automation")
    parser.add_argument("--config", default="config/config.yml")
    parser.add_argument("--research-json", default=None)
    parser.add_argument("--instructions-json", default=None)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--apply-rewrites", action="store_true")
    return parser


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    config = load_config(args.config)
    flow = config.get("organization_flow", {})
    automation = PublisherAutomation(config, WordPressClient.from_env(args.config))
    results = []
    if args.publish:
        results.extend(automation.publish_from_research(args.research_json or flow.get("researcher_output", "data/research/latest_trends.json")))
    if args.apply_rewrites:
        results.extend(automation.apply_rewrite_instructions(args.instructions_json or flow.get("analyst_instruction_output", "data/instructions/rewrite_instructions.json")))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
