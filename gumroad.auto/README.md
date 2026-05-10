# AETERNA Holdings - 第四事業部: gumroad.auto

**目的**: デジタル資産（SDK、テンプレート、ガイド）の自動生成とGumroadでの販売による収益最大化。

## 組織構造（エージェント）

### 1. 市場調査エージェント (Market Researcher)
- **ファイル**: `system/scripts/market_researcher.py`
- **役割**: Gumroad市場をスキャンし、需要が高く競合が少ないニッチを特定。製品仕様書（Spec）を生成。

### 2. エンジニアエージェント (Engineer)
- **ファイル**: `system/scripts/engineer.py`
- **役割**: 仕様書に基づき、コード(SDK)やドキュメント(Guide)を自動構築。

### 3. 分析エージェント (Sales Analyst)
- **ファイル**: `system/scripts/sales_analyst.py`
- **役割**: 販売データを分析し、収益最大化のための改善提案（価格調整、露出強化など）を行う。

## 運用サイクル

1. **GitHub Actions**: 毎日 21:30 JST に `master_autopilot.py` を実行。
2. **自律サイクル**: 調査 → 構築 → 分析 のサイクルを完全自動で回す。
3. **帝国報告**: 生成されたレポートは `system/reports` に保存され、統合分析官（Global Analyst）によって集計される。

## 憲法準拠
本事業部は「AETERNA_EMPIRE_CONSTITUTION.md」の4大原則を厳守し、MacBook 1台で完結する完全自律収益化エンジンとして機能する。
