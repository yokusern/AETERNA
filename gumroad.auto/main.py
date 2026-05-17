#!/usr/bin/env python3
"""
Gumroad Product Factory - English Version
Automated product creation for global market
"""

import os
import sys
import json
import time
import random
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import anthropic

# product_creator_agent は同パッケージ内なので絶対パスで追加
sys.path.insert(0, str(Path(__file__).parent))
from agents.product_creator_agent import create_product as create_typed_product

BASE_DIR = Path(__file__).parent
PRODUCTS_DIR = BASE_DIR / "products"
DATA_DIR = BASE_DIR / "system" / "data"
REPORTS_DIR = BASE_DIR / "system" / "reports"

PRODUCTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


class MarketResearcher:
    """Market Research Class with learning from feedback"""
    
    def __init__(self):
        self.market_data_file = DATA_DIR / "market_analysis.json"
        self.feedback_dir = BASE_DIR / "system" / "feedback"
    
    def load_market_data(self):
        """Load market data"""
        if self.market_data_file.exists():
            with open(self.market_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._generate_default_data()
    
    def _generate_default_data(self):
        """Generate default market data (English)"""
        return {
            "trending_categories": [
                {"category": "Programming", "subcategory": "Python", "trend_score": 95, "user_demand": "high", "avg_price": 15},
                {"category": "Programming", "subcategory": "Data Analysis", "trend_score": 92, "user_demand": "high", "avg_price": 25},
                {"category": "Business", "subcategory": "Side Hustle", "trend_score": 88, "user_demand": "high", "avg_price": 9},
                {"category": "Programming", "subcategory": "React", "trend_score": 85, "user_demand": "high", "avg_price": 20},
                {"category": "AI", "subcategory": "Prompt Engineering", "trend_score": 90, "user_demand": "high", "avg_price": 15},
                {"category": "Business", "subcategory": "Freelancing", "trend_score": 85, "user_demand": "high", "avg_price": 12},
                {"category": "Productivity", "subcategory": "Notion Templates", "trend_score": 88, "user_demand": "high", "avg_price": 9},
                {"category": "Design", "subcategory": "UI/UX", "trend_score": 80, "user_demand": "medium", "avg_price": 19},
                {"category": "Marketing", "subcategory": "Social Media", "trend_score": 82, "user_demand": "medium", "avg_price": 14}
            ],
            "content_ideas": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_feedback(self):
        """Load feedback data"""
        feedback_file = self.feedback_dir / "product_feedback.json"
        if feedback_file.exists():
            with open(feedback_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"approved": [], "rejected": []}
    
    def _load_sales_analysis(self) -> dict:
        """analytics_agent.py が保存した最新分析結果を読む"""
        analysis_file = BASE_DIR / "data" / "latest_analysis.json"
        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def select_product_idea(self):
        """Select product idea — feedback + sales data で重み付け"""
        market_data  = self.load_market_data()
        feedback     = self._load_feedback()
        sales_data   = self._load_sales_analysis()

        trending = market_data["trending_categories"]

        # ── Step 1: 承認/却下フィードバックで重み調整 ──────────────────
        category_stats = {}
        for item in feedback.get("approved", []):
            key = f"{item['category']}:{item['subcategory']}"
            s = category_stats.setdefault(key, {"approved": 0, "rejected": 0})
            s["approved"] += 1
        for item in feedback.get("rejected", []):
            key = f"{item['category']}:{item['subcategory']}"
            s = category_stats.setdefault(key, {"approved": 0, "rejected": 0})
            s["rejected"] += 1

        # ── Step 2: 実売上データで追加ブースト ────────────────────────
        top_selling = {}  # product_name -> revenue
        for name, stats in sales_data.get("products", {}).items():
            top_selling[name.lower()] = stats.get("revenue", 0)

        for category in trending:
            key  = f"{category['category']}:{category['subcategory']}"
            base = category.get("trend_score", 50)

            # フィードバックボーナス
            if key in category_stats:
                st = category_stats[key]
                total = st["approved"] + st["rejected"]
                rate  = st["approved"] / total if total > 0 else 0.5
                feedback_bonus = (rate * 30) - (st["rejected"] * 5)
            else:
                feedback_bonus = 0

            # 売上ボーナス（カテゴリ名が売上商品名に含まれる場合）
            sub = category.get("subcategory", "").lower()
            sales_bonus = sum(rev for name, rev in top_selling.items() if sub in name) / 100

            category["weight"] = max(1, base + feedback_bonus + sales_bonus)

        total_weight = sum(c["weight"] for c in trending)
        weights  = [c["weight"] / total_weight for c in trending]
        selected = random.choices(trending, weights=weights, k=1)[0]

        # ── Step 3: 商品タイプ選択（market_analysis の product_type を優先） ──
        # market_analysis.json が product_type を持っていればそれを使う
        if "product_type" in selected:
            product_type = selected["product_type"]
        else:
            subcategory_type_map = {
                "notion templates": "notion_template",
                "study os": "notion_template",
                "content creator os": "notion_template",
                "prompt engineering": "prompt_pack",
                "chatgpt prompts": "prompt_pack",
                "midjourney prompts": "prompt_pack",
                "social media templates": "prompt_pack",
                "email marketing": "business_template",
                "python automation": "script_pack",
                "javascript": "script_pack",
                "data analysis": "script_pack",
                "side hustle": "guide",
                "freelancing": "guide",
                "business models": "guide",
                "budget tracker": "spreadsheet_pack",
                "habit tracker": "spreadsheet_pack",
                "freelance templates": "business_template",
                "launch checklists": "checklist_pack",
                "seo strategy": "checklist_pack",
                "interactive tools": "html_tool",
            }
            sub_key = selected.get("subcategory", "").lower()
            product_type = subcategory_type_map.get(
                sub_key,
                random.choice(["guide", "notion_template", "prompt_pack", "spreadsheet_pack", "checklist_pack"])
            )
        
        name_templates = [
            f"Complete {selected['subcategory']} Guide",
            f"{selected['subcategory']} for Beginners",
            f"Practical {selected['subcategory']} Handbook",
            f"Master {selected['subcategory']}",
            f"{selected['subcategory']} Essentials",
            f"Quick Start {selected['subcategory']}",
            f"{selected['subcategory']} Blueprint",
            f"{selected['subcategory']} Made Easy"
        ]
        
        idea = {
            "id": f"product_{int(time.time())}",
            "theme": random.choice(name_templates),
            "category": selected["category"],
            "subcategory": selected["subcategory"],
            "product_type": product_type,
            "price": selected["avg_price"] + random.randint(-3, 6),
            "trend_score": selected.get("trend_score", 50),
            "created_at": datetime.now().isoformat()
        }
        
        return idea


class ProductDeveloper:
    """Product Development Class — Claude → Gemini → template fallback"""

    CONTENT_PROMPT = """\
Create a comprehensive, high-quality {product_type} titled "{theme}".

Topic: {subcategory} (Category: {category})
Target audience: English-speaking learners, beginners to intermediate level
Price point: ${price} — the content must justify this price

Requirements:
- Minimum 3,000 words of genuinely useful, actionable content
- Use Markdown formatting with clear H2/H3 headings
- Include concrete examples, step-by-step instructions, and practical tips
- Write as if this is a standalone product a buyer will refer to repeatedly
- Do NOT include placeholder text like "add your content here"

Structure:
# {theme}

## Introduction
## Chapter 1: Foundations
## Chapter 2: Core Techniques
## Chapter 3: Advanced Strategies
## Chapter 4: Common Mistakes & How to Avoid Them
## Conclusion & Next Steps

Write the complete content now. Output only the Markdown document, no preamble:"""

    GUMROAD_PROMPT = """\
Write a high-converting Gumroad product description for this digital product.

Title: {theme}
Type: {product_type}
Topic: {subcategory}
Price: ${price}

Rules:
- Open with the buyer's pain point (1-2 sentences)
- Show the transformation they'll get
- List specific benefits with bullet points
- End with a clear CTA and 30-day guarantee
- Output only the Markdown description, no preamble"""

    def __init__(self):
        self._llm_type, self._llm_client = self._init_llm()

    def _init_llm(self):
        """Claude → Gemini → None の順で試す"""
        # 1. Claude
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if key and len(key) > 10:
            try:
                import anthropic as _anthropic
                client = _anthropic.Anthropic(api_key=key)
                print("  [LLM] Claude API 使用")
                return ("claude", client)
            except Exception as e:
                print(f"  [LLM] Claude 初期化失敗: {e}")

        # 2. Gemini (free tier: 15 RPM, 1500 RPD)
        gkey = os.environ.get("GEMINI_API_KEY", "")
        if gkey and len(gkey) > 10:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gkey)
                model = genai.GenerativeModel("gemini-1.5-flash")
                print("  [LLM] Gemini 1.5 Flash 使用 (無料枠)")
                return ("gemini", model)
            except Exception as e:
                print(f"  [LLM] Gemini 初期化失敗: {e}")

        print("  [LLM] APIキーなし — テンプレートモードで生成")
        return (None, None)

    def _call_gemini(self, prompt: str, max_tokens: int = 4096) -> str | None:
        gkey = os.environ.get("GEMINI_API_KEY", "")
        if not gkey:
            return None
        try:
            import google.generativeai as genai
            genai.configure(api_key=gkey)
            model = genai.GenerativeModel("gemini-1.5-flash")
            resp = model.generate_content(
                prompt,
                generation_config={"max_output_tokens": max_tokens},
            )
            return resp.text.strip()
        except Exception as e:
            print(f"  [Gemini] エラー: {e}")
            return None

    def _call_llm(self, prompt: str, max_tokens: int = 4096) -> str | None:
        if self._llm_type == "claude":
            try:
                resp = self._llm_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return resp.content[0].text.strip()
            except Exception as e:
                print(f"  [Claude] エラー ({e.__class__.__name__}) — Geminiにフォールバック")
                return self._call_gemini(prompt, max_tokens)

        if self._llm_type == "gemini":
            return self._call_gemini(prompt, max_tokens)

        return None

    def generate_product_content(self, idea) -> str | None:
        if self._llm_type:
            prompt = self.CONTENT_PROMPT.format(**idea)
            print(f"  → {self._llm_type.capitalize()} にコンテンツ生成をリクエスト中...")
            return self._call_llm(prompt, max_tokens=4096)
        return None

    def create_gumroad_page(self, idea) -> str:
        """LLMでセールスコピー生成。失敗時はテンプレート。"""
        if self._llm_type:
            prompt = self.GUMROAD_PROMPT.format(**idea)
            print(f"  → {self._llm_type.capitalize()} にセールスコピー生成をリクエスト中...")
            result = self._call_llm(prompt, max_tokens=1024)
            if result:
                return result

        # テンプレートフォールバック
        sub  = idea["subcategory"]
        ptype = idea["product_type"].replace("_", " ").title()
        price = idea["price"]
        return f"""## {idea["theme"]}

### Stop Wasting Time — Get the {sub} Shortcut That Actually Works

Most people trying to learn {sub} spend months on the wrong things. This {ptype} cuts straight to what matters.

### What's Inside

- Step-by-step framework you can follow from day one
- Real examples and templates — no filler, no theory-only content
- The 20% of {sub} that produces 80% of results
- Beginner-friendly structure that goes deep enough to be genuinely valuable

### Who This Is For

✅ Beginners who want a clear path, not scattered tutorials
✅ People who've tried learning {sub} before but got stuck
✅ Anyone who wants practical skills, not just theory

### One-Time Purchase. Instant Download. Keep Forever.

**${price}** — 30-day money-back guarantee. Full refund if you're not satisfied.
"""
    
    def save_product(self, idea, claude_content=None):
        """Save spec.json. Returns (product_dir, spec) tuple."""
        product_dir = PRODUCTS_DIR / idea['id']
        product_dir.mkdir(exist_ok=True)

        spec = {
            "product_id": idea['id'],
            "name": idea['theme'],
            "category": idea['category'],
            "subcategory": idea['subcategory'],
            "product_type": idea['product_type'],
            "price_usd": idea['price'],
            "trend_score": idea['trend_score'],
            "content_file": "content.md",
            "file_format": "MD"
        }

        with open(product_dir / "spec.json", 'w', encoding='utf-8') as f:
            json.dump(spec, f, ensure_ascii=False, indent=2)

        # Claude が生成したコンテンツがあれば保存（guide 系で使う）
        if claude_content and len(claude_content) > 500:
            (product_dir / "content.md").write_text(claude_content, encoding="utf-8")

        return product_dir, spec


class ProductPublisher:
    """Gumroad Publisher Class"""
    
    def __init__(self):
        from gumroad_uploader import GumroadUploader
        self.uploader = GumroadUploader()
    
    def publish_to_gumroad(self, product_dir, idea, publish_now=False):
        """Publish product to Gumroad"""
        try:
            # Gumroad expects price in CENTS! ($15 = 1500 cents)
            price_cents = int(idea['price'] * 100)
            
            product = self.uploader.create_product(
                name=idea['theme'],
                price_cents=price_cents,
                description=self._extract_description(product_dir),
                published=False
            )
            
            content_file = product_dir / "content.md"
            if content_file.exists():
                self.uploader.upload_file(product['id'], str(content_file))
            
            if publish_now:
                self.uploader.publish(product['id'])
            
            return {
                "success": True,
                "product_id": product['id'],
                "product_url": f"https://app.gumroad.com/products/{product['id']}",
                "published": publish_now
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_description(self, product_dir):
        """Extract description from gumroad_page.md"""
        page_file = product_dir / "gumroad_page.md"
        if page_file.exists():
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if "## Description" in content:
                return content.split("## Description")[-1].strip()
        return ""


class GumroadProductFactory:
    """Main Factory Class"""

    def __init__(self):
        self.researcher = MarketResearcher()
        self.developer  = ProductDeveloper()  # Claude → Gemini → template
        try:
            self.publisher = ProductPublisher()
        except Exception:
            self.publisher = None
    
    def run_once(self, publish=False):
        """Run one cycle: Research → Develop → (Optional) Publish"""
        print("=" * 70)
        print("  Gumroad Product Factory - Starting Production")
        print("=" * 70)

        # 1. Market Research
        print("\n[1/4] Researching market trends...")
        idea = self.researcher.select_product_idea()
        print(f"  -> Idea: {idea['theme']}")
        print(f"  -> Category: {idea['category']} > {idea['subcategory']} ({idea['product_type']})")
        print(f"  -> Price: ${idea['price']}")

        # 2. Product Development — Claude API (graceful fallback if credits gone)
        print("\n[2/4] Developing product...")
        claude_content = None
        try:
            claude_content = self.developer.generate_product_content(idea)
            print(f"  -> Claude content ready ({len(claude_content):,} chars)")
        except Exception as e:
            print(f"  ! Claude API unavailable ({e.__class__.__name__}) — using built-in templates")

        # Save spec.json (+ Claude content if available)
        product_dir, spec = self.developer.save_product(idea, claude_content)

        # 3. Generate type-appropriate files (ZIPs / CSVs / scripts / gumroad_page.md)
        print("\n[3/4] Generating product files...")
        try:
            file_info = create_typed_product(spec, product_dir)
            print(f"  -> Files: {file_info.get('files', [])}")
            # For text-based types, prefer Claude content over the template if we got it
            if claude_content and idea['product_type'] in ("guide", "ebook", "course"):
                (product_dir / "content.md").write_text(claude_content, encoding="utf-8")
                print("  -> Claude content applied to content.md")
        except Exception as e:
            print(f"  ! Creator agent error: {e}")

        # 3b. カバー画像生成（Pinterest・Gumroad用）
        try:
            from cover_generator import generate_cover
            cover_path = product_dir / "cover.png"
            if not cover_path.exists():
                generate_cover(spec, cover_path)
                print(f"  -> Cover image: cover.png")
        except Exception as e:
            print(f"  ! Cover generation error: {e}")

        print(f"  -> Product dir: {product_dir}")
        
        # 4. Gumroad Publishing (direct — or use dashboard approve button)
        result = None
        if publish:
            print("\n[4/4] Publishing to Gumroad...")
            result = self.publisher.publish_to_gumroad(product_dir, idea, publish_now=False)
            if result['success']:
                print(f"  -> Published! URL: {result['product_url']}")
            else:
                print(f"  ! Publishing failed: {result['error']}")
        else:
            print("\n[4/4] Ready for dashboard approval (run local_server.py to approve)")

        self._save_report(idea, product_dir, result)

        print("\n" + "=" * 70)
        print("  Product development complete!")
        print(f"  Saved at: {product_dir}")
        if result and result['success']:
            print(f"  Gumroad: {result['product_url']}")
        print("=" * 70)

        return {"idea": idea, "product_dir": str(product_dir), "gumroad_result": result}
    
    def _save_report(self, idea, product_dir, gumroad_result):
        """Save report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "idea": idea,
            "product_dir": str(product_dir),
            "gumroad_result": gumroad_result
        }
        
        report_file = REPORTS_DIR / f"product_{int(time.time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    
    def run_multiple(self, count=5, publish=False):
        """Run multiple times"""
        print(f"\n📦 Developing {count} products...\n")
        results = []
        
        for i in range(count):
            print(f"\n--- [{i+1}/{count}] ---")
            try:
                result = self.run_once(publish=publish)
                results.append(result)
            except Exception as e:
                print(f"  ❌ Error: {e}")
            
            if i < count - 1:
                wait_time = 2
                print(f"\n  ⏸️  Waiting {wait_time} seconds...")
                time.sleep(wait_time)
        
        print(f"\n🎉 Done! Developed {len(results)} products.")
        return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Gumroad Product Factory - English Version')
    parser.add_argument('--count', type=int, default=1, help='Number of products to develop (default:1)')
    parser.add_argument('--publish', action='store_true', help='Publish to Gumroad')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode continuously')
    parser.add_argument('--interval', type=float, default=4.8, help='Interval in hours (default:4.8 = 5x/day)')
    
    args = parser.parse_args()
    
    factory = GumroadProductFactory()
    
    if args.daemon:
        print(f"🔄 Daemon mode: Running every {args.interval} hours")
        print("   Press Ctrl+C to stop\n")
        
        try:
            while True:
                factory.run_once(publish=args.publish)
                wait_seconds = args.interval * 3600
                next_run = datetime.now() + datetime.timedelta(hours=args.interval)
                print(f"\n⏰ Next run: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   (Waiting: {int(wait_seconds)} seconds)\n")
                time.sleep(wait_seconds)
        except KeyboardInterrupt:
            print("\n👋 Stopping...")
    else:
        if args.count > 1:
            factory.run_multiple(args.count, publish=args.publish)
        else:
            factory.run_once(publish=args.publish)


if __name__ == "__main__":
    main()
