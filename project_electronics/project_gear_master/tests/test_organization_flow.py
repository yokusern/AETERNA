from __future__ import annotations

import json

from analyst.performance_report import PerformanceReport
from orchestrator.cli import run_flow
from researcher.market_analyzer import MarketAnalyzer


def test_researcher_outputs_electronics_json(tmp_path):
    config = {
        "system": {"allowed_categories": ["Laptop"], "locale_default": "en-US"},
        "researcher": {
            "market": "US",
            "product_seed": [
                {
                    "category": "Laptop",
                    "title": "Developer Laptop",
                    "tags": ["laptop"],
                    "base_price_yen": 180000,
                    "demand_score": 90,
                    "affiliate_priority": "amazon",
                },
                {
                    "category": "Food",
                    "title": "Coffee",
                    "tags": ["food"],
                    "base_price_yen": 2000,
                    "demand_score": 99,
                    "affiliate_priority": "amazon",
                },
            ],
        },
    }
    output = tmp_path / "latest_trends.json"

    MarketAnalyzer(config).write_json(output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["electronics_only"] is True
    assert len(payload["signals"]) == 1
    assert payload["signals"][0]["category"] == "Laptop"
    assert payload["signals"][0]["locale"] == "en-US"


def test_analyst_writes_report_and_rewrite_instructions(tmp_path):
    trends = tmp_path / "trends.json"
    trends.write_text(
        json.dumps(
            {
                "signals": [
                    {
                        "title": "Developer Laptop",
                        "category": "Laptop",
                        "market": "US",
                        "base_price_yen": 180000,
                        "recommendation_score": 80,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    performance = tmp_path / "performance.json"
    performance.write_text(
        json.dumps(
            {
                "posts": [
                    {
                        "post_id": 101,
                        "slug": "developer-laptop",
                        "title": "Developer Laptop",
                        "views": 1000,
                        "clicks": 10,
                        "ctr": 0.01,
                        "revenue_yen": 100,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = tmp_path / "weekly_report.md"
    instructions = tmp_path / "rewrite_instructions.json"

    PerformanceReport({"analyst": {"rewrite_threshold_ctr": 0.035}}).write_outputs(trends, report, instructions, performance)

    assert "Engineer Instructions" in report.read_text(encoding="utf-8")
    payload = json.loads(instructions.read_text(encoding="utf-8"))
    assert payload["instructions"][0]["post_id"] == 101


def test_full_flow_runs_in_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("WP_DRY_RUN", "true")
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        """
system:
  locale_default: ja-JP
  allowed_categories: [Laptop]
organization_flow:
  researcher_output: data/research/latest_trends.json
  analyst_report_output: data/reports/weekly_report.md
  analyst_instruction_output: data/instructions/rewrite_instructions.json
  wp_payload_archive: data/wp_payloads
researcher:
  market: JP
  product_seed:
    - category: Laptop
      title: 開発用ノートPC
      tags: [laptop, electronics]
      base_price_yen: 180000
      demand_score: 91
      affiliate_priority: amazon
publisher:
  default_category: Electronics
  default_tags: [electronics, affiliate]
analyst:
  rewrite_threshold_ctr: 0.035
  rewrite_threshold_revenue_yen: 500
""",
        encoding="utf-8",
    )

    result = run_flow(config_path)

    assert (tmp_path / "data/research/latest_trends.json").exists()
    assert (tmp_path / "data/reports/weekly_report.md").exists()
    assert (tmp_path / "data/wp_payloads/create_post_001.json").exists()
    assert result[0]["step"] == "researcher"
