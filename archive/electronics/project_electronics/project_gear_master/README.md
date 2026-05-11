# Project GearMaster

電子機器に限定した、自律型アフィリエイト組織フローです。

このプロジェクトでは、4つのロールがJSONとMarkdownを介して連携します。

- **Researcher**: 市場分析、最新ガジェット、Amazon系セールシグナルを解析し、EngineerへJSONで報告
- **Engineer / Publisher**: ResearcherのJSONを元にWordPress REST APIで記事を下書きまたは公開し、アフィリエイトリンクを動的埋め込み
- **Analyst**: Search Consoleや収益データの代替データを集計し、管理者向けレポートとEngineer向け改善指示を生成
- **Administrator**: `data/reports/` の週次レポートを確認し、経営判断を下す

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

`.env` の初期値は `WP_DRY_RUN=true` です。この状態ではWordPressへ送信せず、投稿payloadを `data/wp_payloads/` に保存します。

## WordPress接続テスト

```bash
gear-wp --test-connection
```

## 簡単な記事投稿テスト

```bash
gear-wp --post-sample
```

下書き/公開は `.env` で切り替えます。

```env
WP_POST_STATUS=draft
# WP_POST_STATUS=publish
```

本番接続する場合:

```env
WP_DRY_RUN=false
WP_BASE_URL=https://your-wordpress.example
WP_USERNAME=your-user
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

## 自律フロー

```bash
gear-master run
```

実行順:

1. `src/researcher/market_analyzer.py` が `data/research/latest_trends.json` を生成
2. `src/publisher/wp_client.py` と `src/publisher/automation.py` がWordPress投稿payloadを生成または投稿
3. `src/analyst/performance_report.py` が `data/reports/weekly_report.md` と `data/instructions/rewrite_instructions.json` を生成
4. Engineerが改善指示JSONを読み、既存記事のタイトルやメタ情報更新を実行

## 主要ファイル

- `config/config.yml`: 各ロール、対象市場、多言語、電子機器カテゴリ、出力先の設定
- `src/researcher/market_analyzer.py`: トレンド取得とJSON出力
- `src/publisher/wp_client.py`: WordPress REST API投稿・更新コア
- `src/publisher/automation.py`: Researcher/Analystの出力をEngineerが実行する自動化層
- `src/analyst/performance_report.py`: 管理者向けレポートとEngineer向け改善指示
- `src/orchestrator/cli.py`: 組織フロー全体のCLI

## 世界展開の拡張点

`config/config.yml` の `supported_locales` と `researcher.market` を増やすことで、英語圏や海外Amazon API連携へ拡張できます。現時点の実装は `ja-JP` と `en-US` を想定したデータ構造です。
