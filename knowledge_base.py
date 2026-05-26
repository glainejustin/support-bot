"""
KNOWLEDGE BASE - Edit this file to customize your bot's answers.

How to add a new question/answer:
  1. Add a new entry to the 'faqs' list below
  2. Each entry needs: "keywords" (words to trigger this answer), "question", "answer"
  3. Restart the bot

How it works:
  - When a customer types a message, the bot looks for matching keywords
  - It picks the best match and returns that answer
  - If nothing matches well, it says it'll connect to a human

Tip: Edit 'business_config.py' for business name, email, phone, promo code, etc.
     Those values are automatically used in the FAQ answers below.
"""

import difflib
import json
import os
import re
from business_config import PROMO_CODE, PROMO_DETAILS

# ─── PROMO CODE (auto-filled from business_config.py) ─────────────────────
_PROMO = f"**{PROMO_CODE}**" if PROMO_CODE else None
_PROMO_DETAILS = f" for {PROMO_DETAILS}" if PROMO_DETAILS else ""

# ─── CUSTOM FAQS FILE (added from admin dashboard) ─────────────────────────
CUSTOM_FAQS_FILE = os.path.join(os.path.dirname(__file__), "custom_faqs.json")


def load_custom_faqs():
    """Load custom FAQs added from the admin dashboard."""
    if not os.path.exists(CUSTOM_FAQS_FILE):
        return []
    try:
        with open(CUSTOM_FAQS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_custom_faqs(custom_faqs):
    """Save custom FAQs to the JSON file."""
    with open(CUSTOM_FAQS_FILE, "w") as f:
        json.dump(custom_faqs, f, indent=2)


def get_all_faqs():
    """Return built-in FAQs merged with custom FAQs."""
    return faqs + load_custom_faqs()


# ─── EDIT YOUR FAQS HERE ────────────────────────────────────────────────────

faqs = [
    # ── PRICING & PLANS ────────────────────────────────────────────────────
    {
        "keywords": ["pricing", "price", "cost", "how much", "plan", "plans", "tier", "subscription"],
        "question": "What are your pricing plans?",
        "answer": (
            "We have three plans:\n\n"
            "🚀 **Starter** — $19/month\n"
            "  • Up to 1,000 contacts\n"
            "  • Core features\n"
            "  • Email support\n\n"
            "💼 **Professional** — $49/month\n"
            "  • Up to 10,000 contacts\n"
            "  • Advanced features + automations\n"
            "  • Priority chat support\n\n"
            "🏢 **Enterprise** — Custom pricing\n"
            "  • Unlimited contacts\n"
            "  • Dedicated account manager\n"
            "  • Custom integrations + SLA\n\n"
            "All plans include a **14-day free trial** — no credit card required! 🎉"
        ),
    },
    {
        "keywords": ["free trial", "trial", "try", "demo", "sample", "test"],
        "question": "How do I start a free trial?",
        "answer": (
            "You can start a **14-day free trial** right now at **app.example.com/signup**\n\n"
            "✅ No credit card needed\n"
            "✅ Full access to all features\n"
            "✅ No commitment — cancel anytime\n\n"
            "Want a guided tour? I can walk you through the setup!"
        ),
    },
    {
        "keywords": ["discount", "coupon", "promo", "deal", "offer", "student"],
        "question": "Are there any discounts available?",
        "answer": (
            "Here are current discounts:\n\n"
            "🎓 **Students** — 50% off with a valid .edu email\n"
            "💼 **Non-profits** — Special pricing, contact us for details\n"
            "📢 **Annual billing** — Save 20% when you pay yearly\n"
            "👥 **Referrals** — Get 1 month free for every friend who signs up\n\n"
            f"Use code {_PROMO}{_PROMO_DETAILS}!" if _PROMO else ""
        ),
    },

    # ── FEATURES & CAPABILITIES ───────────────────────────────────────────
    {
        "keywords": ["features", "what does it do", "capabilities", "can it", "functions"],
        "question": "What features does your app offer?",
        "answer": (
            "Here are our core features:\n\n"
            "📊 **Analytics Dashboard** — Real-time insights and reports\n"
            "🤖 **Automations** — Build workflows without code\n"
            "🔗 **Integrations** — Connect with 100+ tools\n"
            "📧 **Email Campaigns** — Design and send newsletters\n"
            "👥 **Team Collaboration** — Invite your whole team\n"
            "📱 **Mobile App** — Manage on the go\n"
            "🔒 **SSO & 2FA** — Enterprise-grade security\n\n"
            "Which one would you like to learn more about?"
        ),
    },
    {
        "keywords": ["automation", "workflow", "auto", "trigger", "zap"],
        "question": "How do automations work?",
        "answer": (
            "Our no-code automation builder lets you create workflows in minutes:\n\n"
            "1. Choose a **trigger** (e.g., 'New user signs up')\n"
            "2. Add **conditions** (e.g., 'If plan = free')\n"
            "3. Set **actions** (e.g., 'Send welcome email')\n\n"
            "**Example workflows:**\n"
            "• Welcome series for new users\n"
            "• Re-engage inactive customers\n"
            "• Alert your team on high-value signups\n\n"
            "Want me to help you set one up?"
        ),
    },
    {
        "keywords": ["analytics", "report", "dashboard", "metrics", "insights"],
        "question": "What kind of analytics do you provide?",
        "answer": (
            "Our analytics dashboard gives you:\n\n"
            "📈 **Real-time metrics** — Active users, revenue, conversion rates\n"
            "📊 **Custom reports** — Build any report you need\n"
            "🎯 **Cohort analysis** — Understand user behavior over time\n"
            "📉 **Churn tracking** — See who's leaving and why\n"
            "📤 **Export** — Download as CSV, PDF, or connect to your BI tool\n\n"
            "Professional plan and above includes **custom dashboard widgets**."
        ),
    },

    # ── ACCOUNT & SETUP ───────────────────────────────────────────────────
    {
        "keywords": ["sign up", "signup", "register", "create account", "get started", "onboarding"],
        "question": "How do I create an account?",
        "answer": (
            "Getting started is easy:\n\n"
            "1. Go to **app.example.com/signup**\n"
            "2. Enter your email and create a password\n"
            "3. Verify your email\n"
            "4. Follow the 3-minute onboarding wizard\n\n"
            "You'll be up and running in under 5 minutes! 🚀\n\n"
            "Need help with setup? Just ask!"
        ),
    },
    {
        "keywords": ["password", "login", "sign in", "can't log", "forgot", "reset password"],
        "question": "How do I reset my password?",
        "answer": (
            "To reset your password:\n\n"
            "1. Go to **app.example.com/reset**\n"
            "2. Enter your email address\n"
            "3. Check your inbox for a reset link (check spam too!)\n"
            "4. Click the link and create a new password\n\n"
            "Still having trouble? Reply 'RESET HELP' and a human will assist you."
        ),
    },
    {
        "keywords": ["team", "invite", "add user", "member", "collaborator", "role", "permissions"],
        "question": "How do I add team members?",
        "answer": (
            "To invite team members:\n\n"
            "1. Go to **Settings > Team**\n"
            "2. Click **'Invite Member'**\n"
            "3. Enter their email and choose a role:\n"
            "   • **Admin** — Full access\n"
            "   • **Editor** — Can create and edit\n"
            "   • **Viewer** — Read-only access\n"
            "4. They'll get an invite email\n\n"
            "You can have up to 5 team members on Professional, unlimited on Enterprise."
        ),
    },
    {
        "keywords": ["delete account", "close account", "remove account"],
        "question": "How do I delete my account?",
        "answer": (
            "We're sorry to see you go! 😢\n\n"
            "To delete your account:\n"
            "1. Go to **Settings > Account > Delete Account**\n"
            "2. Confirm your choice\n"
            "3. Your data will be permanently deleted within 48 hours\n\n"
            "**Before you go:** Would you like me to help with any issues?\n"
            "Maybe I can help resolve what's bothering you!"
        ),
    },

    # ── BILLING & PAYMENTS ────────────────────────────────────────────────
    {
        "keywords": ["billing", "invoice", "receipt", "payment", "charge", "bill", "paid"],
        "question": "How does billing work?",
        "answer": (
            "Here's how billing works:\n\n"
            "💳 **Payment methods** — Credit card (Visa, MC, Amex) or PayPal\n"
            "📅 **Billing cycle** — Monthly or yearly (save 20% with annual)\n"
            "🧾 **Invoices** — Available in **Settings > Billing > Invoices**\n"
            "🔄 **Upgrade/Downgrade** — Changes take effect immediately\n"
            "📉 **Proration** — You only pay for what you use\n\n"
            "Need to update your payment method or view past invoices? Just ask!"
        ),
    },
    {
        "keywords": ["refund", "money back", "guarantee", "cancel subscription"],
        "question": "What's your refund policy?",
        "answer": (
            "We offer a **30-day money-back guarantee** on all plans!\n\n"
            "✅ Full refund within 30 days of purchase — no questions asked\n"
            "✅ Prorated refund if you cancel mid-cycle\n"
            "✅ No cancellation fees\n\n"
            "To request a refund: **Settings > Billing > Request Refund**\n\n"
            "Fun fact: 95% of our customers never ask for one because they love the product! 😊"
        ),
    },
    {
        "keywords": ["upgrade", "downgrade", "change plan", "switch plan"],
        "question": "How do I upgrade or downgrade my plan?",
        "answer": (
            "You can change your plan anytime:\n\n"
            "**To upgrade:**\n"
            "• Go to **Settings > Billing > Change Plan**\n"
            "• New features available immediately\n"
            "• You'll be charged the prorated difference\n\n"
            "**To downgrade:**\n"
            "• Go to **Settings > Billing > Change Plan**\n"
            "• New plan takes effect at next billing cycle\n"
            "• Make sure you won't exceed the new plan's limits!\n\n"
            "Need help picking the right plan? Tell me about your needs!"
        ),
    },

    # ── INTEGRATIONS & API ────────────────────────────────────────────────
    {
        "keywords": ["integration", "integrate", "connect", "sync", "api"],
        "question": "What integrations do you support?",
        "answer": (
            "We integrate with 100+ tools! Here are the most popular:\n\n"
            "📧 **Email** — Gmail, Outlook, Mailchimp\n"
            "📊 **CRM** — Salesforce, HubSpot, Pipedrive\n"
            "💬 **Chat** — Slack, Teams, Discord\n"
            "📅 **Calendar** — Google Calendar, Outlook Calendar\n"
            "🔧 **Dev Tools** — GitHub, GitLab, Jira, Notion\n"
            "🛒 **E-commerce** — Shopify, WooCommerce\n"
            "📈 **Analytics** — Google Analytics, Mixpanel\n\n"
            "Need a specific integration? We have a public API too!"
        ),
    },
    {
        "keywords": ["api", "developer", "webhook", "sdk", "rest", "graphql"],
        "question": "How do I use your API?",
        "answer": (
            "Our API lets you build custom integrations!\n\n"
            "📖 **Documentation:** **docs.example.com/api**\n"
            "🔑 **API Keys:** Generate at **Settings > Developer > API Keys**\n"
            "📦 **SDKs available for:** Python, JavaScript, Ruby, Go, PHP\n"
            "🔗 **Webhooks:** Receive real-time events\n"
            "📊 **Rate limit:** 1,000 requests/minute on Professional\n\n"
            "**Quick start:**\n"
            "```\n"
            "curl -H 'Authorization: Bearer YOUR_API_KEY' \\\n"
            "  https://api.example.com/v1/users\n"
            "```\n\n"
            "Want me to send you the API docs?"
        ),
    },
    {
        "keywords": ["migration", "import", "transfer", "move from", "switch from"],
        "question": "Can I migrate from another platform?",
        "answer": (
            "Absolutely! We make migration easy:\n\n"
            "📥 **Import tools** — CSV, JSON, or direct API import\n"
            "🔄 **Automated migration** — For supported platforms\n"
            "👨‍🔧 **Concierge migration** — Enterprise plan includes white-glove service\n"
            "✅ **Data validation** — We verify everything migrated correctly\n\n"
            "**Supported imports from:** HubSpot, Mailchimp, ActiveCampaign, ConvertKit, and more.\n\n"
            "Typical migration takes **under 1 hour**. Want to get started?"
        ),
    },

    # ── SUPPORT & HELP ────────────────────────────────────────────────────
    {
        "keywords": ["support", "help", "contact", "chat", "live chat", "help center"],
        "question": "How do I get support?",
        "answer": (
            "We're here to help! Here's how to reach us:\n\n"
            "💬 **Live chat** — Right here! Available 24/5\n"
            "📧 **Email** — **support@example.com** (reply within 2 hours)\n"
            "📚 **Knowledge base** — **help.example.com** (self-serve guides)\n"
            "🎓 **Academy** — **academy.example.com** (video tutorials)\n"
            "💬 **Community** — **community.example.com** (talk to other users)\n\n"
            "**Response times:**\n"
            "• Starter: Within 24 hours (email only)\n"
            "• Professional: Within 4 hours (chat + email)\n"
            "• Enterprise: 1-hour SLA with dedicated support manager"
        ),
    },
    {
        "keywords": ["status", "downtime", "outage", "down", "not working", "error", "bug"],
        "question": "Is there an outage right now?",
        "answer": (
            "Check our live system status at **status.example.com** 🟢\n\n"
            "**Current status:** All systems operational\n\n"
            "📊 **99.99% uptime** guaranteed for Enterprise plans\n"
            "🔔 **Subscribe** to status alerts at status.example.com\n"
            "📋 **Incident reports** — Full transparency on past incidents\n\n"
            "If you're experiencing a specific issue, please describe it and I'll help troubleshoot!"
        ),
    },
    {
        "keywords": ["tutorial", "guide", "how to", "walkthrough", "training", "onboarding"],
        "question": "Where can I find tutorials?",
        "answer": (
            "We have a full learning center for you:\n\n"
            "🎓 **Academy** — **academy.example.com**\n"
            "  • Getting Started (5 min)\n"
            "  • Advanced Automations (20 min)\n"
            "  • Master Class (60 min)\n\n"
            "📚 **Knowledge Base** — **help.example.com**\n"
            "  • Step-by-step guides\n"
            "  • Video walkthroughs\n"
            "  • Best practices\n\n"
            "🎥 **YouTube Channel** — youtube.com/@example\n"
            "  • Weekly tips & tricks\n"
            "  • Feature deep dives\n\n"
            "What do you want to learn about?"
        ),
    },

    # ── SECURITY & COMPLIANCE ─────────────────────────────────────────────
    {
        "keywords": ["security", "data", "privacy", "gdpr", "soc2", "encryption", "safe", "secure"],
        "question": "How do you protect my data?",
        "answer": (
            "Security is our top priority. Here's what we do:\n\n"
            "🔒 **Encryption** — AES-256 at rest, TLS 1.3 in transit\n"
            "✅ **SOC 2 Type II** — Certified annually\n"
            "🇪🇺 **GDPR Compliant** — Full data portability\n"
            "🌍 **Data centers** — US, EU, and APAC regions\n"
            "🔐 **SSO/SAML** — Enterprise-grade authentication\n"
            "📋 **Audit logs** — Complete activity history\n"
            "🔄 **Backups** — Daily automated backups with 30-day retention\n\n"
            "Want to see our full security documentation? Visit **security.example.com**"
        ),
    },
    {
        "keywords": ["export", "download data", "backup", "extract", "csv"],
        "question": "How do I export my data?",
        "answer": (
            "You own your data — and you can export it anytime:\n\n"
            "📤 **Export options:**\n"
            "  • **CSV** — For spreadsheets\n"
            "  • **JSON** — For developers\n"
            "  • **PDF** — For reports\n"
            "  • **API** — Programmatic access\n\n"
            "**How to export:**\n"
            "  Go to **Settings > Data > Export**\n\n"
            "**What's included:**\n"
            "  • All your contacts and segments\n"
            "  • Campaign history and analytics\n"
            "  • Automation workflows\n"
            "  • Custom reports\n\n"
            "Exports are typically ready within 5 minutes!"
        ),
    },

    # ── GENERAL / POLITE ──────────────────────────────────────────────────
    {
        "keywords": ["hello", "hi", "hey", "good morning", "good evening", "yo", "sup"],
        "question": "Greeting",
        "answer": (
            "Hey there! 👋 Welcome to ExampleApp support!\n\n"
            "I can help you with:\n"
            "🚀 **Getting started** — Setup, onboarding, tutorials\n"
            "💳 **Billing** — Plans, invoices, refunds\n"
            "🔧 **Technical** — API, integrations, troubleshooting\n"
            "👥 **Account** — Team, settings, security\n\n"
            "What can I help you with today?"
        ),
    },
    {
        "keywords": ["thanks", "thank you", "appreciate", "awesome", "great"],
        "question": "Thank you",
        "answer": (
            "You're welcome! 😊 Happy to help!\n\n"
            "Is there anything else I can assist you with?\n"
            "If not, have a productive day! 🚀"
        ),
    },
    {
        "keywords": ["bye", "goodbye", "see you", "later", "take care"],
        "question": "Goodbye",
        "answer": (
            "Take care! 👋 If you ever need help, just come back and chat.\n\n"
            "**Quick links:**\n"
            "📚 Knowledge base — help.example.com\n"
            "🎓 Academy — academy.example.com\n"
            "💬 Community — community.example.com\n\n"
            "Have an awesome day! 🚀"
        ),
    },
    {
        "keywords": ["human", "agent", "real person", "manager", "representative", "speak to"],
        "question": "Talk to a human",
        "answer": (
            "I'll connect you with a human agent right away! 🧑‍💼\n\n"
            "While you wait, here's how to reach us directly:\n"
            "📧 **Email:** **support@example.com**\n"
            "📞 **Phone:** **1-800-555-EXAMPLE** (Mon-Fri, 9-6 EST)\n"
            "💬 **Live chat:** Available during business hours\n\n"
            "A real person will be with you shortly!"
        ),
    },
    {
        "keywords": ["help", "menu", "options", "what can you do", "commands"],
        "question": "Help menu",
        "answer": (
            "Here's everything I can help with:\n\n"
            "💰 **Pricing & Plans** — Costs, trials, discounts\n"
            "⚙️ **Features** — Automations, analytics, integrations\n"
            "👤 **Account** — Login, team, settings, security\n"
            "💳 **Billing** — Invoices, refunds, upgrades\n"
            "🔗 **Integrations & API** — Connect your tools\n"
            "❓ **Troubleshooting** — Errors, outages, bugs\n"
            "📚 **Learning** — Tutorials, guides, academy\n\n"
            "Just type your question! Or say **'human'** to talk to a real person."
        ),
    },
]

# ─── MATCHING LOGIC (no need to edit below) ────────────────────────────────


_FOLLOW_UP_MAP = {
    # Map topic keywords to related FAQ questions for follow-up suggestions
    "pricing": ["free trial", "discount", "upgrade"],
    "plan": ["pricing", "features", "billing"],
    "trial": ["pricing", "features", "get started"],
    "feature": ["automation", "analytics", "integration"],
    "automation": ["features", "integration", "api"],
    "analytics": ["features", "export"],
    "account": ["password", "team", "delete account"],
    "login": ["password", "account"],
    "password": ["login", "account"],
    "team": ["account", "permissions"],
    "billing": ["pricing", "refund", "upgrade"],
    "invoice": ["billing", "payment"],
    "payment": ["billing", "invoice"],
    "refund": ["billing", "cancel"],
    "integration": ["api", "migration", "features"],
    "api": ["integration", "developer"],
    "migration": ["integration", "export"],
    "security": ["data", "privacy", "export"],
    "support": ["help", "contact", "human"],
    "help": ["support", "tutorial", "faq"],
    "tutorial": ["help", "get started"],
}

# Related FAQ question lookup by question text
_QUESTION_TO_KEYWORDS = {
    faq["question"]: faq["keywords"]
    for faq in faqs
}


def get_follow_up_suggestions(current_context):
    """
    Given the current conversation context (the last matched FAQ question),
    return suggested follow-up questions to help the user explore related topics.
    """
    if not current_context:
        return []

    # Find keywords associated with the current context
    context_keywords = _QUESTION_TO_KEYWORDS.get(current_context, [])

    # Collect related FAQ questions
    related = []
    seen = {current_context}
    for keyword in context_keywords:
        if keyword in _FOLLOW_UP_MAP:
            for related_keyword in _FOLLOW_UP_MAP[keyword]:
                # Find the FAQ that has this keyword
                for faq in faqs:
                    if related_keyword in faq["keywords"] and faq["question"] not in seen:
                        related.append(faq["question"])
                        seen.add(faq["question"])
                        break

    return related[:3]  # Max 3 suggestions


def find_best_match(user_message, context=None):
    """
    Find the best FAQ match for a user's message.
    Uses fuzzy matching so misspellings still work.
    Optionally takes a context (last matched question) to boost related FAQs.
    Returns the FAQ entry or None if no good match.
    """
    if not user_message:
        return None

    message_lower = user_message.lower().strip()
    all_faqs = get_all_faqs()

    # Score each FAQ by how well its keywords match
    best_score = 0
    best_match = None

    for faq in all_faqs:
        for keyword in faq["keywords"]:
            # Check if keyword is directly in the message
            if keyword.lower() in message_lower:
                score = len(keyword)  # Longer keyword match = better
                if score > best_score:
                    best_score = score
                    best_match = faq
            else:
                # Fuzzy match: how similar is the keyword to parts of the message?
                words = re.findall(r'\w+', message_lower)
                for word in words:
                    ratio = difflib.SequenceMatcher(None, keyword.lower(), word).ratio()
                    if ratio > 0.8:  # 80% similarity threshold
                        score = ratio * len(keyword)
                        if score > best_score:
                            best_score = score
                            best_match = faq

    # Boost score if this FAQ relates to the conversation context
    if context and best_match:
        context_keywords = _QUESTION_TO_KEYWORDS.get(context, [])
        # Also check custom FAQs for context keywords
        for cf in all_faqs:
            if cf.get("question") == context:
                context_keywords = cf.get("keywords", [])
                break
        if any(kw in context_keywords for kw in best_match["keywords"]):
            best_score *= 1.3  # 30% boost for contextually relevant FAQs

    # Only return if the match is good enough
    # Use a lower threshold (2) so short greetings like "hi" also match
    if best_score >= 2:
        return best_match
    return None
