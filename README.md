<div align="center">
  <h1>🤖 SaaS Support Bot</h1>
  <p><strong>24/7 AI-powered customer support chatbot — deploy in 5 minutes, free</strong></p>
  <p>
    <a href="#-features">Features</a> •
    <a href="#-demo">Demo</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-customization">Customization</a> •
    <a href="#-lead-capture">Lead Capture</a> •
    <a href="#-email-follow-ups">Email Follow-ups</a> •
    <a href="#-admin-dashboard">Admin Dashboard</a> •
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

A fully-featured, **white-label customer support chatbot** for SaaS businesses. Answers FAQs, captures leads, sends automated follow-up emails, and provides an admin dashboard — all running 24/7 on Streamlit Cloud for **free**.

Every business gets their own copy. Just fork, edit one config file, and deploy.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **24/7 Automated Support** | Instantly answers customer questions about pricing, features, billing, account management, integrations, and more |
| 🧠 **Fuzzy Matching** | Understands typos, misspellings, and similar phrasing — not just exact keywords |
| 🏢 **White-Label Branding** | Customize company name, colors, tagline, and bot avatar in one config file |
| 📬 **Lead Capture** | Automatically collects name, email, and phone when it can't answer a question |
| 📨 **Email Follow-ups** | Sends personalized follow-up emails via Resend (free, 3,000 emails/month) |
| 📊 **Admin Dashboard** | View leads, mark as contacted/closed, add notes, export CSV |
| 👍 **Feedback Buttons** | Customers can thumbs-up/down responses to help improve your FAQ |
| 🔐 **Password-Protected Admin** | Secure admin panel with configurable password |
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

| Feature | What it does |
|---|---|
| 👁️ **View all leads** | Name, email, phone, question, timestamp, status |
| ✅ **Mark contacted** | Track which leads you've followed up with |
| ❌ **Mark closed** | Close out resolved leads |
| 📝 **Add notes** | Internal notes per lead |
| 📧 **Send email** | Manually trigger a follow-up email to any lead |
| 📥 **Export CSV** | Download all leads for your CRM |
| 🗑️ **Clear all** | Reset leads (with confirmation) |

---

## 🧠 How It Works

1. **Customer messages the bot** in the chat interface
2. **Fuzzy matching engine** compares their message against all FAQ keywords using similarity scoring
3. **Best match found** → bot responds with the answer
4. **No match found** → bot shows a lead capture form
5. **Lead captured** → stored in `leads.json` + optional auto email
6. **Admin** views/manages leads from the sidebar dashboard

---

## 📁 Project Structure

```
support-bot/
├── bot.py                 # Main app — Streamlit chat interface + admin dashboard
├── business_config.py     # ✏️ EDIT THIS — One file to customize everything
├── knowledge_base.py      # ✏️ EDIT THIS — Your FAQ questions and answers
├── leads_manager.py       # Lead storage, retrieval, CSV export
├── email_sender.py        # Resend email integration
├── requirements.txt       # Python dependencies
├── .streamlit/
│   ├── config.toml        # Streamlit theme and server config
│   └── secrets.toml       # 🔐 API keys (gitignored — don't commit!)
├── leads.json             # 📁 Captured leads (gitignored)
└── .gitignore
```

---

## 🔧 Tech Stack

- **[Streamlit](https://streamlit.io/)** — Python web framework (free hosting)
- **[Resend](https://resend.com/)** — Email API (free tier: 3,000 emails/month)
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
