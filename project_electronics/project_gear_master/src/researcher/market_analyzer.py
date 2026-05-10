from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import google.generativeai as genai
import yaml


@dataclass(frozen=True)
class TrendSignal:
    locale: str
    market: str
    category: str
    title: str
    tags: list[str]
    base_price_yen: int
    demand_score: int
    trend_score: int
    sale_score: int
    affiliate_priority: str
    recommendation_score: int
    summary: str


class MarketAnalyzer:
    """Researcher role: analyze electronics-only trend data and output JSON for Engineer."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.allowed_categories = set(config.get("system", {}).get("allowed_categories", []))
        self.locale = config.get("system", {}).get("locale_default", "ja-JP")
        self.market = config.get("researcher", {}).get("market", "JP")

    def analyze(self) -> list[TrendSignal]:
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                return self._analyze_with_gemini(api_key)
            except Exception as e:
                print(f"Gemini API error, falling back to local analysis: {e}")
        
        return self._analyze_local()

    def _analyze_with_gemini(self, api_key: str) -> list[TrendSignal]:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        seeds = self.config.get("researcher", {}).get("product_seed", [])
        prompt = f"""
        あなたは一流のガジェットレビュアー兼ITコンサルタントです。
        以下の電子機器リストを分析し、{self.market}市場（{self.locale}）のエンジニアが「今すぐ導入すべき理由」を特定してください。

        【分析要件】
        1. trend_score (0-100): 市場の注目度・新技術の採用率
        2. sale_score (0-100): 過去の価格推移に対する現在のお得度
        3. recommendation_score (0-100): 業務効率化への寄与度
        4. summary: エンジニアの課題（技術的負債や疲労）をどう解決するか、専門用語を交えて具体的に記述

        対象リスト: {json.dumps(seeds, ensure_ascii=False)}
        
        【出力形式】
        以下のキーを持つ純粋なJSONリストのみを返してください:
        [{"title": "...", "category": "...", "trend_score": 0, "sale_score": 0, "recommendation_score": 0, "summary": "...", "tags": ["...", "..."]}]
        """
        
        response = model.generate_content(prompt)
        raw_text = response.text.strip().replace("```json", "").replace("```", "")
        ai_data = json.loads(raw_text)
        
        signals = [
            TrendSignal(
                locale=self.locale,
                market=self.market,
                category=item["category"],
                title=item["title"],
                tags=item.get("tags", ["electronics"]),
                base_price_yen=0, # 本来はAPI連携等で取得
                demand_score=item.get("recommendation_score", 50),
                trend_score=item.get("trend_score", 50),
                sale_score=item.get("sale_score", 50),
                affiliate_priority="amazon",
                recommendation_score=item.get("recommendation_score", 50),
                summary=item.get("summary", ""),
            ) for item in ai_data
        ]
        return sorted(signals, key=lambda s: s.recommendation_score, reverse=True)

    def _analyze_local(self) -> list[TrendSignal]:
        signals: list[TrendSignal] = []
        for item in self.config.get("researcher", {}).get("product_seed", []):
            if item.get("category") not in self.allowed_categories:
                continue
            trend_score = self._stable_score(item["title"], "trend", 45, 96)
            sale_score = self._stable_score(item["title"], "sale", 30, 92)
            demand_score = int(item.get("demand_score", 50))
            recommendation = round(demand_score * 0.42 + trend_score * 0.34 + sale_score * 0.24)
            signals.append(
                TrendSignal(
                    locale=self.locale,
                    market=self.market,
                    category=item["category"],
                    title=item["title"],
                    tags=list(item.get("tags", [])),
                    base_price_yen=int(item.get("base_price_yen", 0)),
                    demand_score=demand_score,
                    trend_score=trend_score,
                    sale_score=sale_score,
                    affiliate_priority=item.get("affiliate_priority", "amazon"),
                    recommendation_score=recommendation,
                    summary=self._summary(item["title"], recommendation),
                )
            )
        return sorted(signals, key=lambda signal: signal.recommendation_score, reverse=True)

    def write_json(self, output_path: str | Path) -> Path:
        signals = self.analyze()
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0",
            "generated_at": datetime.now(UTC).isoformat(),
            "role": "researcher",
            "handoff_to": "engineer",
            "electronics_only": True,
            "signals": [asdict(signal) for signal in signals],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def _stable_score(self, title: str, salt: str, low: int, high: int) -> int:
        seed = f"{title}:{salt}:{datetime.now(UTC).date().isoformat()}"
        value = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:4], 16)
        return low + value % (high - low + 1)

    def _summary(self, title: str, score: int) -> str:
        if score >= 82:
            return f"{title}は今週の優先投稿候補。価格比較と用途別訴求を強める。"
        if score >= 68:
            return f"{title}は比較記事向き。セール待ち読者に刺さる構成にする。"
        return f"{title}は保留候補。競合製品と価格推移を追加調査する。"


def load_config(config_path: str | Path = "config/config.yml") -> dict[str, Any]:
    path = Path(config_path)
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Researcher market analyzer")
    parser.add_argument("--config", default="config/config.yml")
    parser.add_argument("--output", default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    output = args.output or config.get("organization_flow", {}).get("researcher_output", "data/research/latest_trends.json")
    path = MarketAnalyzer(config).write_json(output)
    print(path)


if __name__ == "__main__":
    main()
