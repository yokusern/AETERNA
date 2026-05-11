"""
Webスクレイピングスクリプト
指定URLからデータを取得してCSVに保存する
※利用前にrobots.txtと利用規約を必ず確認すること
"""
import time
import csv
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Union
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser


class WebScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; research-bot/1.0)"
    }

    def __init__(self, delay: float = 1.0, timeout: int = 10):
        self.delay = delay
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def check_robots(self, url: str) -> bool:
        """robots.txtでアクセス許可を確認する"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(self.HEADERS["User-Agent"], url)
        except Exception:
            return True

    def _get_soup(self, url: str) -> BeautifulSoup:
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return BeautifulSoup(response.text, "html.parser")

    def scrape(self, url: str, selectors: dict) -> list[dict]:
        """単一ページのスクレイピング
        selectors例: {"name": "h2.title", "price": "span.price"}
        CSS属性取得: "img::attr(src)" または "a::attr(href)"
        """
        print(f"スクレイピング中: {url}")
        soup = self._get_soup(url)
        results = []

        for key, selector in selectors.items():
            if "::attr(" in selector:
                css, attr = selector.split("::attr(")
                attr = attr.rstrip(")")
                elements = [el.get(attr, "") for el in soup.select(css)]
            else:
                elements = [el.get_text(strip=True) for el in soup.select(selector)]

            # 最初の要素数を基準行数として揃える
            if not results:
                results = [{} for _ in elements]
            for i, val in enumerate(elements):
                if i < len(results):
                    results[i][key] = val

        time.sleep(self.delay)
        return results

    def scrape_paginated(self, base_url: str, selectors: dict,
                         start_page: int = 1, max_pages: int = 5,
                         page_param: str = "{page}") -> list[dict]:
        """ページネーション対応スクレイピング
        base_url例: "https://example.com/items?page={page}"
        """
        all_results = []
        for page in range(start_page, start_page + max_pages):
            url = base_url.replace(page_param, str(page))
            try:
                results = self.scrape(url, selectors)
                if not results:
                    print(f"ページ{page}: データなし（終了）")
                    break
                all_results.extend(results)
                print(f"ページ{page}: {len(results)}件取得（累計: {len(all_results)}件）")
            except requests.HTTPError as e:
                print(f"ページ{page}: HTTPエラー {e}（終了）")
                break

        return all_results

    def save_csv(self, data: list[dict], output_file: str, encoding: str = "utf-8-sig"):
        """データをCSVに保存する"""
        if not data:
            print("保存するデータがありません")
            return

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", newline="", encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        print(f"保存完了: {len(data)}件 → {output_file}")


if __name__ == "__main__":
    print("WebScraperの使い方:")
    print("  from web_scraper import WebScraper")
    print("  scraper = WebScraper(delay=1.0)")
    print("  data = scraper.scrape('https://example.com', {'title': 'h1', 'price': '.price'})")
    print("  scraper.save_csv(data, 'output.csv')")
    print("\n⚠️  利用前にrobots.txtと利用規約を必ず確認してください")
