from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RewriteInstruction:
    post_id: int | None
    slug: str
    title: str
    reason: str
    new_title: str
    meta_description: str
    priority: int


class PerformanceReport:
    """Analyst role: generate admin report and improvement instructions for Engineer."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        analyst = config.get("analyst", {})
        self.ctr_threshold = float(analyst.get("rewrite_threshold_ctr", 0.035))
        self.revenue_threshold = int(analyst.get("rewrite_threshold_revenue_yen", 500))

    def analyze(self, trend_json_path: str | Path, performance_json_path: str | Path | None = None) -> tuple[str, list[RewriteInstruction]]:
        trends = json.loads(Path(trend_json_path).read_text(encoding="utf-8"))
        performance = self._load_performance(performance_json_path, trends)
        instructions = self._instructions(performance)
        report = self._report_markdown(trends, performance, instructions)
        return report, instructions

    def write_outputs(
        self,
        trend_json_path: str | Path,
        report_path: str | Path,
        instruction_path: str | Path,
        performance_json_path: str | Path | None = None,
    ) -> tuple[Path, Path]:
        report, instructions = self.analyze(trend_json_path, performance_json_path)
        report_out = Path(report_path)
        instruction_out = Path(instruction_path)
        report_out.parent.mkdir(parents=True, exist_ok=True)
        instruction_out.parent.mkdir(parents=True, exist_ok=True)
        report_out.write_text(report, encoding="utf-8")
        instruction_out.write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "generated_at": datetime.now(UTC).isoformat(),
                    "role": "analyst",
                    "handoff_to": "engineer",
                    "instructions": [asdict(item) for item in instructions],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return report_out, instruction_out

    def _load_performance(self, performance_json_path: str | Path | None, trends: dict[str, Any]) -> list[dict[str, Any]]:
        if performance_json_path and Path(performance_json_path).exists():
            return json.loads(Path(performance_json_path).read_text(encoding="utf-8")).get("posts", [])

        posts = []
        for index, signal in enumerate(trends.get("signals", []), start=1):
            score = int(signal["recommendation_score"])
            views = 300 + score * 12
            clicks = max(5, round(views * (0.025 + (score % 12) / 1000)))
            revenue = clicks * max(20, round(signal["base_price_yen"] * 0.0008))
            posts.append(
                {
                    "post_id": None,
                    "slug": self._slug(signal["title"]),
                    "title": signal["title"],
                    "views": views,
                    "clicks": clicks,
                    "ctr": round(clicks / views, 4),
                    "revenue_yen": revenue,
                    "rank": index,
                }
            )
        return posts

    def _instructions(self, performance: list[dict[str, Any]]) -> list[RewriteInstruction]:
        instructions: list[RewriteInstruction] = []
        for item in performance:
            ctr = float(item.get("ctr", 0))
            revenue = int(item.get("revenue_yen", 0))
            if ctr < self.ctr_threshold or revenue < self.revenue_threshold:
                title = item.get("title", "電子機器レビュー")
                instructions.append(
                    RewriteInstruction(
                        post_id=item.get("post_id"),
                        slug=item.get("slug", self._slug(title)),
                        title=title,
                        reason=f"CTR={ctr:.2%}, revenue={revenue}円。導入文とメタ情報の改善が必要。",
                        new_title=f"{title}: 失敗しない選び方と価格比較",
                        meta_description=f"{title}を電子機器専門の視点で比較。価格、用途、アフィリエイト導線を見直しました。",
                        priority=90 if ctr < self.ctr_threshold else 70,
                    )
                )
        return sorted(instructions, key=lambda item: item.priority, reverse=True)

    def _report_markdown(self, trends: dict[str, Any], performance: list[dict[str, Any]], instructions: list[RewriteInstruction]) -> str:
        lines = [
            f"# {self.config.get('analyst', {}).get('report_title', 'Project GearMaster Weekly Report')}",
            "",
            f"- Generated: {datetime.now(UTC).isoformat()}",
            "- Scope: electronics-only affiliate operation",
            "",
            "## Research Signals",
        ]
        for signal in trends.get("signals", []):
            lines.append(f"- {signal['title']} ({signal['category']}): score={signal['recommendation_score']}, market={signal['market']}")
        lines.extend(["", "## Performance"])
        for item in performance:
            lines.append(f"- {item['title']}: views={item['views']}, clicks={item['clicks']}, ctr={item['ctr']:.2%}, revenue={item['revenue_yen']}円")
        lines.extend(["", "## Engineer Instructions"])
        if instructions:
            for instruction in instructions:
                lines.append(f"- priority={instruction.priority}: {instruction.slug} -> {instruction.reason}")
        else:
            lines.append("- リライト不要。高スコア記事の横展開を継続。")
        return "\n".join(lines) + "\n"

    def _slug(self, value: str) -> str:
        return value.lower().replace(" ", "-").replace("　", "-")


def load_config(config_path: str | Path = "config/config.yml") -> dict[str, Any]:
    return yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyst performance report")
    parser.add_argument("--config", default="config/config.yml")
    parser.add_argument("--trends", default=None)
    parser.add_argument("--report", default=None)
    parser.add_argument("--instructions", default=None)
    parser.add_argument("--performance-json", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    flow = config.get("organization_flow", {})
    trends = args.trends or flow.get("researcher_output", "data/research/latest_trends.json")
    report = args.report or flow.get("analyst_report_output", "data/reports/weekly_report.md")
    instructions = args.instructions or flow.get("analyst_instruction_output", "data/instructions/rewrite_instructions.json")
    report_path, instruction_path = PerformanceReport(config).write_outputs(trends, report, instructions, args.performance_json)
    print(report_path)
    print(instruction_path)


if __name__ == "__main__":
    main()
