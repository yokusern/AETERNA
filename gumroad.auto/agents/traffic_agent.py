#!/usr/bin/env python3
"""
Traffic Agent
各商品のオーガニックトラフィック用コンテンツを自動生成する。
- Reddit 投稿（value-first, CTA あり）
- Twitter/X スレッド（10ツイート）
- メールシーケンス（5通）
生成結果は products/<id>/marketing/ に保存。
"""
import json, time
from pathlib import Path
from datetime import datetime

BASE_DIR     = Path(__file__).parent.parent
PRODUCTS_DIR = BASE_DIR / "products"


# ── Reddit 投稿生成 ──────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = {
    "Productivity":  ["r/productivity", "r/getdisciplined", "r/selfimprovement", "r/LifeProTips"],
    "AI":            ["r/ChatGPT", "r/artificial", "r/AItools", "r/ChatGPTPromptEngineering"],
    "Finance":       ["r/personalfinance", "r/financialindependence", "r/frugal", "r/povertyfinance"],
    "Business":      ["r/Entrepreneur", "r/smallbusiness", "r/startups", "r/sidehustle"],
    "Marketing":     ["r/marketing", "r/socialmedia", "r/digital_marketing", "r/content_marketing"],
    "Programming":   ["r/learnpython", "r/Python", "r/learnprogramming", "r/webdev"],
    "Design":        ["r/web_design", "r/UI_Design", "r/graphic_design"],
}


def generate_reddit_post(spec: dict, gumroad_url: str) -> str:
    name       = spec["name"]
    category   = spec.get("category", "Business")
    sub        = spec.get("subcategory", "")
    ptype      = spec.get("product_type", "guide").replace("_", " ")
    price      = spec.get("price_usd", spec.get("price", 15))
    subs       = REDDIT_SUBREDDITS.get(category, ["r/selfimprovement"])

    post = f"""# I spent 3 months building this — sharing what actually worked for {sub}

[VALUE POST — post to: {', '.join(subs[:3])}]

---

**Title:** I put together everything I learned about {sub} into one resource — here's what's actually inside

---

**Body:**

Hey everyone,

I've been deep in {sub} for the past few months and got frustrated by how scattered all the good information was. Tutorials that skip the basics, guides that are 80% filler, YouTube videos where the actual content starts at minute 12.

So I built something I wish existed when I started.

Here's what I actually learned that makes a difference:

**The 3 things that matter most in {sub}:**

1. **Start with the foundation, not the advanced stuff.** Most people jump to the complex techniques before the basics are automatic. This is the #1 reason people plateau. Get boring good at the fundamentals first.

2. **Systems beat motivation every time.** I used to rely on feeling motivated. Now I have a system. The system runs on my worst days. The result is the same either way.

3. **The 80/20 of {sub}.** About 20% of the techniques produce 80% of the results. Everything else is noise. Identify that 20% and ignore the rest until you've mastered it.

---

After documenting all of this, I packaged it into **{name}** — a {ptype} that covers the exact framework I use.

It's on Gumroad for ${price}: {gumroad_url}

But honestly, even if you don't get it, the 3 principles above are the core insight. Apply those and you'll be ahead of 90% of people.

Happy to answer questions in the comments.

---

*Note: I made the product so this is technically promotional, but I tried to make this post genuinely useful regardless. Remove the link if the mods prefer.*
"""
    return post


# ── Twitter/X スレッド生成 ───────────────────────────────────────────────────

def generate_twitter_thread(spec: dict, gumroad_url: str) -> str:
    name  = spec["name"]
    sub   = spec.get("subcategory", "your field")
    price = spec.get("price_usd", spec.get("price", 15))
    ptype = spec.get("product_type", "guide").replace("_", " ")

    thread = f"""# Twitter/X Thread
# Post these 10 tweets 30 seconds apart (use Typefully or TweetDeck)
# Each tweet is a separate post in the thread

---

[Tweet 1/10 — Hook]
I studied {sub} for 6 months.

Here's what actually matters (thread) 🧵

---

[Tweet 2/10]
First: most people learn {sub} completely backwards.

They start with advanced tactics before mastering the foundation.

Then they wonder why nothing sticks.

---

[Tweet 3/10]
The foundation is simple:

→ Understand the 2-3 core principles
→ Apply them consistently for 30 days
→ THEN add complexity

Skip this and you'll be stuck forever.

---

[Tweet 4/10]
The biggest mistake I made early on:

Optimizing for activity instead of outcomes.

"I spent 2 hours on {sub} today" is meaningless.

"I moved my key metric by X" is what matters.

---

[Tweet 5/10]
The 80/20 of {sub}:

20% of the techniques produce 80% of results.

Most "experts" don't tell you which 20%.

They want you confused so you keep buying courses.

---

[Tweet 6/10]
Here's the 20% that actually works:

1. Foundation first — build on solid ground
2. Consistency beats intensity every time
3. Measure outcomes, not effort
4. Find the constraint and fix that first

---

[Tweet 7/10]
Systems > Motivation.

Motivation is unreliable.

A good system runs on your worst day.

If you need to "feel like it" to do the work, the system is broken.

---

[Tweet 8/10]
Quick recap:
→ Foundation before tactics
→ Outcomes not activity
→ 80/20 the effort
→ Systems not willpower

Apply these 4 and you'll outperform 90% of people in {sub}.

---

[Tweet 9/10]
I put all of this into a {ptype}: **{name}**

→ The framework I use
→ Templates included
→ Works even if you're a beginner
→ ${price} one-time

{gumroad_url}

---

[Tweet 10/10]
If you found this useful:

RT the first tweet to help others.

And follow me — I share stuff like this weekly.

What's your biggest challenge with {sub}? Drop it below 👇

---
"""
    return thread


# ── メールシーケンス生成 ─────────────────────────────────────────────────────

def generate_email_sequence(spec: dict, gumroad_url: str) -> str:
    name  = spec["name"]
    sub   = spec.get("subcategory", "your field")
    price = spec.get("price_usd", spec.get("price", 15))
    ptype = spec.get("product_type", "guide").replace("_", " ")

    seq = f"""# Email Marketing Sequence — {name}
# 5 emails over 7 days. Import into Mailchimp / ConvertKit / Beehiiv.

---

## EMAIL 1 — Day 0 (Welcome)
**Subject:** You asked about {sub} — here's where to start

Hi [First Name],

Thanks for joining. I want to give you something useful right away.

The #1 mistake people make with {sub}:

Starting with the advanced stuff before the foundation is solid.

Here's how to fix that: [Short 3-step explanation]

Step 1: Define your ONE metric that tells you it's working
Step 2: Do the minimum viable practice daily for 14 days
Step 3: Add complexity only after step 2 is automatic

That's the whole framework. Most people skip step 1.

Next email comes in 2 days — I'll share the 80/20 of {sub}.

[Your name]

---

## EMAIL 2 — Day 2 (Value)
**Subject:** The 80/20 of {sub} (most people ignore this)

Hi [First Name],

Quick one today.

20% of {sub} techniques produce 80% of results.

The 20% that matters:
• [Core technique 1]
• [Core technique 2]
• [Core technique 3]

The 80% that's noise:
• Complex advanced tactics before basics
• Switching systems every week
• Optimizing things that don't move the main metric

Focus on the 20%. Ignore everything else until it's automatic.

Tomorrow: the biggest mistake I see beginners make.

[Your name]

---

## EMAIL 3 — Day 4 (Story + Soft Pitch)
**Subject:** I made this mistake for 6 months

Hi [First Name],

Quick story.

When I started with {sub}, I spent 6 months consuming content without making real progress.

Why? I was optimizing for learning instead of doing.

The shift that changed everything: I stopped reading about {sub} and started *applying* one thing at a time.

Results came within 2 weeks.

I documented the exact system I built into **{name}** — a {ptype} that covers:
→ The core framework
→ Ready-to-use templates
→ Step-by-step from zero

It's ${price} one-time: {gumroad_url}

Not pushing you — just sharing what worked for me.

[Your name]

---

## EMAIL 4 — Day 6 (Objection Handling)
**Subject:** "I don't have time for this"

Hi [First Name],

The most common thing I hear: "I'd love to get better at {sub} but I don't have time."

Real talk: this is usually not a time problem.

It's a clarity problem.

When you know exactly what to do (and what to skip), you need 20 minutes a day. Not 2 hours.

The reason people feel like they "don't have time" is that they're doing the wrong things — the 80% that doesn't move the needle.

If you've been putting it off, {name} gives you the exact 20% to focus on.

${price}: {gumroad_url}

Or don't — either way, focus on what moves the needle.

[Your name]

---

## EMAIL 5 — Day 7 (Final CTA + Urgency)
**Subject:** Last email about this (I mean it)

Hi [First Name],

This is the last email I'll send about {name}.

If you've been on the fence: the product isn't going anywhere, but the mindset that says "I'll do it later" is expensive.

Six months from now, you'll either:
A) Have been applying this for 6 months and be significantly further ahead
B) Still be thinking about it

One leads to results. One leads to regret.

${price}: {gumroad_url}

If it's not for you, no worries. I'll keep sending value either way.

[Your name]

P.S. If you do get it and love it — forward this email to someone who'd benefit. That means a lot.

---
"""
    return seq


# ── SEO商品説明文生成 ────────────────────────────────────────────────────────

def generate_seo_description(spec: dict, gumroad_url: str) -> str:
    name  = spec["name"]
    sub   = spec.get("subcategory", "")
    cat   = spec.get("category", "")
    price = spec.get("price_usd", spec.get("price", 15))
    ptype = spec.get("product_type", "guide").replace("_", " ")

    keywords = [sub.lower(), cat.lower(), f"{sub.lower()} {ptype}",
                f"best {sub.lower()} resource", f"{sub.lower()} for beginners",
                f"learn {sub.lower()}", f"{ptype} {sub.lower()} download"]

    desc = f"""## SEO-Optimized Product Description
## Primary keyword: "{sub} {ptype}"
## Secondary keywords: {', '.join(keywords[2:])}

---

### Long Description (for Gumroad / landing page):

**{name}**

*The complete {ptype} for anyone serious about {sub}.*

If you've been searching for a {sub} resource that actually covers everything — without the filler — this is it.

**What makes this different:**

Most {sub} resources are either too basic (you already know this) or too complex (you're not there yet). This {ptype} is designed for the space in between: people who are serious, but want a clear, proven path.

**What you get:**
- A step-by-step framework you can follow from day one
- Real templates and examples, not theoretical concepts
- The 20% of {sub} that produces 80% of results
- Beginner-friendly but goes deep enough to be genuinely valuable

**Who this is for:**
✅ Complete beginners to {sub}
✅ People who've tried before but got stuck
✅ Anyone who wants practical skills, not just theory
✅ People who learn by doing, not just reading

**Who this is NOT for:**
❌ Advanced practitioners looking for cutting-edge research
❌ People who want a one-size-fits-all magic solution

**Price:** ${price} — one-time purchase, instant download, keep forever.

**Guarantee:** 30-day money-back. If you're not satisfied for any reason, full refund. No questions asked.

---

### Short Description (for social media / ads, under 150 chars):

{name}: Master {sub} with this complete {ptype}. Templates, frameworks, practical. ${price} instant download.

---

### Meta Description (for blog/SEO, 155 chars max):

The best {sub} {ptype} for beginners. Step-by-step framework, real templates, practical examples. ${price} digital download. Instant access.

---

### Google/Meta Ad Headlines (30 chars max each):

1. {name[:30]}
2. Master {sub[:20]} Fast
3. {ptype.title()[:25]} Download
4. ${price} One-Time Access
5. {sub[:20]} Made Simple

---

### Google/Meta Ad Descriptions (90 chars max):

Primary: Get the complete {sub} {ptype}. Practical, actionable, beginner-friendly. ${price}.
Secondary: Stop struggling with {sub}. This {ptype} gives you the exact framework that works.

---
"""
    return desc


# ── メイン関数 ─────────────────────────────────────────────────────────────────

def generate_all(spec: dict, gumroad_url: str) -> dict:
    """
    1商品の全マーケティングコンテンツを生成して保存する。
    Returns: dict of file paths
    """
    pid       = spec["product_id"]
    mkt_dir   = PRODUCTS_DIR / pid / "marketing"
    mkt_dir.mkdir(parents=True, exist_ok=True)

    reddit = generate_reddit_post(spec, gumroad_url)
    thread = generate_twitter_thread(spec, gumroad_url)
    emails = generate_email_sequence(spec, gumroad_url)
    seo    = generate_seo_description(spec, gumroad_url)

    (mkt_dir / "reddit_post.md").write_text(reddit, encoding="utf-8")
    (mkt_dir / "twitter_thread.md").write_text(thread, encoding="utf-8")
    (mkt_dir / "email_sequence.md").write_text(emails, encoding="utf-8")
    (mkt_dir / "seo_copy.md").write_text(seo, encoding="utf-8")

    # サマリー JSON
    summary = {
        "product_id":   pid,
        "name":         spec["name"],
        "gumroad_url":  gumroad_url,
        "generated_at": datetime.now().isoformat(),
        "files": {
            "reddit":  str(mkt_dir / "reddit_post.md"),
            "twitter": str(mkt_dir / "twitter_thread.md"),
            "email":   str(mkt_dir / "email_sequence.md"),
            "seo":     str(mkt_dir / "seo_copy.md"),
        }
    }
    (mkt_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"[Traffic] マーケティングコンテンツ生成完了: {spec['name']}")
    return summary


def get_marketing_content(product_id: str) -> dict:
    """ダッシュボードから呼ぶ用 — 全コンテンツを返す"""
    mkt_dir = PRODUCTS_DIR / product_id / "marketing"
    if not mkt_dir.exists():
        return {}

    result = {}
    for key, fname in [("reddit", "reddit_post.md"), ("twitter", "twitter_thread.md"),
                       ("email", "email_sequence.md"), ("seo", "seo_copy.md")]:
        f = mkt_dir / fname
        if f.exists():
            result[key] = f.read_text(encoding="utf-8")
    return result


if __name__ == "__main__":
    # テスト実行
    test_spec = {
        "product_id": "test_traffic",
        "name": "Ultimate Budget Tracker",
        "category": "Finance",
        "subcategory": "Budget Tracker",
        "product_type": "spreadsheet_pack",
        "price_usd": 12,
    }
    generate_all(test_spec, "https://gumroad.com/l/example")
    print("生成完了 — products/test_traffic/marketing/ を確認してください")
