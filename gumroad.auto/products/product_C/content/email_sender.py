"""
メール自動送信スクリプト
GmailのSMTPを使ってメールを自動送信する
アプリパスワードが必要: https://myaccount.google.com/apppasswords
"""
import smtplib
import csv
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Union


class EmailSender:
    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 587

    def __init__(self, gmail_address: str, app_password: str):
        self.address = gmail_address
        self.password = app_password

    def _build_message(self, to: str, subject: str, body: str,
                       attachments: list = None) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["From"] = self.address
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        for file_path in (attachments or []):
            path = Path(file_path)
            if not path.exists():
                print(f"警告: 添付ファイルが見つかりません: {file_path}")
                continue
            with open(path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{path.name}"')
            msg.attach(part)

        return msg

    def send(self, to: str, subject: str, body: str,
             attachments: list = None) -> bool:
        """単一メールの送信"""
        try:
            msg = self._build_message(to, subject, body, attachments)
            with smtplib.SMTP(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.starttls()
                server.login(self.address, self.password)
                server.send_message(msg)
            print(f"[送信済み] → {to}")
            return True
        except Exception as e:
            print(f"[エラー] {to}: {e}")
            return False

    def bulk_send(self, recipient_csv: str, subject_template: str,
                  body_template: str, attachment_dir: str = None,
                  dry_run: bool = False) -> dict:
        """CSVリストへの一括送信（差し込み機能付き）
        recipient_csv: name, email列を含むCSVファイル
        subject_template: "{name}様へ" のように{列名}で差し込み可能
        body_template: テキストファイルまたはテンプレート文字列
        """
        if os.path.exists(body_template):
            with open(body_template, encoding="utf-8") as f:
                body_text = f.read()
        else:
            body_text = body_template

        stats = {"sent": 0, "failed": 0, "skipped": 0}

        with open(recipient_csv, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("email"):
                    stats["skipped"] += 1
                    continue

                try:
                    subject = subject_template.format(**row)
                    body = body_text.format(**row)
                except KeyError as e:
                    print(f"テンプレートエラー: {e} (行: {row})")
                    stats["failed"] += 1
                    continue

                attachments = []
                if attachment_dir and row.get("name"):
                    for f_path in Path(attachment_dir).glob(f"*{row['name']}*"):
                        attachments.append(str(f_path))

                if dry_run:
                    print(f"[DRY] → {row['email']} | 件名: {subject}")
                    stats["sent"] += 1
                else:
                    success = self.send(row["email"], subject, body, attachments)
                    stats["sent" if success else "failed"] += 1

        print(f"\n=== 一括送信完了 ===")
        print(f"送信: {stats['sent']}件 | 失敗: {stats['failed']}件 | スキップ: {stats['skipped']}件")
        return stats


if __name__ == "__main__":
    print("EmailSenderの使い方:")
    print("  from email_sender import EmailSender")
    print("  sender = EmailSender('your@gmail.com', 'app_password')")
    print("  sender.send('to@example.com', '件名', '本文')")
