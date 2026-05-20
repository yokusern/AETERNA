#!/usr/bin/env python3
"""
Pinterest アクセストークン再取得ツール
======================================
実行するとブラウザが開きます。PinterestでALLOWを押したら自動で
.env と GitHub Secrets 用のトークンが表示されます。

使い方:
  python3 get_pinterest_token.py
"""
import os, re, json, time, threading, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, urlencode
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID     = os.environ.get("PINTEREST_APP_ID", "1571558")
APP_SECRET = os.environ.get("PINTEREST_APP_SECRET", "9384953d5813f290a26faa94a9a1bdc1cc3d58a8")
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "boards:read,pins:write,user_accounts:read"

_token_result = {}
_done = threading.Event()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/callback":
            if "code" in params:
                code = params["code"][0]
                # トークン交換
                r = requests.post(
                    "https://api.pinterest.com/v5/oauth/token",
                    auth=(APP_ID, APP_SECRET),
                    data={
                        "grant_type":   "authorization_code",
                        "code":         code,
                        "redirect_uri": REDIRECT_URI,
                    },
                )
                data = r.json()
                _token_result.update(data)
                at = data.get("access_token", "")

                body = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><title>認証完了</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:60px auto;padding:20px}}
pre{{background:#f5f5f5;padding:20px;border-radius:8px;word-break:break-all;font-size:13px}}</style>
</head><body>
<h2>✅ Pinterest認証完了！</h2>
<p>アクセストークン:</p>
<pre>{at}</pre>
<p>このページを閉じてターミナルに戻ってください。</p>
</body></html>"""
            else:
                error = params.get("error", ["unknown"])[0]
                body = f"<html><body><h2>❌ エラー: {error}</h2></body></html>"

            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
            _done.set()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def update_env(token: str):
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    content = env_path.read_text()
    content = re.sub(r'PINTEREST_ACCESS_TOKEN=.*', f'PINTEREST_ACCESS_TOKEN={token}', content)
    env_path.write_text(content)
    print(f"✅ .env を更新: {env_path}")


def main():
    auth_url = (
        "https://www.pinterest.com/oauth/?"
        + urlencode({
            "client_id":     APP_ID,
            "redirect_uri":  REDIRECT_URI,
            "response_type": "code",
            "scope":         SCOPE,
        })
    )

    server = HTTPServer(("localhost", 8888), Handler)

    print("=" * 65)
    print("  Pinterest トークン取得ツール")
    print("=" * 65)
    print()
    print("ブラウザが自動で開きます。")
    print("Pinterestにログインして「ALLOW」を押してください。")
    print()
    print("ブラウザが開かない場合は下記URLを手動でコピーして開いてください:")
    print()
    print(auth_url)
    print()
    print("待機中...")

    # 1秒後にブラウザを開く
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(auth_url)

    threading.Thread(target=open_browser, daemon=True).start()

    # コールバック待機
    while not _done.is_set():
        server.handle_request()

    if not _token_result.get("access_token"):
        print("❌ トークン取得に失敗しました")
        print(json.dumps(_token_result, ensure_ascii=False, indent=2))
        return

    at = _token_result["access_token"]
    rt = _token_result.get("refresh_token", "")
    exp = _token_result.get("expires_in", 0)

    print()
    print("=" * 65)
    print("✅ トークン取得成功！")
    print("=" * 65)
    print(f"access_token : {at}")
    if rt:
        print(f"refresh_token: {rt}")
    print(f"有効期限     : {exp} 秒 ({exp // 86400} 日)")
    print()

    # .env 更新
    update_env(at)

    print()
    print("─" * 65)
    print("【必須】GitHub Secrets も更新してください")
    print("─" * 65)
    print("URL: https://github.com/yokusern/AETERNA/settings/secrets/actions")
    print("Secret名: PINTEREST_ACCESS_TOKEN")
    print(f"値: {at}")
    print()


if __name__ == "__main__":
    main()
