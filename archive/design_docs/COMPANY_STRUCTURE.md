# AETERNA Holdings - 組織構造 v2.0

**制定日**: 2026-05-11  
**方針**: 売上ゼロから最速で収益化するための最小構成

---

## 組織図

```
CEO（人間）
  │
  └── 参謀エージェント（strategist_agent.py）
        ├── 商品企画エージェント（product_planner_agent.py）
        ├── 商品制作エージェント（product_builder_agent.py）
        ├── 販売最適化エージェント（sales_optimizer_agent.py）
        └── 分析・改善エージェント（analytics_agent.py）
```

---

## 各エージェントの責務

| エージェント | ファイル | 入力 | 出力 |
|---|---|---|---|
| 参謀 | `strategist_agent.py` | 全エージェントの出力JSON | `data/daily_plan.json` |
| 商品企画 | `product_planner_agent.py` | トレンドデータ | `product_specs/*.json` |
| 商品制作 | `product_builder_agent.py` | 企画書JSON | 完成品ファイル（PDF/ZIP） |
| 販売最適化 | `sales_optimizer_agent.py` | 完成品 + Gumroad売上 | 公開済みURL・価格調整 |
| 分析・改善 | `analytics_agent.py` | Gumroad売上データ | `data/reports/` + Discord通知 |

---

## データフロー

```
[product_planner] → product_specs/YYYY-MM-DD.json
[product_builder] → products/PRODUCT_ID/ (コンテンツ一式)
[sales_optimizer] → Gumroad公開 + data/products/registry.json
[analytics]       → data/reports/YYYY-MM-DD.md + Discord
[strategist]      → data/daily_plan.json (次の実行優先順位)
```

---

## ディレクトリ構造

```
gumroad.auto/
├── agents/                    # 5エージェント
│   ├── strategist_agent.py
│   ├── product_planner_agent.py
│   ├── product_builder_agent.py
│   ├── sales_optimizer_agent.py
│   └── analytics_agent.py
├── products/                  # 制作済み商品
│   └── {product_id}/
│       ├── content/           # コンテンツファイル
│       ├── spec.json          # 商品仕様
│       └── gumroad_page.md   # 商品ページ説明文
├── product_specs/             # 企画書JSON
├── data/
│   ├── sales/                 # 日次売上CSV
│   ├── products/              # 商品登録情報
│   ├── reports/               # 分析レポート
│   └── logs/                  # 実行ログ
├── gumroad_uploader.py        # Gumroad API連携
└── run_pipeline.py            # パイプライン実行エントリポイント
```

---

## 凍結事業部（再始動条件）

| 事業部 | 再始動条件 | 場所 |
|---|---|---|
| Affiliate.auto | 月間売上¥100,000達成後 | `archive/` → `Affiliate.auto/` |
| SaaS.auto | 月間売上¥300,000達成後 | `archive/saas/` → `SaaS.auto/` |
| project_electronics | 未定 | `archive/electronics/` |

---

*AETERNA Holdings 組織構造 v2.0 - 2026-05-11*
