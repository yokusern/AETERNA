"""
PDF自動生成スクリプト
テンプレートとデータからPDFを生成する
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Union
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _register_japanese_font():
    """日本語フォントの登録を試みる"""
    font_paths = [
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/usr/share/fonts/truetype/ipafont/ipaexg.ttf",
        "C:/Windows/Fonts/msgothic.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Japanese", path))
                return "Japanese"
            except Exception:
                continue
    return "Helvetica"


class PDFGenerator:
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.font_name = _register_japanese_font()
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        self.title_style = ParagraphStyle(
            "Title", fontName=self.font_name, fontSize=18,
            textColor=colors.HexColor("#1a1a2e"), spaceAfter=6
        )
        self.heading_style = ParagraphStyle(
            "Heading", fontName=self.font_name, fontSize=13,
            textColor=colors.HexColor("#16213e"), spaceAfter=4, spaceBefore=12
        )
        self.body_style = ParagraphStyle(
            "Body", fontName=self.font_name, fontSize=10,
            textColor=colors.HexColor("#333333"), leading=16, spaceAfter=4
        )
        self.meta_style = ParagraphStyle(
            "Meta", fontName=self.font_name, fontSize=9,
            textColor=colors.HexColor("#666666"), spaceAfter=2
        )

    def generate(self, data: dict, filename: str) -> str:
        """データ辞書からPDFを生成する
        data: {"title": str, "sections": [{"heading": str, "body": str}], ...}
        """
        output_path = str(self.output_dir / filename)
        if not filename.endswith(".pdf"):
            output_path += ".pdf"

        doc = SimpleDocTemplate(output_path, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)

        story = []

        # タイトル
        story.append(Paragraph(data.get("title", "Document"), self.title_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#4a90d9")))
        story.append(Spacer(1, 6))

        # メタ情報
        if "date" in data:
            story.append(Paragraph(f"作成日: {data['date']}", self.meta_style))
        if "author" in data:
            story.append(Paragraph(f"作成者: {data['author']}", self.meta_style))
        story.append(Spacer(1, 12))

        # セクション
        for section in data.get("sections", []):
            if section.get("heading"):
                story.append(Paragraph(section["heading"], self.heading_style))
            if section.get("body"):
                for line in section["body"].split("\n"):
                    if line.strip():
                        story.append(Paragraph(line, self.body_style))
            story.append(Spacer(1, 6))

        # テーブルデータ
        if "table" in data:
            table_data = data["table"]
            if table_data:
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a90d9")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(table)

        doc.build(story)
        print(f"PDF生成完了: {output_path}")
        return output_path

    def generate_from_json(self, json_file: str, filename: str = None) -> str:
        """JSONファイルからPDFを生成する"""
        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)
        if not filename:
            filename = Path(json_file).stem + ".pdf"
        return self.generate(data, filename)

    def bulk_generate(self, data_csv: str, filename_column: str,
                      title_column: str = "title", prefix: str = "") -> list[str]:
        """CSVデータから一括PDF生成する"""
        outputs = []
        with open(data_csv, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = f"{prefix}{row[filename_column]}.pdf"
                data = {
                    "title": row.get(title_column, "Document"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "sections": [{"heading": k, "body": v}
                                 for k, v in row.items()
                                 if k not in [filename_column, title_column]]
                }
                output = self.generate(data, filename)
                outputs.append(output)
        return outputs


if __name__ == "__main__":
    gen = PDFGenerator(output_dir="output")
    sample_data = {
        "title": "サンプルレポート",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "author": "AETERNA Holdings",
        "sections": [
            {"heading": "概要", "body": "このPDFはPython自動生成スクリプトで作成されました。"},
            {"heading": "実績", "body": "売上: ¥1,234,567\nユーザー数: 1,000"},
        ],
        "table": [
            ["商品名", "価格", "販売数", "売上"],
            ["プロンプト集", "¥980", "50", "¥49,000"],
            ["Notionテンプレート", "¥1,480", "30", "¥44,400"],
            ["Pythonスクリプト", "¥1,980", "20", "¥39,600"],
        ]
    }
    gen.generate(sample_data, "sample_report.pdf")
