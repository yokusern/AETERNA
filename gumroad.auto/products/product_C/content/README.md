# Python自動化スクリプト5選

**対象**: Python初級〜中級者、業務自動化に興味がある方  
**価格**: ¥1,980  
**形式**: ZIP（Pythonスクリプト5本 + 各README）

---

## 収録スクリプト一覧

| # | スクリプト | ファイル | 用途 |
|---|---|---|---|
| 1 | ファイル自動整理 | `file_organizer.py` | 指定フォルダ内のファイルを拡張子別に自動分類 |
| 2 | CSV一括加工 | `csv_processor.py` | 複数CSVの結合・フィルタ・集計を自動化 |
| 3 | メール自動送信 | `email_sender.py` | Gmailから条件付きメールを自動送信 |
| 4 | Webスクレイピング | `web_scraper.py` | 指定サイトからデータを自動収集・CSV保存 |
| 5 | PDF自動生成 | `pdf_generator.py` | テンプレートからPDFレポートを自動生成 |

---

## セットアップ（共通）

```bash
# Python 3.8以上が必要
python --version

# 必要ライブラリのインストール
pip install -r requirements.txt
```

---

## スクリプト1: ファイル自動整理（file_organizer.py）

### 機能
指定フォルダ内のファイルを拡張子別にサブフォルダに自動分類します。

```python
from file_organizer import FileOrganizer

organizer = FileOrganizer(
    source_dir="~/Downloads",  # 整理したいフォルダ
    target_dir="~/Organized"   # 整理後の保存先
)
organizer.organize()
```

### 分類ルール（カスタマイズ可能）
- `images/`: .jpg, .jpeg, .png, .gif, .heic
- `documents/`: .pdf, .docx, .xlsx, .pptx, .txt
- `videos/`: .mp4, .mov, .avi
- `audio/`: .mp3, .wav, .flac
- `code/`: .py, .js, .ts, .html, .css
- `archives/`: .zip, .tar.gz, .rar
- `others/`: 上記以外

### 実行例
```
Before: Downloads/ (152ファイル混在)
After:  Organized/
        ├── images/ (45ファイル)
        ├── documents/ (38ファイル)
        ├── videos/ (12ファイル)
        └── others/ (57ファイル)
```

---

## スクリプト2: CSV一括加工（csv_processor.py）

### 機能
複数のCSVファイルを結合し、フィルタリング・集計を自動化します。

```python
from csv_processor import CSVProcessor

processor = CSVProcessor()

# 複数CSVの結合
processor.merge(
    input_dir="data/monthly_reports/",
    output_file="data/merged.csv",
    encoding="utf-8-sig"  # Excel対応
)

# フィルタリング
processor.filter(
    input_file="data/merged.csv",
    output_file="data/filtered.csv",
    conditions={"status": "完了", "amount": (">", 10000)}
)

# 集計
processor.aggregate(
    input_file="data/merged.csv",
    group_by="category",
    agg_columns={"amount": "sum", "count": "count"},
    output_file="data/summary.csv"
)
```

### 対応機能
- 文字コード自動検出（UTF-8, Shift-JIS, CP932）
- 日付列の自動パース
- 重複行の検出・削除
- ピボットテーブル生成

---

## スクリプト3: メール自動送信（email_sender.py）

### 機能
Gmailから条件に基づいたメールを自動送信します。

```python
from email_sender import EmailSender

sender = EmailSender(
    gmail_address="your@gmail.com",
    app_password="xxxx-xxxx-xxxx-xxxx"  # Googleアプリパスワード
)

# 単一送信
sender.send(
    to="recipient@example.com",
    subject="自動送信テスト",
    body="本文テキスト",
    attachments=["report.pdf"]  # 添付ファイル（オプション）
)

# CSVリストへの一括送信（差し込み機能付き）
sender.bulk_send(
    recipient_csv="contacts.csv",  # name, email列必須
    subject_template="【{name}様へ】月次レポートをお送りします",
    body_template="templates/monthly_report_email.txt",
    attachment_dir="reports/"  # {name}でマッチング
)
```

### 注意事項
- Gmailの「アプリパスワード」が必要（2段階認証設定後に発行）
- 1日の送信上限: 500通（Gmail無料）

---

## スクリプト4: Webスクレイピング（web_scraper.py）

### 機能
指定URLからデータを自動収集し、CSVに保存します。

```python
from web_scraper import WebScraper

scraper = WebScraper(delay=1.0)  # リクエスト間隔（秒）

# 単一ページのスクレイピング
data = scraper.scrape(
    url="https://example.com/products",
    selectors={
        "name": "h2.product-title",
        "price": "span.price",
        "rating": "div.rating::attr(data-score)"
    }
)

# ページネーション対応
all_data = scraper.scrape_paginated(
    base_url="https://example.com/items?page={page}",
    start_page=1,
    max_pages=10,
    selectors={...}
)

scraper.save_csv(all_data, "output.csv")
```

### 注意事項
- robots.txtとサイトの利用規約を確認してから使用してください
- 過度なリクエストは行わないよう`delay`を適切に設定してください
- JavaScript動的サイトにはSeleniumが必要（別途設定）

---

## スクリプト5: PDF自動生成（pdf_generator.py）

### 機能
テンプレートとデータからPDFレポートを自動生成します。

```python
from pdf_generator import PDFGenerator

generator = PDFGenerator(
    template_file="templates/report_template.html",
    output_dir="output/"
)

# 単一PDF生成
generator.generate(
    data={
        "title": "月次売上レポート",
        "period": "2026年4月",
        "total_sales": 1234567,
        "items": [{"name": "商品A", "qty": 100, "amount": 980000}, ...]
    },
    filename="report_2026_04.pdf"
)

# CSVデータから一括生成
generator.bulk_generate(
    data_csv="sales_data.csv",
    filename_column="customer_id",
    prefix="invoice_"
)
```

### テンプレートについて
- HTMLテンプレート（Jinja2形式）を使用
- 日本語フォント対応（IPAexゴシック同梱）
- A4サイズ、カスタムサイズ対応

---

## requirements.txt

```
pandas>=2.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
reportlab>=4.0.0
jinja2>=3.1.0
openpyxl>=3.1.0
chardet>=5.0.0
```

---

## よくある質問

**Q: Pythonのバージョンは？**  
A: Python 3.8以上。3.10〜3.12を推奨します。

**Q: Windowsでも動きますか？**  
A: はい。Windows/Mac/Linuxすべて対応しています。

**Q: カスタマイズできますか？**  
A: 全スクリプトはMITライセンスです。自由に改変・商用利用できます。

**Q: エラーが出た場合は？**  
A: `requirements.txt`のインストールを確認してください。それでも解決しない場合は、エラーメッセージをGPT-4に貼り付けると解決できます。

---

*AETERNA Holdings - Python自動化スクリプト5選*
