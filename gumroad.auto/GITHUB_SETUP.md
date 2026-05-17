# 🔧 GitHub Secrets Setup Guide

## GitHub Actionsで自動実行するための設定

### Step 1: GitHub SecretsにAPIキーを登録

1. リポジトリを開く: https://github.com/[ユーザー名]/AETERNA
2. **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
3. 以下の3つのシークレットを登録する：

| Secret Name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | `.env`ファイルの値をコピー |
| `OPENAI_API_KEY` | `.env`ファイルの値をコピー |
| `GUMROAD_ACCESS_TOKEN` | `.env`ファイルの値をコピー |

### Step 2: ワークフローの確認

- ワークフローファイル: `.github/workflows/gumroad-factory.yml`
- 実行スケジュール: **毎朝9時（JST）**
- 手動実行も可能: Actions → "Gumroad Product Factory - Daily Run" → Run workflow

### Step 3: 動作内容

毎朝9時に自動で以下が実行されます：
1. 商品を5個作成
2. ソーシャルコンテンツを生成
3. 変更をGitにコミットしてプッシュ

---

## ⚠️ 注意点

- **Gumroadへの公開**: GitHub Actionsでは非公開状態で作成します。手動でGumroadダッシュボードから公開してください。
- **リポジトリ**: Publicリポジトリの場合、Secretsは安全に保管されます（外部に漏れません）。
