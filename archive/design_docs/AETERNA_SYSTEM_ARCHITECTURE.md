# AETERNA Holdings - システム設計・モジュール仕様書

**作成日**: 2026年5月11日  
**作成者**: 総括分析家（参謀）  
**適用対象**: AETERNA Holdings全事業部（Affiliate.auto / SaaS.auto / Guardian）  
**準拠**: AETERNA_EMPIRE_CONSTITUTION.md (帝国憲法)

---

## 1. 目的

本ドキュメントは、「AETERNA_STRATEGIC_MASTERPLAN.md」で策定された戦略を、エージェントが即時にコードレベルで実行・実装するための具体的なシステム設計とモジュール仕様を定義するものです。すべてのモジュールは「完全自律」「無料枠の最大活用」「APIフォールバック（堅牢性）」の原則に基づいて設計されています。

---

## 2. 第一事業部：Affiliate.auto 強化仕様

### 2.1. APIフォールバックマネージャー (`api_fallback_manager.py`)
現状の `master_autopilot.py` を強化し、APIのレートリミットや枯渇に耐えうる堅牢な生成エンジンを構築します。

- **役割**: メインのLLM API（Gemini等）が失敗した場合、自動的に代替API（Groq, Claude等）に切り替えて処理を継続する。
- **実装要件**:
  - 状態管理: 各APIの残リクエスト数やエラー状態をメモリ（または軽量なローカルJSON）で管理。
  - リトライロジック: エラーコード（429 Too Many Requests 等）を検知し、指数的バックオフでリトライ、規定回数失敗でフォールバック。
  - インターフェース: `generate_content(prompt: str) -> str` の単一インターフェースを提供し、内部の切り替えを隠蔽する。

### 2.2. SEO自動最適化モジュール (`seo_optimizer.py`)
生成された記事のSEO品質を機械的に評価・修正します。

- **役割**: 記事のタイトル、見出し構造、キーワード密度を分析し、必要に応じてリライトを行う。
- **実装要件**:
  - キーワード抽出: ターゲットキーワードの出現頻度を計算。
  - メタデータ生成: 魅力的な `meta description` を自動生成。
  - 内部リンク挿入: 既存の関連記事URLをJSONから読み込み、文脈に合った箇所に自動挿入する機能。

---

## 3. 第二事業部：SaaS.auto (TimeTracker Pro) MVP仕様

### 3.1. システムアーキテクチャ
- **フロントエンド**: Next.js 14 (App Router), React, Tailwind CSS
- **バックエンド/DB**: Supabase (PostgreSQL, Auth)
- **ホスティング**: Vercel
- **決済**: Stripe (テスト環境から開始)

### 3.2. データベーススキーマ (Supabase)
```sql
-- Users table (managed by Supabase Auth, extended here)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT NOT NULL,
  plan TEXT DEFAULT 'free', -- 'free' or 'pro'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Time entries table
CREATE TABLE time_entries (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES profiles(id) NOT NULL,
  project_name TEXT NOT NULL,
  task_description TEXT,
  start_time TIMESTAMP WITH TIME ZONE NOT NULL,
  end_time TIMESTAMP WITH TIME ZONE,
  duration_minutes INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3.3. コア機能モジュール
- **`TimerComponent.tsx`**: スタート/ストップボタン、経過時間のリアルタイム表示。
- **`Dashboard.tsx`**: 今週の総稼働時間、プロジェクト別の円グラフ表示（Recharts等を利用）。
- **`ReportGenerator.ts`** (将来拡張): Supabase Edge Functions を用いて、週次データを集計し、LLM APIを叩いて「今週の稼働分析と改善提案」テキストを生成。

---

## 4. 統制・守備部門：Guardian システム自律復旧仕様

### 4.1. 拡張ヘルスチェック (`enhanced_health_check.py`)
既存の死活監視を拡張し、自律復旧（Self-Healing）のトリガーとします。

- **役割**: サイト、API、データベースの健全性を定期確認し、異常時に復旧スクリプトを起動。
- **監視項目**:
  - サイトHTTPステータス (200 OK)
  - Supabase接続テスト
  - GitHub Actionsの直近の実行ステータス (GitHub API経由)

### 4.2. 自律復旧エージェント (`auto_healer.py`)
- **役割**: `enhanced_health_check.py` からのアラートを受け取り、定義された手順で復旧を試みる。
- **実装要件 (アクション定義)**:
  - Vercelデプロイ失敗時: Vercel APIを叩き、直前の成功したデプロイIDへロールバック。
  - GitHub Actions失敗時: ログを取得してLLMに解析させ、一時的なエラー（ネットワーク等）であれば再実行トリガーを送信。
  - APIキー枯渇時: `.env` 相当の設定ファイル（またはGitHub Secrets）のフォールバックキーへの切り替え通知（自動書き換えはリスクが高いため、段階的に実装）。

---

## 5. 開発・デプロイメントフロー

1. **コード生成**: エージェントが本仕様書に基づき、ローカル（MacBook環境相当のサンドボックス）でコードを生成・テスト。
2. **品質チェック**: `constitution_monitor.py` による帝国憲法準拠チェック（無料ツールのみか、無駄なリソース消費はないか）。
3. **コミット＆プッシュ**: GitHubリポジトリへ自動コミット。
4. **CI/CD**: GitHub Actions がテストを実行し、Vercelへ自動デプロイ。
5. **監視**: デプロイ完了後、Guardianシステムが直ちに監視を開始。

本設計書は即時実行可能な状態であり、エージェントはこれより各モジュールのコーディングタスクに移行可能である。
