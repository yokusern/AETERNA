# 副業支援ツール × WordPress × Gumroad 完全自動収益化システム

> **目標：** Claude Codeでシステムを1度構築したら、以後は何も触らずに記事投稿・集客・販売が自動で回り続ける状態を作る。

---

## プロジェクト概要

| 項目 | 内容 |
|------|------|
| 収益モデル | SEOブログ流入 → Gumroad商品購入 |
| ジャンル | 副業支援ツール・テンプレート販売 |
| 基盤 | WordPress（Xserver）+ Gumroad + Claude API |
| 自動化 | GitHub Actions（毎日自動実行） |
| 想定月収 | 3ヶ月後：1〜3万円 / 12ヶ月後：20〜50万円 |

---

## 収益の流れ

```
Claude API（記事自動生成）
        ↓ GitHub Actions（毎朝10時）
WordPress（SEO記事を毎日1本公開）
        ↓ Google検索流入
読者がGumroadリンクをクリック
        ↓
Gumroad商品購入（1,980〜9,800円）
        ↓
収益（Gumroadが自動で振込）
```

**自分がやること：初期構築のみ。以後ゼロ操作。**

---

## ディレクトリ構成

```
affiliate-auto-system/
├── .github/
│   └── workflows/
│       └── daily_post.yml        # GitHub Actions 定期実行
├── src/
│   ├── generate.py               # Claude APIで記事生成
│   ├── post.py                   # WordPressへ自動投稿
│   ├── keywords.py               # キーワード管理
│   └── notify.py                 # Slack通知（任意）
├── keywords/
│   └── list.txt                  # 攻めるキーワード一覧
├── products/
│   └── gumroad_links.json        # Gumroad商品URL一覧
├── logs/
│   └── .gitkeep
├── requirements.txt
├── .env.example
└── README.md
```

---

## Phase 1：インフラ構築（1〜2日）

### 1-1. サーバー・ドメイン取得

```
1. Xserver（https://www.xserver.ne.jp/）でサーバー契約
   - スタンダードプラン（月1,100円〜）
   - 独自ドメインを同時取得（例：fukugyo-tool.com）

2. WordPressをXserverの管理画面から1クリックインストール
   - サーバーパネル → WordPress簡単インストール

3. WordPressにプラグインを導入
   - SEO: Yoast SEO または Rank Math
   - セキュリティ: Wordfence
   - キャッシュ: W3 Total Cache
```

### 1-2. WordPress REST API の設定

```
1. WordPress管理画面にログイン
2. ユーザー → プロフィール → 「アプリケーションパスワード」を生成
   - 名前：「auto-post」など任意
   - 生成されたパスワードをメモ（後でGitHub Secretsに登録）
3. パーマリンク設定 → 「投稿名」に変更して保存
```

### 1-3. Gumroadアカウント作成・商品登録

```
1. https://gumroad.com でアカウント作成
2. 最初の商品を作成（例：「副業自動化テンプレート集」）
   - 価格：2,980円〜
   - ファイル：PDF or Notion テンプレート
   - 商品URLをメモ（例：https://gumroad.com/l/xxxxx）
3. 銀行口座を登録（Wiseが国際送金対応で便利）
```

### 1-4. Claude API キー取得

```
1. https://console.anthropic.com にアクセス
2. API Keys → Create Key
3. 生成されたキーをメモ
4. 請求：記事1本あたり約0.5〜1円（月30本で30円程度）
```

---

## Phase 2：コード実装（Claude Codeで一括構築）

> Claude Codeを開いて、以下のプロンプトをそのまま貼り付けるだけで全ファイルが生成されます。

### Claude Code 投入プロンプト

```
以下の仕様でPythonプロジェクトを全ファイル作成してください。

【目的】
Claude APIで副業・お金系SEO記事を自動生成し、WordPress REST APIで毎日自動投稿する。
記事末尾にGumroad商品リンクを自然な形で挿入してアフィリエイト収益を得る。

【ファイル一覧と仕様】

1. src/keywords.py
   - keywords/list.txtからキーワードを読み込む
   - 今日の日付をシードにして毎日別のキーワードを返す関数

2. src/generate.py
   - anthropic ライブラリを使用
   - モデル: claude-sonnet-4-20250514
   - max_tokens: 4000
   - キーワードを受け取り、以下の記事を生成する：
     * 文字数：3000字以上
     * HTML形式（WordPressに貼れる形）
     * H2/H3見出しを使った構成
     * 副業・AI活用・お金の悩みに寄り添うトーン
     * 最後のセクションに「おすすめツール」としてGumroadリンクを自然に挿入
     * レスポンスの1行目は「TITLE:」で始まるタイトル行
   - 環境変数CLAUDE_API_KEYを使用

3. src/post.py
   - requests ライブラリを使用
   - WordPress REST API（/wp-json/wp/v2/posts）でPOST
   - 環境変数 WP_URL, WP_USER, WP_APP_PASSWORD を使用
   - ステータスはpublish
   - 成功/失敗をboolで返す
   - エラー時はログをlogs/error.logに記録

4. src/notify.py
   - 投稿成功時にSlack Webhookで通知（SLACK_WEBHOOK_URLが未設定なら何もしない）
   - 通知内容：記事タイトル、投稿URL、日時

5. main.py
   - 上記を統合して実行
   - keywords → generate → post → notify の順で実行
   - 実行ログをlogs/YYYY-MM-DD.logに保存

6. requirements.txt
   - anthropic, requests, python-dotenv

7. .env.example
   - 必要な環境変数をコメント付きで列挙

8. keywords/list.txt
   - 副業・AI・お金系の日本語キーワードを50個

9. products/gumroad_links.json
   - {
       "main": "https://gumroad.com/l/YOUR_PRODUCT",
       "cta_text": "今すぐ無料で試す副業自動化テンプレートはこちら"
     }

すべてのファイルを完全なコードで作成してください。
```

---

## Phase 3：GitHub Actions 設定（完全自動化の核心）

### .github/workflows/daily_post.yml

```yaml
name: 毎日自動記事投稿

on:
  schedule:
    # 毎日 01:00 UTC = 日本時間 10:00
    - cron: '0 1 * * *'
  workflow_dispatch:  # 手動実行ボタン（テスト用）

jobs:
  post-article:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v4

      - name: Python 3.11 セットアップ
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 依存パッケージインストール
        run: pip install -r requirements.txt

      - name: 記事を生成して投稿
        run: python main.py
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY }}
          WP_URL: ${{ secrets.WP_URL }}
          WP_USER: ${{ secrets.WP_USER }}
          WP_APP_PASSWORD: ${{ secrets.WP_APP_PASSWORD }}
          GUMROAD_LINK: ${{ secrets.GUMROAD_LINK }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}

      - name: ログをアーティファクトとして保存
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: logs-${{ github.run_number }}
          path: logs/
          retention-days: 30
```

### GitHub Secrets の登録手順

```
GitHubリポジトリ → Settings → Secrets and variables → Actions → New repository secret

登録するSecrets：
┌─────────────────────┬──────────────────────────────────────────┐
│ Secret名            │ 値                                       │
├─────────────────────┼──────────────────────────────────────────┤
│ CLAUDE_API_KEY      │ sk-ant-xxxxxxxxxxxx（Anthropic Console） │
│ WP_URL              │ https://yourdomain.com                   │
│ WP_USER             │ WordPressのユーザー名                    │
│ WP_APP_PASSWORD     │ WPアプリケーションパスワード             │
│ GUMROAD_LINK        │ https://gumroad.com/l/xxxxx              │
│ SLACK_WEBHOOK_URL   │ https://hooks.slack.com/... （任意）     │
└─────────────────────┴──────────────────────────────────────────┘
```

---

## Phase 4：SEO戦略（流入を最大化する）

### 攻めるキーワード戦略

```
【月間検索数1,000〜5,000の中難易度キーワードを狙う】

優先度A（単価高・競合少）
- 「副業 自動化 ツール」
- 「AI 副業 稼ぎ方 2025」
- 「ChatGPT 副業 具体的」
- 「ブログ 収益化 自動化」
- 「アフィリエイト 自動化 方法」

優先度B（集客向け）
- 「在宅ワーク おすすめ ツール」
- 「副業 初心者 何から始める」
- 「月5万 副業 現実的」
- 「ノーコード 副業 作り方」
- 「Notion テンプレート 副業」
```

### 記事構成テンプレート（Claude生成指示に組み込み済み）

```
H1: [キーワード]の完全ガイド【2025年最新版】
  H2: [キーワード]とは？初心者にわかりやすく解説
  H2: なぜ今[キーワード]が注目されているのか
  H2: 実際にやってみた結果【体験談】
    H3: ステップ1：準備するもの
    H3: ステップ2：具体的な手順
    H3: ステップ3：収益化のコツ
  H2: よくある失敗とその対処法
  H2: おすすめツール・サービス ← Gumroadリンクをここに挿入
  H2: まとめ
```

---

## Phase 5：Gumroad商品ラインナップ（Claude で自動生成可能）

### 最初に作る商品（優先度順）

| 商品名 | 価格 | 内容 | 制作時間 |
|--------|------|------|---------|
| 副業自動化テンプレート集 | 2,980円 | Notion + Excelテンプレート20枚 | 2時間 |
| ChatGPT副業プロンプト100選 | 1,980円 | PDF（Claude で生成） | 1時間 |
| アフィリエイト記事ひな形集 | 3,980円 | HTML記事テンプレート30本 | 3時間 |
| 副業自動化スクリプト集 | 9,800円 | Pythonコード一式 | 5時間 |

### 商品をClaudeで即生成するプロンプト例

```
「副業自動化テンプレート集」のPDF教材を作ってください。

構成：
- 表紙
- はじめに（なぜ自動化が必要か）
- テンプレート1：月次収益管理シート（Excelの数式込みで説明）
- テンプレート2：キーワード管理シート
- テンプレート3：記事作成チェックリスト
- テンプレート4：SNS投稿カレンダー
- テンプレート5：アフィリエイト収益トラッカー
- おわりに

全文をMarkdown形式で出力してください。
```

---

## Phase 6：モニタリング（月1回見るだけ）

### 確認すべき指標

```
【月1回だけ確認する4つの数字】

1. Google Search Console
   → 検索クリック数が先月より増えているか
   URL: https://search.google.com/search-console

2. WordPress管理画面
   → 記事が毎日投稿されているか（GitHub Actionsが動いているか確認）

3. Gumroadダッシュボード
   → 販売数・収益額
   URL: https://app.gumroad.com/dashboard

4. GitHub Actions ログ
   → エラーが出ていないか
   リポジトリ → Actions → 最新のワークフロー実行
```

### 自動アラート設定

```
GitHub Actionsが失敗した場合：
→ GitHubがメールで自動通知（デフォルト設定）

Gumroadで売れた場合：
→ Gumroadが自動でメール通知

Slackに毎日投稿レポートを送る：
→ notify.py のSlack Webhook設定で対応
```

---

## コスト試算

| 項目 | 月額コスト |
|------|-----------|
| Xserverサーバー | 1,100円 |
| ドメイン | 約100円（年1,200円÷12） |
| Claude API | 約30〜100円（記事30〜100本） |
| GitHub Actions | 無料（月2,000分まで） |
| Gumroad手数料 | 売上の10%（売れたときだけ） |
| **合計固定費** | **約1,300円/月** |

**月収5万円達成で利益率97%超。**

---

## トラブルシューティング

### よくあるエラーと対処法

```
■ GitHub Actionsが失敗する場合
→ Actions → 失敗したワークフロー → ログを確認
→ 多くはSecrets未設定が原因

■ WordPressに投稿されない場合
→ WP_APP_PASSWORDのスペースを除去して再設定
→ パーマリンク設定を「投稿名」に変更して再保存

■ Claude APIエラーが出る場合
→ console.anthropic.com でAPIキーの残高・制限を確認
→ max_tokensを3000に下げてリトライ

■ Gumroadリンクのクリック数が増えない場合
→ 記事内のCTAボタンのテキストを変更（「無料で試す」が効果的）
→ 記事の上部にもリンクを追加するようプロンプトを修正
```

---

## ロードマップ

```
Week 1-2：Phase 1-2（インフラ + コード構築）
  └→ Claude Codeでコード生成、GitHubにプッシュ、Secretsを登録

Week 3：Phase 3（GitHub Actions 動作確認）
  └→ 手動実行でテスト投稿、WordPressに記事が出ることを確認

Month 1-3：記事90本蓄積、SEO育成期
  └→ 何もしない。毎朝自動投稿されるのを待つ。

Month 4-6：検索流入が始まる
  └→ 月1回Search Consoleを見るだけ。Gumroad売上が出始める。

Month 7-12：収益加速
  └→ Gumroad商品を追加するだけで売上が増える。
```

---

## まとめ：やることリスト

- [ ] Xserverでサーバー・ドメイン取得
- [ ] WordPress設置・プラグイン導入
- [ ] WordPressアプリケーションパスワード発行
- [ ] Gumroadアカウント作成・最初の商品登録
- [ ] Claude APIキー取得
- [ ] GitHubリポジトリ作成
- [ ] **Claude Codeに上記プロンプトを投入してコード生成**
- [ ] GitHub Secretsに全キーを登録
- [ ] GitHub Actionsを手動実行してテスト
- [ ] 動作確認できたら放置

**以上で完了。あとはシステムが全部やってくれます。**
