# 🏭 Gumroad Product Factory

**Create → Sell → Scale - Fully Automated**

A complete system for creating and selling digital products on Gumroad.

---

## 🚀 Key Features

- **Market Research**: AI-powered trend analysis with **learning from feedback**
- **Product Creation**: Auto-generate eBooks, templates, toolkits in English
- **Gumroad Integration**: API-based product publishing & file upload
- **Social Content**: Auto-generate Pinterest & Twitter posts
- **Pinterest API**: Auto-pin products directly from the factory
- **GitHub Actions**: Daily automated product creation at 9 AM JST
- **Dashboard**: Server-free product management with social content generator
- **Feedback Learning**: System gets smarter by learning from your approve/reject decisions

---

## ⚠️ Important

This is a **factory for creating products** - not a product to sell itself. The products created by this factory are what you sell on Gumroad.

---

## 📦 Setup

### 1. Install Dependencies
```bash
cd gumroad.auto
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
# Edit .env with your API keys
```

Required keys:
- `GUMROAD_ACCESS_TOKEN`: From [Gumroad Settings](https://app.gumroad.com/settings/advanced)
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`: For content generation

Optional keys (for Pinterest automation):
- `PINTEREST_APP_ID`: From [Pinterest Developers](https://developers.pinterest.com/)
- `PINTEREST_APP_SECRET`: From Pinterest Developers
- `PINTEREST_ACCESS_TOKEN`: OAuth2 access token
- `PINTEREST_BOARD_ID`: Board ID to post pins to

---

## 💡 Usage

### Quick Start - One Command
```bash
source venv/bin/activate
python run_workflow.py
```
This creates 5 products + social content in one go!

### Manual Options
```bash
# Create 1 product
python main.py

# Create 5 products
python main.py --count 5

# Create product AND publish to Gumroad (draft mode)
python main.py --publish

# Generate social content only
python social_content_generator.py

# Pin to Pinterest (interactive)
python pin_to_pinterest.py

# Test Pinterest API connection
python pinterest_client.py
```

### Admin Dashboard (Two Versions)

#### Version 1: Simple (No Server)
Open `admin_dashboard_simple.html` in your browser:
- Load products from the `products/` folder
- Approve/Reject products **with feedback**
- Copy social media content (Pinterest & Twitter)
- Track product status locally
- **Export feedback data** to help the system learn

#### Version 2: Server (Auto-Publish to Gumroad)
**ONE-CLICK PUBLISHING + PWA for iPhone!**

1. **Install dependencies first**:
   ```bash
   pip install Flask flask-cors
   ```

2. **Start the server**:
   ```bash
   python local_server.py
   ```

3. **Open dashboard**: 
   - On your Mac/PC: Go to **http://localhost:8001**
   - On your iPhone: Connect to same Wi-Fi, go to **http://[YOUR_MAC_IP]:8001**

4. **Add to iPhone Home Screen**:
   - Open in Safari
   - Tap the share button ↗️
   - Tap "Add to Home Screen"
   - Now you can open it like an app!

5. **Approve & Publish**: Click "✅ Approve & Publish" to auto-publish directly to Gumroad!

Features:
- One-click Gumroad publishing
- Auto-saves feedback to `system/feedback/`
- Real-time server status check
- Shows learning insights
- **PWA support for iPhone home screen
- High-converting product descriptions

### Feedback Learning (How It Works)
The system gets smarter over time by learning what the market wants:

1. **Approve/Reject with Reason**: In the dashboard, select why you're approving/rejecting a product (based on market fit)
2. **Export Feedback**: Click "Export Feedback Data" in the dashboard
3. **Save Feedback**: Put the exported `product_feedback.json` in `system/feedback/`
4. **System Learns**: Next time you run `python main.py`, the system will:
   - Prioritize categories that the market likes (based on your approval)
   - Avoid categories that the market doesn't want (based on your rejection)
   - Adjust trend scores to match market demand

Check feedback summary:
```bash
python feedback_tracker.py --summary
```

---

## 📌 Pinterest Automation Setup

### Get Your Credentials
1. Go to [developers.pinterest.com](https://developers.pinterest.com/)
2. Create a new app (App name, description, website URL)
3. Get your `App ID` and `App Secret`
4. Generate an access token using OAuth2 flow

### Quick OAuth Flow
```python
# Use this URL in your browser (replace YOUR_APP_ID):
https://www.pinterest.com/oauth/?client_id=YOUR_APP_ID&redirect_uri=https://httpstat.us/200&response_type=code&scope=boards:read,boards:write,pins:read,pins:write
```

After authorizing, copy the `code` from the URL and exchange it for an access token.

---

## 🔄 GitHub Actions - Daily Automation

### What it does
- Runs **every morning at 9 AM JST**
- Creates 5 products automatically
- Generates social media content
- Commits changes to Git

### Setup (One Time)
1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets (copy from `.env`):
   - `ANTHROPIC_API_KEY`
   - `OPENAI_API_KEY`
   - `GUMROAD_ACCESS_TOKEN`

That's it! The workflow runs automatically every day.

Detailed guide: [GITHUB_SETUP.md](./GITHUB_SETUP.md)

---

## 📊 The $1000+/month Plan

| Metric | Target |
|--------|--------|
| Products/Month | 150 (5/day) |
| Pinterest Pins | 300 (10/day) |
| Avg Price | $15 |
| Conversion | 2% |
| Sales/Month | 67 |
| **Revenue/Month** | **$1000+ (~¥150,000)** |

---

## 📱 Social Media Strategy

### Pinterest (#1 Priority)
- **Tools**: Canva (free) + Pinterest API (optional)
- **Frequency**: 5-10 pins/day
- **Focus**: Visual pins with value-first descriptions
- **Automation**: Use `pin_to_pinterest.py` for API-based posting

### Twitter/X (Secondary)
- **Frequency**: 2-3 tweets/day
- **Rule**: 70% value, 30% promotion
- **Why**: API is expensive ($200/month+) - semi-automated is safer

### Reddit (Tertiary)
- **Frequency**: 1-2 posts/week
- **Rule**: 80% value, 20% promotion
- **Best**: r/sidehustle, r/passive_income, r/indiehackers

---

## 📁 Project Structure

```
gumroad.auto/
├── main.py                      # Product factory main script (with learning!)
├── run_workflow.py              # One-click: 5 products + social content
├── local_server.py              # Local server for auto-publishing
├── gumroad_uploader.py          # Gumroad API integration
├── social_content_generator.py  # Pinterest & Twitter content
├── pinterest_client.py          # Pinterest API client
├── pin_to_pinterest.py          # Interactive pinning script
├── feedback_tracker.py          # Feedback learning system
├── global_marketing.py          # Global marketing strategy
├── admin_dashboard_simple.html  # Server-free admin dashboard
├── admin_dashboard_server.html  # Server version (auto-publish)
├── requirements.txt             # Dependencies
├── .env.example                 # API keys template
├── .env                         # Your API keys (don't commit!)
├── GITHUB_SETUP.md              # GitHub Actions guide
├── SOCIAL_STRATEGY.md           # Detailed social media guide
├── QUICKSTART.md                # Quick start guide
├── products/                    # Created products
├── social_content/              # Generated social posts
├── marketing_strategies/        # Marketing plans
├── production_assets/           # Product assets
└── system/
    ├── data/                    # Market data
    ├── feedback/                # Feedback learning data
    ├── reports/                 # Run reports
    ├── scripts/                 # Utility scripts
    └── prompts/                 # AI prompts
```

---

## ✅ What's Working Now

1. ✅ **Product Creation**: AI-powered product generation
2. ✅ **Gumroad Integration**: API-based product publishing
3. ✅ **Social Content**: Pinterest & Twitter posts auto-generated
4. ✅ **Pinterest API**: Full API client for automated pinning
5. ✅ **Admin Dashboard**: Server-free product management
6. ✅ **GitHub Actions**: Daily automation workflow
7. ✅ **Price Fixed**: Uses correct cents units ($15 = 1500¢)
8. ✅ **Feedback Learning**: System learns from your approve/reject decisions

---

## 🎯 Daily Routine (30-60 mins)

1. **Morning (5 mins)**: Check GitHub Actions ran, or run `python run_workflow.py`
2. **Midday (10 mins)**: Open dashboard, review/approve products
3. **Afternoon (15 mins)**: Copy social content + pin to Pinterest
4. **Evening (10 mins)**: Check Gumroad sales, double down on winners

---

## 💡 Improvement Ideas

### Short-Term
- [ ] Add image generation (DALL-E/Stable Diffusion) for Pinterest pins
- [ ] Track which products sell best and prioritize similar topics
- [ ] Add A/B testing for product titles/descriptions
- [ ] Auto-refresh Pinterest access token

### Long-Term
- [ ] Add email marketing automation
- [ ] Create upsell funnels for existing customers
- [ ] Add analytics dashboard for sales tracking
- [ ] Multi-language support for global markets

---

## 📝 License

© 2025 AETERNA Holdings. All rights reserved.
