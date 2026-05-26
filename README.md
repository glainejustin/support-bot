<div align="center">
  <h1>🤖 SaaS Support Bot</h1>
  <p><strong>24/7 AI-powered customer support chatbot — deploy in 5 minutes, free</strong></p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-demo">Demo</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-multi-language">Multi-Language</a> •
    <a href="#-live-agent-handoff">Handoff</a> •
    <a href="#-conversation-analytics">Analytics</a> •
    <a href="#-faq-training">FAQ Training</a> •
    <a href="#-deployment">Deployment</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit" alt="Streamlit">
    <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/Resend-Email-000000?logo=resend" alt="Resend">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

---

## 📋 Overview

A fully-featured, **white-label customer support chatbot** for SaaS businesses. Answers FAQs in any language, captures leads, sends automated follow-up emails, provides an admin dashboard with analytics, live agent handoff, and FAQ training — all running 24/7 on Streamlit Cloud for **free**.

Every business gets their own copy. Just fork, edit one config file, and deploy.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **24/7 Automated Support** | Instantly answers customer questions about pricing, features, billing, account management, integrations, and more |
| 🧠 **Fuzzy Matching** | Understands typos, misspellings, and similar phrasing — not just exact keywords |
| 🌐 **Multi-Language** | Auto-detects the user's language and responds in their native tongue (40+ languages) |
| 🤝 **Live Agent Handoff** | When the bot can't answer, an admin can pick up the conversation from the dashboard |
| 📊 **Conversation Analytics** | Track resolution rates, popular questions, daily activity, feedback, and language distribution |
| 🧠 **FAQ Training** | Add new FAQs directly from the admin dashboard — no code or restart needed |
| 🏢 **White-Label Branding** | Customize company name, colors, tagline, and bot avatar in one config file |
| 📬 **Lead Capture** | Automatically collects name, email, and phone when it can't answer a question |
| 📨 **Email Follow-ups** | Sends personalized follow-up emails via Resend (free, 3,000 emails/month) |
| 📋 **Admin Dashboard** | View leads, analytics, manage handoffs, train FAQs, mark as contacted/closed, export CSV |
| 🔔 **Webhook Alerts** | Send Slack/Discord notifications when new leads are captured |
| 👍 **Feedback Buttons** | Customers can thumbs-up/down responses to help improve your FAQ |
| 🔐 **Password-Protected Admin** | Secure admin panel with configurable password (supports env var override) |
| 🚀 **Free Hosting** | Deploy on Streamlit Cloud — 100% free, always on |

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/glainejustin/support-bot.git
cd support-bot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run locally

```bash
streamlit run bot.py
```

Open **http://localhost:8501** in your browser.

### 4. Customize for your business

Edit **`business_config.py`** — everything is in one place:

```python
BUSINESS_NAME = "Your Company Name"     # Appears everywhere
WEBSITE_URL = "https://yourcompany.com"
SUPPORT_EMAIL = "support@yourcompany.com"
PRIMARY_COLOR = "#0066cc"               # Brand color
ADMIN_PASSWORD = "your-secure-password"  # 🔐 Change this!
```

Then edit **`knowledge_base.py`** with your real FAQ questions and answers.

### 5. Deploy to Streamlit Cloud (Free)

1. Push your repo to GitHub
2. Go to **[share.streamlit.io](https://share.streamlit.io)**
3. Sign in with GitHub → **New app**
4. Select your repo, branch `master`, main file `bot.py`
5. Click **Deploy!**

Your bot is live at: `https://your-username-support-bot.streamlit.app`

---

## 🌐 Multi-Language Support

The bot can **auto-detect** your customer's language and respond in their native tongue. No extra setup required.

### How it works

1. User types in their language (e.g., Spanish, French, Japanese)
2. `langdetect` detects the language automatically
3. `googletrans` translates the question to English for FAQ matching
4. The bot finds the best answer
5. The answer is translated back to the user's language

### Configuration

In `business_config.py`:

```python
ENABLE_TRANSLATION = True              # Set to False to disable
SUPPORTED_LANGUAGES = []               # Empty = allow all languages
# Or restrict to specific languages:
# SUPPORTED_LANGUAGES = ["en", "es", "fr", "de", "pt", "ja", "ko", "zh-cn"]
DEFAULT_LANGUAGE = "en"                # Fallback if detection fails
```

> **Note:** Translation requires `googletrans==4.0.0rc1` and `langdetect>=1.0.9` — both are in `requirements.txt`. The bot gracefully falls back to English if these aren't installed.

---

## 🤝 Live Agent Handoff

When the bot can't answer a question AND a lead is captured, the conversation is flagged for a human agent.

### How it works

1. Bot can't find a match → lead capture form appears
2. User submits their contact info → handoff request is created automatically
3. **Admin sidebar** → a "Handoffs" tab appears showing pending conversations
4. Admin types a response → it appears in the user's chat next time they interact
5. Admin can mark conversations as resolved when done

### Admin handoff dashboard

| Feature | Description |
|---|---|
| 🟡 **Pending** | New handoffs waiting for a response |
| 🔵 **Assigned** | Handoffs with an admin reply in progress |
| ✅ **Mark Resolved** | Close out resolved conversations |
| 📨 **Send Reply** | Type a response that the user will see in their chat |

### Configuration

```python
ENABLE_HANDOFF = True                  # Enable/disable live handoff
HANDOFF_MESSAGE = "A human agent will connect with you shortly! 🧑‍💼"
```

---

## 📊 Conversation Analytics

Track how your bot is performing with built-in analytics. Data persists across restarts in `analytics_data.json`.

### Metrics tracked

| Metric | Description |
|---|---|
| 💬 **Total Chats** | Number of conversations started |
| ✅ **Resolution Rate** | Percentage of questions answered successfully |
| 📈 **Daily Activity** | Chat and lead volume over the last 14 days |
| 🔥 **Top FAQs** | Most frequently matched questions |
| 👍/👎 **Feedback** | Thumbs up/down counts |
| 🌐 **Languages** | Distribution of detected languages |
| 📉 **Unmatched** | Questions the bot couldn't answer |
| 💼 **Lead Conversion** | Percentage of chats that resulted in a lead |

### Admin dashboard

- **Charts:** Daily activity bar chart, resolution trends
- **Export:** Download analytics as JSON
- **Reset:** Clear all analytics data

---

## 🧠 FAQ Training

Add new FAQs directly from the admin dashboard without editing code or restarting the bot.

### How it works

1. Navigate to the **Train FAQ** tab in the admin sidebar
2. Fill in:
   - **Question** — What the customer would ask (e.g., "Do you have a mobile app?")
   - **Keywords** — Comma-separated trigger words (e.g., "mobile app, ios, android, app")
   - **Answer** — Markdown-formatted response
3. Click **Add FAQ** — the bot learns it immediately!

### Managing FAQs

- View all custom FAQs in the admin panel
- Expand any FAQ to see details
- **Delete** individual FAQs with the delete button
- Built-in and custom FAQs are merged for matching

---

## 🔔 Webhook / Slack Alerts

Get notified when new leads are captured — works with Slack, Discord, or any webhook endpoint.

### Setup

In `business_config.py`:

```python
WEBHOOK_URL = "https://hooks.slack.com/services/..."  # Your webhook URL
WEBHOOK_TITLE = "New Lead Captured! 🎯"               # Custom message title
```

### What's sent

The webhook receives a formatted message with:
- Customer name
- Email address
- Question (first 200 characters)
- Timestamp

---

## 🎨 Customization

### Business Config (`business_config.py`)

Everything is in one file:

| Setting | What it controls |
|---|---|
| `BUSINESS_NAME` | Your company name in all bot responses |
| `BUSINESS_TAGLINE` | Short description shown in branding |
| `WEBSITE_URL` | Links in answers and follow-up emails |
| `SUPPORT_EMAIL` | Contact email shown to customers |
| `SUPPORT_PHONE` | Phone number shown to customers |
| `SUPPORT_HOURS` | Business hours displayed in responses |
| `PRIMARY_COLOR` | Brand color for buttons and accents |
| `BOT_AVATAR` | Emoji icon for the bot |
| `PROMO_CODE` | Promo code injected into discount answers |

### Feature Toggles

All in `business_config.py`:

| Setting | Default | What it does |
|---|---|---|
| `ENABLE_TRANSLATION` | `True` | Multi-language auto-detect & translate |
| `ENABLE_HANDOFF` | `True` | Live agent handoff system |
| `WEBHOOK_URL` | `""` | Webhook URL (empty = disabled) |
| `CAPTURE_LEADS` | `True` | Show lead capture form |
| `AUTO_SEND_EMAIL` | `True` | Auto-send follow-up emails |

### Knowledge Base (`knowledge_base.py`)

Edit the FAQ answers directly:

```python
faqs = [
    {
        "keywords": ["pricing", "cost", "plans"],
        "question": "What are your pricing plans?",
        "answer": "We have three plans: ..."
    },
    # Add as many as you want!
]
```

The fuzzy matching engine automatically handles typos and similar phrasing.

---

## 📬 Lead Capture

When the bot can't answer a customer's question, it gracefully offers to connect them with a human and **captures their contact information**:

- Automatically shows a lead capture form
- Collects name, email (required), phone, company (optional)
- Stores leads persistently in `leads.json`
- All configurable in `business_config.py`

You can also configure it to **auto-send a follow-up email** immediately after capture (see Email Follow-ups below).

---

## 📨 Email Follow-ups

Send automated follow-up emails to captured leads using **Resend** (free tier: 3,000 emails/month).

### Setup

1. Sign up at **[resend.com](https://resend.com)** (free)
2. Create an API key in your dashboard
3. Add it to `.streamlit/secrets.toml`:

```toml
[resend]
api_key = "re_your_api_key_here"
```

Or set as an environment variable:

```bash
export RESEND_API_KEY="re_your_api_key_here"
```

4. Customize the email template in `business_config.py`:

```python
EMAIL_FROM = "onboarding@resend.dev"
AUTO_SEND_EMAIL = True
FOLLOW_UP_SUBJECT = "Thanks for chatting with {name}! 🙌"
```

> **⚠️ Streamlit Cloud:** Paste your secrets in **Settings → Secrets** instead of committing the file.

---

## 📊 Admin Dashboard

Access the admin panel from the **sidebar** → enter your admin password:

### Lead Management

| Feature | What it does |
|---|---|
| 👁️ **View all leads** | Name, email, phone, question, timestamp, status |
| ✅ **Mark contacted** | Track which leads you've followed up with |
| ❌ **Mark closed** | Close out resolved leads |
| 📝 **Add notes** | Internal notes per lead |
| 📧 **Send email** | Manually trigger a follow-up email to any lead |
| 📥 **Export CSV** | Download all leads for your CRM |
| 🗑️ **Clear all** | Reset leads (with confirmation) |

### Analytics Dashboard

| Feature | What it does |
|---|---|
| 📈 **Daily Charts** | 14-day activity overview bar charts |
| ✅ **Resolution Rate** | Percentage of questions answered successfully |
| 🔥 **Top FAQs** | Most frequently matched questions |
| 🌐 **Language Distribution** | Which languages your customers use |
| 📥 **Export JSON** | Download analytics data |

### Handoff Management

| Feature | What it does |
|---|---|
| 🤝 **Pending Handoffs** | Conversations awaiting agent response |
| 📨 **Send Reply** | Respond to customers directly from dashboard |
| ✅ **Mark Resolved** | Close completed handoffs |
| 💬 **Conversation View** | Full message history per handoff |

### FAQ Training

| Feature | What it does |
|---|---|
| ➕ **Add FAQ** | New question/keywords/answer — instantly learned |
| 🗑️ **Delete FAQ** | Remove custom FAQs |
| 📚 **View All FAQs** | Both built-in and custom FAQs merged |

---

## 🧠 How It Works

1. **Customer messages the bot** in the chat interface
2. **Language detection** (if enabled) → translates to English
3. **Fuzzy matching engine** compares their message against all FAQ keywords (built-in + custom) using similarity scoring
4. **Best match found** → bot responds with the answer (translated back if needed)
5. **No match found** → bot shows a lead capture form
6. **Lead captured** → stored in `leads.json` + optional auto email + webhook alert + handoff request
7. **Admin** views/manages leads, analytics, handoffs, and trains FAQs from the sidebar dashboard

---

## 📁 Project Structure

```
support-bot/
├── bot.py                 # Main app — Streamlit chat interface + admin dashboard
├── business_config.py     # ✏️ EDIT THIS — One file to customize everything
├── knowledge_base.py      # ✏️ EDIT THIS — Your FAQ questions and answers
├── leads_manager.py       # Lead storage, retrieval, CSV export
├── email_sender.py        # Resend email integration
├── analytics.py           # 📊 Conversation analytics tracking
├── requirements.txt       # Python dependencies
├── .streamlit/
│   ├── config.toml        # Streamlit theme and server config
│   └── secrets.toml       # 🔐 API keys (gitignored — don't commit!)
├── leads.json             # 📁 Captured leads (gitignored)
├── handoff_messages.json  # 📁 Handoff conversations (gitignored)
├── custom_faqs.json       # 📁 Admin-added FAQs (gitignored)
├── analytics_data.json    # 📁 Analytics metrics (gitignored)
├── .env.example           # 🔐 Environment variable reference
├── SECURITY.md            # Security audit report
└── .gitignore
```

---

## 🔧 Tech Stack

- **[Streamlit](https://streamlit.io/)** — Python web framework (free hosting)
- **[Resend](https://resend.com/)** — Email API (free tier: 3,000 emails/month)
- **[googletrans](https://pypi.org/project/googletrans/)** — Free translation API
- **[langdetect](https://pypi.org/project/langdetect/)** — Language detection library
- **[Python](https://python.org/)** — Core logic

No HTML, CSS, JavaScript, or database setup required.

---

## 🤝 Contributing

This is a template intended for any SaaS business to clone and customize. Feel free to:

- Open issues for feature requests
- Submit PRs for improvements
- Fork and make it your own!

---

## 📄 License

MIT — use it for any business, personal or commercial.

---

<div align="center">
  <p>Built with ❤️ for SaaS businesses everywhere</p>
  <p>
    <a href="https://share.streamlit.io">🚀 Deploy on Streamlit Cloud</a> •
    <a href="https://resend.com">📨 Resend for Email</a>
  </p>
</div>
