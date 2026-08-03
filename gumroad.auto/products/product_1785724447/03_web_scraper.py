#!/usr/bin/env python3
"""03_web_scraper.py - Scrape any website to CSV"""
import argparse, csv, requests
from bs4 import BeautifulSoup

def scrape(url, selector, output, limit=200):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    r.raise_for_status()
    items = BeautifulSoup(r.text, "html.parser").select(selector)[:limit]
    rows = [{"text": el.get_text(strip=True), "href": el.get("href",""), "src": el.get("src","")} for el in items]
    with open(output, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["text","href","src"]); w.writeheader(); w.writerows(rows)
    print(f"Saved {len(rows)} items -> {output}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("url"); p.add_argument("--selector", default="a")
    p.add_argument("--output", default="scraped.csv"); p.add_argument("--limit", type=int, default=200)
    a = p.parse_args(); scrape(a.url, a.selector, a.output, a.limit)
