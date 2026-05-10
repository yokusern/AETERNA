from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from analyst.performance_report import PerformanceReport
from publisher.automation import PublisherAutomation
from publisher.wp_client import WordPressClient, sample_post_from_env
from researcher.market_analyzer import MarketAnalyzer


def load_config(config_path: str | Path) -> dict[str, Any]:
    return yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}


def run_flow(config_path: str | Path) -> list[dict[str, Any]]:
    config = load_config(config_path)
    flow = config.get("organization_flow", {})
    research_path = Path(flow.get("researcher_output", "data/research/latest_trends.json"))
    report_path = Path(flow.get("analyst_report_output", "data/reports/weekly_report.md"))
    instructions_path = Path(flow.get("analyst_instruction_output", "data/instructions/rewrite_instructions.json"))

    MarketAnalyzer(config).write_json(research_path)
    wp = WordPressClient.from_env(config_path)
    publisher = PublisherAutomation(config, wp)
    publish_results = publisher.publish_from_research(research_path)
    PerformanceReport(config).write_outputs(research_path, report_path, instructions_path)
    rewrite_results = publisher.apply_rewrite_instructions(instructions_path)

    return [
        {"step": "researcher", "output": str(research_path)},
        {"step": "engineer_publish", "results": publish_results},
        {"step": "analyst", "report": str(report_path), "instructions": str(instructions_path)},
        {"step": "engineer_rewrite", "results": rewrite_results},
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project GearMaster autonomous organization flow")
    parser.add_argument("--config", default="config/config.yml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Research -> publish -> analyze -> rewrite trigger")
    sub.add_parser("research", help="Run Researcher only")
    sub.add_parser("wp-test", help="Test WordPress connection")
    sub.add_parser("wp-sample", help="Create simple sample post")
    sub.add_parser("report", help="Generate Analyst report and rewrite instructions")
    return parser


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    config = load_config(args.config)
    flow = config.get("organization_flow", {})

    if args.command == "run":
        result = run_flow(args.config)
    elif args.command == "research":
        path = MarketAnalyzer(config).write_json(flow.get("researcher_output", "data/research/latest_trends.json"))
        result = [{"output": str(path)}]
    elif args.command == "wp-test":
        result = [WordPressClient.from_env(args.config).test_connection()]
    elif args.command == "wp-sample":
        client = WordPressClient.from_env(args.config)
        result = [client.create_post(sample_post_from_env(args.config))]
    elif args.command == "report":
        report, instructions = PerformanceReport(config).write_outputs(
            flow.get("researcher_output", "data/research/latest_trends.json"),
            flow.get("analyst_report_output", "data/reports/weekly_report.md"),
            flow.get("analyst_instruction_output", "data/instructions/rewrite_instructions.json"),
        )
        result = [{"report": str(report), "instructions": str(instructions)}]

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
