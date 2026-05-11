p Project EM (Electronic Master) - 自律成長型収益エンジン仕様書

## 1. ビジョン
**「エンジニアの財布を支え、購入者の迷いを解決する」**
本システムは、IGNITERA副代表の知見をアルゴリズム化し、ガジェット選びに悩むエンジニアや生活必需品としての電子機器を求める人々に対し、客観的データに基づいた「正解」を提示します。同時に、最小の運用コストで最大の収益（バイト代の代替〜事業資金の創出）を自律的に生み出します。

## 2. ターゲットユーザー
- **悩めるエンジニア**: 開発効率を最大化する機材（PC、キーボード、モニター）を求めている層。
- **ガジェット愛好家**: 最新情報の鮮度とリセールバリュー（出口戦略）を重視する層。
- **一般生活者**: 失敗しない生活必需品（PC、タブレット、周辺機器）を求めている層。

## 3. システムアーキテクチャ（フルオート・ループ）

### A. リサーチ・エンジン（探知）
- **トレンド取得**: `pytrends` を活用したGoogle Trendsの解析。
- **リアルタイム情報**: Amazonタイムセール、楽天スーパーセール、新製品発表ニュースの自動スクレイピング。
- **独自指標**: 過去の中古相場データに基づく「将来のリセールバリュー予測」の算出。

### B. コンテンツ・エンジン（構築）
- **プラットフォーム**: Google Blogger（完全無料・高ドメインパワー）。
- **生成ロジック**: Gemini 1.5/2.0 Flash による「専門家トーン」の執筆。
- **必須要素**: 
    - エンジニア視点の動作負荷シミュレーション。
    - メリット・デメリットの公平な比較。
    - 「今、この瞬間に買うべきか」の判定。

### C. 改善・分析エンジン（自己進化）
- **インサイト抽出**: Google Search Console API 経由で流入キーワードと滞在時間を分析。
- **自律的リライト**: 反応の良いキーワードを元に、AIが過去記事を自動アップデートし、検索順位を維持・向上。

## 4. 収益化戦略（キャッシュフロー・ルート）
1. **ハイエンド物販（Amazon/楽天）**: 高単価PC・周辺機器（報酬: 1,000円〜3,000円/件）。
2. **高単価サービス（A8.net）**: PC買取、エンジニアスクール、Wi-Fi契約（報酬: 5,000円〜50,000円/件）。
3. **クリック型広告（忍者AdMax）**: 全サイトに配置し、アクセスを漏らさず換金。

## 5. 管理者ダッシュボード（週次経営レポート）
毎週、システムが管理者（あなた）へ以下の「異種間レポート」を提出します。

### レポート項目:
- **Performance**: PV、クリック、収益の推移グラフと表。
- **Insight**: 読者がどこで熱狂し、どこで離脱したかの言語化。
- **Action Log**: AIが自律的に行った改善内容（ボタン配置変更、リライト等）。
- **Decision**: 次の「特化サイト構築」や「案件変更」の承認依頼。

## 6. 運用・管理ガイド
- **日次タスク**: システムによる自動リサーチ・投稿（管理者操作不要）。
- **週次タスク（月曜日）**: 管理者レポートを確認し、次週の戦略を「承認」する。
- **月次タスク**: A8.net等の未確定報酬の確認と、獲得したキャッシュのIGNITERA事業への再投資。

---
*Created by Project EM Build System v1.0*
*Authorized by IGNITERA Vice Representative*

project_gear_master/
├── system/
│   ├── researcher/         # 最新トレンド・セール情報の取得
│   │   ├── resale_calc.py  # リセールバリュー計算ロジック
│   │   └── sale_checker.py # セール情報監視
│   ├── analyst/            # 週次レポート・インサイト生成
│   │   └── insight_gen.py  # 異種間データ分析
│   └── publisher/          # Bloggerへの自動投稿・リライト
├── data/
│   ├── market_prices.csv   # 中古相場データ蓄積
│   └── weekly_reports/     # あなたに届く週次レポート（.md / .html）
├── templates/              # 信頼性を担保する専門記事テンプレート
└── README.md               # 先ほど作成した仕様書

このような構成です。新しいフォルダとしてproject_gear_masterを作成してください。

## 実装済みシステム

`project_gear_master/` に、電子機器限定の自律アフィリエイト実行システムを実装済みです。

### 実行

```bash
cd project_gear_master
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
gear-master run
```

### 自動ロール

- **Researcher**: 電子機器カテゴリだけを検知し、トレンド、セール、リセールを評価
- **Affiliate Manager**: Amazon、楽天、A8 の導線を商品ごとに設計
- **Publisher**: 投稿候補記事を自動生成
- **Engineer**: 記事構造、リンク、品質ゲートを検査
- **Analyst**: PV、クリック、CVR、収益、弱点を分析
- **Strategist**: 次サイクルの成長方針を自動決定

### 生成物

- `project_gear_master/data/articles/*.md`
- `project_gear_master/data/dashboards/dashboard.html`
- `project_gear_master/data/weekly_reports/weekly_report.md`
- `project_gear_master/data/gear_master.sqlite3`
