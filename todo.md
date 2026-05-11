# AETERNA Holdings - 自己進化型AI会社 構築TODO

**作成日**: 2026年5月11日
**目的**: AIエージェントだけで自律的に回り、成長し、収益化する「生きた会社」を構築する
**核心思想**: ユーザーが寝ている間にも、エージェント同士が対話し、コードを書き換え、商品を作り、売り、改善し、新しいエージェントすら生み出す

---

## 現状の正直な評価

Phase 0〜3は完了済み。5エージェント体制・商品3品・GitHub Actionsパイプラインが存在する。
しかし、今の構造には決定的な欠陥がある。

**欠陥: 今のエージェントは「人間がClaude Codeで実行してあげないと動かない」**

商品を作ったのはClaude Code。エージェントを書いたのもClaude Code。
つまり今の「会社」は、人間が手回しするオルゴールでしかない。
ここから、**人間が手を離しても永久に回り続けるエンジン**に変える。

---

## 設計思想: 「脳」を持つ会社

従来のAETERNAは「設計書の山」か「人間が回すスクリプト」だった。
新しいAETERNAは以下の構造を持つ。

```
┌─────────────────────────────────────────────────────────┐
│                    BRAIN（脳）                           │
│  ┌───────────────────────────────────────────────────┐  │
│  │ brain.py - 全ての起点                              │  │
│  │ ・現状を読む（売上、商品数、エラーログ、市場）     │  │
│  │ ・考える（LLM APIで次にやるべきことを決定）        │  │
│  │ ・実行する（必要なエージェントを呼ぶ/作る）        │  │
│  │ ・記録する（結果をログに残し、次回の判断材料に）    │  │
│  └───────────────────────────────────────────────────┘  │
│                         │                                │
│              GitHub Actions (cron)                        │
│              毎日21:00 JST 自動起動                      │
│                         │                                │
│    ┌────────┬────────┬────────┬────────┬────────┐        │
│    │商品制作│市場分析│販売管理│改善実行│増殖管理│        │
│    │Agent   │Agent   │Agent   │Agent   │Agent   │        │
│    └────────┴────────┴────────┴────────┴────────┘        │
│                         │                                │
│              ┌──────────┴──────────┐                     │
│              │   data/state.json   │                     │
│              │   会社の「記憶」     │                     │
│              └─────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

**核心: brain.pyは「何をすべきか」を自分で考える。**

人間が「商品を作れ」と言うのではない。
brainが売上データを見て「商品Aが売れていない→価格を下げるか、類似の安い商品を出すか、説明文を変えるか」を自分で判断し、実行する。

---

## TODO一覧

### Phase A: 会社の「脳」を作る

#### A-1: state.json — 会社の記憶システム

会社の全状態を1つのJSONで管理する。brainが毎回これを読み、更新する。

```json
{
  "last_run": "2026-05-11T21:00:00+09:00",
  "run_count": 47,
  "revenue": {
    "total_lifetime": 12800,
    "last_30_days": 12800,
    "last_7_days": 4200,
    "by_product": {
      "product_A": { "sales": 5, "revenue": 4900, "views": 230 },
      "product_B": { "sales": 3, "revenue": 4440, "views": 180 }
    }
  },
  "products": {
    "published": ["product_A", "product_B", "product_C"],
    "drafts": ["product_D"],
    "total": 4
  },
  "agents": {
    "active": ["brain", "builder", "analyzer", "seller", "evolver"],
    "created_by_evolver": [],
    "total": 5
  },
  "decisions_log": [
    {
      "date": "2026-05-11",
      "observation": "product_Aの売上が他より2倍高い",
      "decision": "product_Aの類似商品を2つ制作する",
      "result": "pending"
    }
  ],
  "market_insights": {
    "trending_topics": ["AI agent", "自動化", "Claude活用"],
    "last_scan": "2026-05-11"
  },
  "errors": [],
  "next_actions": []
}
```

- [ ] `data/state.json` の初期構造を定義・作成
- [ ] 読み書きユーティリティ `core/state_manager.py` を実装
- [ ] 全エージェントがstate.jsonを通じて情報共有するルールを確立

#### A-2: brain.py — 自律思考エンジン

brain.pyはGitHub Actionsで毎日自動実行される「会社のCEO AI」。
人間のCEOはDiscord通知を見るだけ。

**brain.pyの思考ループ:**

```python
def run():
    # 1. 記憶を読む
    state = load_state()
    
    # 2. 現状を把握する
    sales_data = fetch_gumroad_sales()
    market_data = scan_market_trends()
    error_log = check_system_health()
    
    # 3. LLMに「次に何をすべきか」を聞く
    prompt = f"""
    あなたはAETERNA Holdingsの自律型CEO AIです。
    以下の現状データに基づき、今日実行すべきアクションを
    最大3つ、JSON形式で出力してください。
    
    【売上データ】{sales_data}
    【市場トレンド】{market_data}
    【現在の商品数】{state['products']['total']}
    【エラー】{error_log}
    【過去の意思決定と結果】{state['decisions_log'][-10:]}
    
    アクション種別:
    - CREATE_PRODUCT: 新商品を作る（テーマ、価格、理由を含む）
    - IMPROVE_PRODUCT: 既存商品を改善する（対象、改善内容）
    - ADJUST_PRICE: 価格を変更する（対象、新価格、理由）
    - WRITE_ARTICLE: 集客記事を書く（テーマ、掲載先）
    - CREATE_AGENT: 新しいエージェントを作る（役割、理由）
    - EXPAND_BUSINESS: 新事業領域に進出する（領域、理由）
    - FIX_ERROR: システムエラーを修復する（対象、内容）
    - POST_SNS: SNS投稿を行う（内容、プラットフォーム）
    - DO_NOTHING: 今日は行動不要（理由）
    """
    
    actions = call_llm(prompt)
    
    # 4. 各アクションを実行
    for action in actions:
        execute_action(action)
    
    # 5. 結果を記録
    update_state(state, actions, results)
    
    # 6. CEOにDiscord通知
    notify_ceo(summary)
```

- [ ] `core/brain.py` を実装
  - [ ] state.json読み込み
  - [ ] Gumroad API売上データ取得
  - [ ] 市場トレンドスキャン（Webスクレイピング or API）
  - [ ] LLM思考ループ（Anthropic Claude API）
  - [ ] アクション実行ディスパッチャー
  - [ ] 結果記録・state.json更新
  - [ ] Discord通知
- [ ] エラー時の自動復旧ロジック（try/except + リトライ）
- [ ] API制限時のフォールバック（Claude → Gemini → Groq）

#### A-3: GitHub Actionsワークフローの改修

現在のdaily_pipeline.ymlを、brain.py起動に一本化する。

```yaml
# .github/workflows/brain.yml
name: AETERNA Brain - Daily Autonomous Run
on:
  schedule:
    - cron: '0 12 * * *'  # 毎日21:00 JST
  workflow_dispatch:  # 手動実行も可能

jobs:
  think-and-act:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python core/brain.py
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GUMROAD_ACCESS_TOKEN: ${{ secrets.GUMROAD_ACCESS_TOKEN }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "🧠 Brain auto-update: [date]"
```

**重要: `git-auto-commit-action`により、brainが生成したコード・商品・改善結果が自動的にリポジトリにコミットされる。ユーザーが知らない間にコードが変わっても問題ない。**

- [ ] `.github/workflows/brain.yml` を作成
- [ ] 既存のdaily_pipeline.yml、product_planning.ymlを統合・置換
- [ ] git-auto-commit-actionの設定
- [ ] 手動トリガー（workflow_dispatch）の設定

---

### Phase B: 各エージェントを「脳から呼ばれる関数」に再構成

現在のエージェントは独立したスクリプトだが、brainから統一的に呼び出せるように再構成する。

#### B-1: 商品制作エージェント（builder）の再構成

brainから `CREATE_PRODUCT` アクションが来たとき呼ばれる。

```python
# agents/builder.py
def create_product(spec):
    """
    spec = {
      "theme": "Excel業務効率化マクロ集",
      "price": 1980,
      "format": "zip",  # pdf / zip / notion
      "reason": "Excel関連の検索ボリュームが高い"
    }
    """
    # 1. LLMでコンテンツ生成
    content = generate_content(spec)
    # 2. ファイル出力（PDF/ZIP/Markdown）
    filepath = package_product(content, spec)
    # 3. spec.jsonを生成
    save_spec(spec, filepath)
    # 4. state.jsonに追加
    register_product(spec)
    return filepath
```

- [ ] `agents/builder.py` をbrain対応に再構成
- [ ] PDF生成機能の実装（reportlab or markdown→PDF）
- [ ] ZIP生成機能の実装（Pythonスクリプト集等）
- [ ] Notion用Markdown生成機能
- [ ] 商品サムネイル画像の自動生成（PIL/Pillow）

#### B-2: 市場分析エージェント（analyzer）の再構成

世の中の金銭の流通を分析し、「何が売れるか」を見つける。

```python
# agents/analyzer.py
def analyze_market():
    """
    やること:
    1. Gumroad上の売れ筋商品を分析
    2. Google Trendsのトレンドキーワードを取得
    3. X/Twitter上のバズトピックを分析
    4. 競合商品の価格帯・レビューを分析
    5. 自社商品の売上データと比較
    
    出力: 「次に作るべき商品」の提案リスト
    """
    trends = scrape_trends()
    gumroad_top = analyze_gumroad_rankings()
    own_performance = load_state()['revenue']
    
    prompt = f"""
    以下のデータから、次に制作すべきデジタル商品を3つ提案してください。
    条件: AI（Claude/ChatGPT）で制作可能、制作時間24時間以内、
    Gumroadで販売、価格¥500〜¥9,980
    
    トレンド: {trends}
    Gumroad売れ筋: {gumroad_top}
    自社実績: {own_performance}
    """
    return call_llm(prompt)
```

- [ ] `agents/analyzer.py` をbrain対応に再構成
- [ ] Gumroad売れ筋スクレイピング機能
- [ ] Google Trends API / pytrends連携
- [ ] X API連携（トレンド取得）
- [ ] 競合価格帯分析ロジック
- [ ] 「Gumroad以外にも売れる場所」を探索するロジック
  - note.com有料記事
  - BOOTH
  - Kindle Direct Publishing
  - Udemy（動画コース）
  - ココナラ（スキル販売）

#### B-3: 販売管理エージェント（seller）の再構成

- [ ] `agents/seller.py` をbrain対応に再構成
- [ ] Gumroad API連携（商品登録、価格変更、データ取得）
- [ ] 商品説明文のA/Bテスト機能（2パターン用意して交互に設定）
- [ ] 価格最適化ロジック（売上データに基づく自動価格調整）
- [ ] 複数プラットフォーム対応の基盤設計

#### B-4: 改善実行エージェント（improver）の再構成

既存商品・既存コード・既存パイプラインを改善する。

```python
# agents/improver.py
def improve(target, improvement_spec):
    """
    target: "product_A" or "agents/builder.py" or "brain.py"
    
    このエージェントは、商品だけでなく
    会社のコード自体も改善できる。
    つまり、エージェントがエージェントを改善する。
    """
    if target.startswith("product_"):
        improve_product(target, improvement_spec)
    elif target.endswith(".py"):
        improve_code(target, improvement_spec)
```

- [ ] `agents/improver.py` を実装
- [ ] 商品改善機能（説明文書き換え、内容追加）
- [ ] コード改善機能（LLMでコードを読み→改善案を出し→書き換える）
- [ ] 改善前後の差分ログ保存

---

### Phase C: エージェント増殖システム（Evolver）

**これが最も重要な機能。** エージェントが新しいエージェントを生み出す。

#### C-1: evolver.py — エージェント生成エージェント

```python
# agents/evolver.py
def create_agent(spec):
    """
    spec = {
      "name": "note_publisher",
      "role": "note.comに有料記事を自動投稿する",
      "reason": "note.comの有料記事市場が成長しているため",
      "triggers": ["CREATE_NOTE_ARTICLE"],
      "inputs": ["テーマ", "価格", "本文"],
      "outputs": ["note記事URL", "売上データ"]
    }
    """
    # 1. LLMにエージェントのPythonコードを生成させる
    code = generate_agent_code(spec)
    
    # 2. agents/ に保存
    filepath = f"agents/{spec['name']}.py"
    save_file(filepath, code)
    
    # 3. brain.pyのアクションディスパッチャーに登録
    register_in_brain(spec)
    
    # 4. state.jsonに記録
    register_agent(spec)
    
    # 5. テスト実行
    test_result = test_agent(filepath)
    
    return test_result
```

**brainが「新しい収益チャネルが必要」と判断したとき、evolverが自動的に新しいエージェントを作り、それが翌日から稼働する。**

例:
- brainが「Kindleで電子書籍を売るべき」と判断
- → evolverが `agents/kindle_publisher.py` を生成
- → 翌日からbrainが `PUBLISH_KINDLE` アクションでそれを呼ぶ
- → 人間は何もしていないのに、Kindleに本が出版される

- [ ] `agents/evolver.py` を実装
  - [ ] LLMによるPythonコード生成
  - [ ] 生成コードの構文チェック（ast.parse）
  - [ ] 生成コードのサンドボックステスト
  - [ ] brain.pyへの自動登録
  - [ ] state.jsonへの記録
- [ ] エージェント削除・無効化機能（パフォーマンスが悪いエージェントを止める）
- [ ] エージェント改良機能（既存エージェントのコードを改善する）

---

### Phase D: 収益チャネルの自動探索と拡張

brainとanalyzerが協力して、「今のAETERNAのリソースで参入できる収益チャネル」を自動的に見つけ、evolverが参入用エージェントを作る。

#### D-1: 収益チャネル探索エンジン

```python
# core/revenue_scanner.py
def scan_revenue_opportunities():
    """
    世の中のデジタル商品・サービスの金銭の流れを分析し、
    AETERNAが参入可能な領域を特定する。
    
    分析対象:
    1. Gumroad（現在の主戦場）
    2. note.com有料記事（日本市場、参入障壁低い）
    3. BOOTH（同人・デジタル商品、参入障壁低い）
    4. Kindle Direct Publishing（電子書籍、参入障壁中）
    5. Udemy/Skillshare（動画コース、参入障壁高）
    6. ココナラ（スキル販売、参入障壁低い）
    7. X/Twitter有料コンテンツ（サブスクリプション）
    8. GitHub Sponsors（OSS、参入障壁中）
    9. アフィリエイト（A8.net, もしもアフィリエイト）
    10. YouTube（広告収益、参入障壁高）
    
    AIエージェントに可能な作業:
    - テキストコンテンツ生成（記事、書籍、プロンプト集）
    - コード生成（テンプレート、スクリプト、ツール）
    - データ分析レポート作成
    - マーケティングコピー作成
    - SNS投稿自動化
    
    AIエージェントに不可能な作業（当面）:
    - 動画撮影（テキスト読み上げ動画は可能）
    - 実物の発送
    - 対面コンサルティング
    - 銀行振込等の物理的操作
    """
    
    prompt = """
    以下の収益チャネルを分析し、
    AIエージェントだけで参入可能で、
    かつ月間¥50,000以上の収益が見込めるチャネルを
    優先度順にランク付けしてください。
    
    各チャネルについて:
    - 参入難易度（低/中/高）
    - 期待月間収益
    - 必要なエージェント
    - 最初に作るべき商品/サービス
    を出力してください。
    """
    return call_llm(prompt)
```

- [ ] `core/revenue_scanner.py` を実装
- [ ] 各プラットフォームのAPI/スクレイピング基盤
- [ ] チャネル評価スコアリングロジック
- [ ] brainとの統合（月1回の収益チャネルスキャン）

#### D-2: 自動参入プロセス

brainが「note.comに参入すべき」と判断した場合の流れ:

```
1. brain: "EXPAND_BUSINESS: note.com有料記事"
2. evolver: agents/note_publisher.py を自動生成
3. builder: 最初の有料記事コンテンツを自動生成
4. note_publisher: note.com APIで記事を投稿
5. analyzer: 売上データを収集・分析
6. brain: 次回実行時に結果を評価し、継続/撤退を判断
```

- [ ] 各プラットフォームへの自動投稿エージェントのテンプレート
- [ ] 参入/撤退判断ロジック（3回の投稿で反応がなければ撤退）

---

### Phase E: 自己改善・自己進化メカニズム

#### E-1: コード自己書き換えシステム

brainが自身のコードを改善する仕組み。

```python
# agents/self_modifier.py
def review_and_improve_codebase():
    """
    1. 全エージェントのコードを読む
    2. 各エージェントのパフォーマンス（実行時間、エラー率、成果）を評価
    3. 改善が必要なコードをLLMで書き換える
    4. テストを実行
    5. テストが通ったらコミット
    """
    for agent_file in glob("agents/*.py"):
        code = read_file(agent_file)
        perf = get_agent_performance(agent_file)
        
        if perf['error_rate'] > 0.1 or perf['effectiveness'] < 0.5:
            improved = call_llm(f"""
            以下のPythonコードを改善してください。
            現在のエラー率: {perf['error_rate']}
            現在の有効性: {perf['effectiveness']}
            
            コード:
            {code}
            """)
            
            if validate_code(improved):
                write_file(agent_file, improved)
                log_change(agent_file, "auto-improvement")
```

- [ ] `agents/self_modifier.py` を実装
- [ ] コード品質チェック（ast.parse + 基本テスト）
- [ ] 変更前のバックアップ自動保存
- [ ] 危険な変更のブロック（core/brain.pyの書き換えは慎重に）
- [ ] 変更ログの自動記録

#### E-2: 学習・記憶システム

過去の成功・失敗パターンを蓄積し、判断精度を上げる。

```
data/memory/
├── successes.jsonl    # 成功した施策とその条件
├── failures.jsonl     # 失敗した施策とその条件
├── market_history.jsonl  # 市場トレンドの変遷
└── product_lifecycle.jsonl  # 各商品のライフサイクルデータ
```

- [ ] `core/memory.py` を実装
- [ ] 成功/失敗パターンの自動分類・記録
- [ ] brainのプロンプトに過去の記憶を注入する機能
- [ ] 古い記憶の自動要約・圧縮（トークン節約）

---

### Phase F: CEOへの報告・通知システム

#### F-1: Discord自動レポート

brainが毎日の実行後、CEOにDiscord通知を送る。

```
📊 AETERNA日報 (2026-05-15)
━━━━━━━━━━━━━━━━━━━━━━━
💰 売上: ¥4,200（累計¥12,800）
📦 商品数: 6個（+1 新商品「Excel自動化マクロ集」）
🤖 稼働エージェント: 7個（+2 note_publisher, booth_seller）
📈 今日の判断:
  1. product_Aの価格を¥980→¥780に調整（売上低迷のため）
  2. 新商品「Excel自動化マクロ集」を制作・公開
  3. note.comに参入（初回記事投稿完了）
⚠️ エラー: なし
━━━━━━━━━━━━━━━━━━━━━━━
次回実行: 明日21:00
```

- [ ] `core/notifier.py` を実装
- [ ] Discord Webhook連携
- [ ] 日報テンプレート
- [ ] 週次サマリー自動生成（毎週日曜）
- [ ] 緊急通知（大きなエラー、売上急変時）

---

## ディレクトリ構造（最終形）

```
AETERNA/
├── core/                          # 会社の中枢
│   ├── brain.py                   # 自律思考エンジン（会社のCEO AI）
│   ├── state_manager.py           # state.jsonの読み書き
│   ├── memory.py                  # 学習・記憶システム
│   ├── revenue_scanner.py         # 収益チャネル探索
│   ├── notifier.py                # Discord通知
│   └── llm_client.py              # LLM API呼び出し（フォールバック付き）
│
├── agents/                        # エージェント群（増殖する）
│   ├── builder.py                 # 商品制作
│   ├── analyzer.py                # 市場分析
│   ├── seller.py                  # 販売管理
│   ├── improver.py                # 改善実行
│   ├── evolver.py                 # エージェント増殖
│   ├── self_modifier.py           # 自己コード改善
│   └── ...                        # evolverが自動生成するエージェント群
│
├── data/                          # 会社の記憶
│   ├── state.json                 # 現在の会社状態
│   ├── memory/                    # 過去の学習データ
│   │   ├── successes.jsonl
│   │   ├── failures.jsonl
│   │   └── market_history.jsonl
│   ├── sales/                     # 売上データ
│   └── reports/                   # 自動生成レポート
│
├── products/                      # 商品フォルダ（自動増殖する）
│   ├── product_A/
│   ├── product_B/
│   ├── product_C/
│   └── ...                        # builderが自動生成する商品群
│
├── .github/workflows/
│   └── brain.yml                  # 毎日21:00 JSTに自動実行
│
├── requirements.txt
├── CONSTITUTION_v2.md
├── COMPANY_STRUCTURE.md
└── CLAUDE.md
```

---

## 実装優先度と所要時間

| 優先度 | タスク | 所要時間 | 依存関係 |
|--------|--------|----------|----------|
| **P0** | A-1: state.json設計 | 1時間 | なし |
| **P0** | A-2: brain.py実装 | 4時間 | A-1 |
| **P0** | A-3: brain.yml作成 | 1時間 | A-2 |
| **P1** | B-1: builder再構成 | 2時間 | A-2 |
| **P1** | B-2: analyzer再構成 | 2時間 | A-2 |
| **P1** | B-3: seller再構成 | 2時間 | A-2 |
| **P1** | B-4: improver実装 | 2時間 | A-2 |
| **P2** | C-1: evolver実装 | 3時間 | B全部 |
| **P2** | D-1: revenue_scanner | 2時間 | B-2 |
| **P3** | E-1: self_modifier | 2時間 | C-1 |
| **P3** | E-2: memory.py | 2時間 | A-2 |
| **P3** | F-1: notifier | 1時間 | A-2 |
| **P4** | D-2: 自動参入プロセス | 3時間 | D-1, C-1 |

**合計: 約27時間（P0〜P2で約19時間、P3〜P4で約8時間）**

---

## 成功の定義

### 1週間後
- [ ] brain.pyが毎日自動実行され、Discord通知が届く
- [ ] brainが自分で「次に作る商品」を決定し、builderに指示している
- [ ] state.jsonが毎日自動更新されている

### 1ヶ月後
- [ ] 商品数が10個以上に自動増殖している
- [ ] 少なくとも1つの新しい収益チャネル（note.com等）に自動参入している
- [ ] evolverが少なくとも1つの新エージェントを自動生成している
- [ ] 月間売上¥30,000以上

### 3ヶ月後
- [ ] 商品数が30個以上
- [ ] 3つ以上の収益チャネルで販売中
- [ ] エージェント数が10個以上（evolver生成含む）
- [ ] コードの自己改善が週1回以上実行されている
- [ ] 月間売上¥100,000以上
- [ ] CEOの介入がDiscord通知の確認のみ

### 6ヶ月後
- [ ] 月間売上¥300,000以上
- [ ] 完全に自律運用（CEOの介入ゼロ）
- [ ] brainの判断精度が初期より明確に向上している（記憶システムの効果）
- [ ] 少なくとも1つのエージェントが「人間には思いつかなかった」収益源を発見している

---

## Claude Codeの役割（このTODOを読んで実行すること）

Claude Codeの仕事は「この会社の初期インフラを作る大工」である。
家（会社）が建ったら、中に住むAIエージェントたちが自分で家を増改築していく。

具体的にClaude Codeがやること:
1. **core/brain.pyを書く** — これが会社の心臓
2. **agents/を再構成する** — brainから呼べる形にする
3. **agents/evolver.pyを書く** — これが会社の成長エンジン
4. **GitHub Actionsを設定する** — これが会社の心拍
5. **テストして動かす** — 初回の心拍を確認する

Claude Codeがやらないこと:
- 設計書を増やすこと
- 42個のエージェントを定義すること
- 壮大なロードマップを描くこと
- シミュレーション値で「月間1000万円達成確実」と書くこと

**原則: 動くコードだけが価値を持つ。設計書は¥0。**
