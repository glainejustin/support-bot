"""
BUSINESS CONFIGURATION — Edit this file to customize the bot for YOUR business.

Every business gets their own copy. Just fill in your details below
and the bot will use them everywhere — answers, lead capture, branding, etc.
"""

# ─── YOUR BUSINESS INFO ─────────────────────────────────────────────────────

BUSINESS_NAME = "Your Business Name"          # e.g., "Acme Corp"
BUSINESS_TAGLINE = "We help you grow 🚀"      # Short description
WEBSITE_URL = "https://yourcompany.com"       # Your website
SUPPORT_EMAIL = "support@yourcompany.com"     # Support email
SUPPORT_PHONE = "1-800-555-0000"             # Support phone number
SUPPORT_HOURS = "Mon-Fri, 9 AM to 6 PM EST"  # Business hours

# ─── BRANDING ───────────────────────────────────────────────────────────────

PRIMARY_COLOR = "#0066cc"                     # Hex color for buttons/accents
BOT_AVATAR = "🤖"                             # Bot icon emoji
BOT_NAME = "Support Bot"                      # What the bot calls itself

# ─── LEAD CAPTURE ───────────────────────────────────────────────────────────

CAPTURE_LEADS = True                          # Enable/disable lead capture
REQUIRE_PHONE = False                         # Ask for phone number?
REQUIRE_COMPANY = False                       # Ask for company name?

# ─── FOLLOW-UP SETTINGS ────────────────────────────────────────────────────

FOLLOW_UP_MESSAGE = (
    "Thanks for chatting! A member of our team will follow up "
    "with you at the email you provided within 24 hours."
)

# ─── EMAIL FOLLOW-UP (Resend) ──────────────────────────────────────────────

# Resend is a free email service (3,000 emails/month).
# Sign up at resend.com and add your API key to .streamlit/secrets.toml:
#   [resend]
#   api_key = "re_..."

# The 'from' address for automated follow-up emails.
# On Resend's free tier, you can use "onboarding@resend.dev"
# OR verify your own domain in the Resend dashboard.
# Can be overridden via EMAIL_FROM environment variable.
import os as _os
EMAIL_FROM = _os.environ.get("EMAIL_FROM") or SUPPORT_EMAIL  # Can also use "onboarding@resend.dev"

# Subject line for follow-up emails (supports {name} placeholder)
FOLLOW_UP_SUBJECT = "Thanks for chatting with {name}! 🙌"

# HTML body for follow-up emails (supports {name}, {question}, {phone} placeholders)
# Edit this to match your brand voice!
FOLLOW_UP_BODY = """
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <div style="text-align: center; padding: 30px 0;">
    <h1 style="color: #0066cc; margin: 0;">Thanks for reaching out! 🙌</h1>
  </div>

  <div style="background: #f8f9fa; border-radius: 12px; padding: 30px;">
    <p style="font-size: 16px; line-height: 1.6;">
      Hi <strong>{name}</strong>,
    </p>

    <p style="font-size: 16px; line-height: 1.6;">
      Thanks for chatting with us! We received your message and
      a member of our team will follow up with you within 24 hours.
    </p>

    {question}
    {phone}

    <p style="font-size: 16px; line-height: 1.6;">
      In the meantime, feel free to check out our website for more info!
    </p>

    <div style="text-align: center; padding: 20px 0;">
      <a href="{WEBSITE_URL}"
         style="background: #0066cc; color: white; padding: 12px 30px;
                border-radius: 8px; text-decoration: none; font-weight: bold;">
        Visit Our Website →
      </a>
    </div>
  </div>

  <div style="text-align: center; padding-top: 20px; color: #999; font-size: 12px;">
    <p>{BUSINESS_NAME} — Here to help you grow 🚀</p>
  </div>
</div>
"""

# Auto-send a follow-up email immediately after lead capture?
AUTO_SEND_EMAIL = True

# ─── BRANDED RESPONSES (the bot uses these in answers) ──────────────────────

# These are auto-filled into FAQ answers that reference your business.
# Edit if you want to customize the tone.
PROMO_CODE = ""                               # e.g., "WELCOME20" for 20% off
PROMO_DETAILS = ""                            # e.g., "20% off your first month!"

# ─── MULTI-LANGUAGE SUPPORT ────────────────────────────────────────────────

# Enable the bot to detect and respond in multiple languages.
# When enabled, the bot will:
#   1. Auto-detect the user's language from their message
#   2. Translate their question to English for FAQ matching
#   3. Translate the response back to their language
#
# Requires: pip install googletrans==4.0.0rc1 langdetect>=1.0.9
ENABLE_TRANSLATION = True                   # Set to False to disable multi-language
# List of supported languages (ISO 639-1 codes) — leave empty to allow all
# Example: ["en", "es", "fr", "de", "pt", "ja", "ko", "zh-cn"]
SUPPORTED_LANGUAGES = []
# Default language if detection fails
DEFAULT_LANGUAGE = "en"

# ─── LIVE AGENT HANDOFF ──────────────────────────────────────────────────────

# When the bot can't answer AND a lead is captured, the conversation
# is flagged for a human agent to pick up. Admins can respond from
# the dashboard and messages appear in the user's chat.
#
# Handoff messages are stored in handoff_messages.json.
ENABLE_HANDOFF = True                       # Enable live agent handoff
# Message shown to user when handoff is requested
HANDOFF_MESSAGE = "A human agent will connect with you shortly! 🧑‍💼"

# ─── WEBHOOK / SLACK ALERTS ──────────────────────────────────────────────────

# Send a webhook notification when a new lead is captured.
# Works with Slack webhooks, Discord webhooks, or any custom endpoint.
#
# Set WEBHOOK_URL to your webhook endpoint to enable.
# Leave empty to disable.
WEBHOOK_URL = ""                              # e.g., "https://hooks.slack.com/services/..."
# Customize the webhook message
WEBHOOK_TITLE = "New Lead Captured! 🎯"       # Title/header for the webhook message
WEBHOOK_ENABLED = bool(WEBHOOK_URL)            # Auto-enabled when URL is set

# ─── RATE LIMITING ──────────────────────────────────────────────────────────

# Limits how many messages a single session can send within the time window.
# Helps prevent spam, resource exhaustion, and accidental infinite loops.
# Set RATE_LIMIT_ENABLED to False to disable (not recommended in production).
RATE_LIMIT_ENABLED = True
RATE_LIMIT_MAX_MESSAGES = 20       # Max messages allowed per window
RATE_LIMIT_WINDOW_SECONDS = 60     # Time window in seconds

# ─── INPUT LENGTH LIMITS ───────────────────────────────────────────────────

# Maximum character lengths for various input fields.
# Prevents storage bloat, display issues, and DoS via huge payloads.
MAX_CHAT_MESSAGE_LENGTH = 2000      # User chat messages
MAX_LEAD_NAME_LENGTH = 255          # Lead capture form: name
MAX_LEAD_EMAIL_LENGTH = 255         # Lead capture form: email
MAX_LEAD_PHONE_LENGTH = 50          # Lead capture form: phone
MAX_LEAD_COMPANY_LENGTH = 255       # Lead capture form: company
MAX_FAQ_QUESTION_LENGTH = 500       # Admin FAQ training: question
MAX_FAQ_KEYWORDS_LENGTH = 500       # Admin FAQ training: keywords
MAX_FAQ_ANSWER_LENGTH = 5000        # Admin FAQ training: answer
MAX_HANDOFF_MESSAGE_LENGTH = 2000   # Agent handoff: response
MAX_ADMIN_NOTE_LENGTH = 1000        # Admin lead notes

# ─── WHATSAPP INTEGRATION ───────────────────────────────────────────────────

# WhatsApp bot powered by Twilio.
# To enable:
#   1. Sign up at https://twilio.com (free trial available)
#   2. Get your Account SID and Auth Token from the Twilio Console
#   3. Get a Twilio WhatsApp-enabled number or use the Sandbox
#   4. Set these as environment variables or add them to .env:
#        TWILIO_ACCOUNT_SID=your_sid
#        TWILIO_AUTH_TOKEN=your_token
#        TWILIO_WHATSAPP_NUMBER=+14155238886
#   5. Start the webhook server:
#        uvicorn whatsapp_handler:app --host 0.0.0.0 --port 8000
#   6. Expose with ngrok: ngrok http 8000
#   7. Set the ngrok URL as your Twilio WhatsApp webhook (e.g., https://xxxx.ngrok.io/whatsapp)

# Set to True to enable the WhatsApp handler functionality
WHATSAPP_ENABLED = False

# Custom welcome message sent to new WhatsApp users (leave empty for default)
WHATSAPP_WELCOME_MESSAGE = ""

# ─── LEAD RETENTION POLICY ────────────────────────────────────────────────────

# Auto-archive leads older than this many days.
# Archived leads are moved from leads.json to archived_leads.json
# and can still be viewed/exported from the admin dashboard.
# Set to 0 to disable auto-archiving.
LEAD_RETENTION_DAYS = 90

# ─── DASHBOARD ADMIN PASSWORD ───────────────────────────────────────────────

# ⚠️  SECURITY WARNING: Change this to a strong, unique password!
#     "admin123" is extremely weak and publicly known.
#     Use a password manager to generate something like "K9#mP2$xL7@nR4!q"
#
# 🔐  BETTER: Use an environment variable instead so the password
#     isn't in your source code. Set ADMIN_PASSWORD as a secret
#     in Streamlit Cloud or your deployment platform.
#
#     The code below checks for an env var first, then falls back
#     to this file. On Streamlit Cloud, set it in Settings → Secrets:
#       ADMIN_PASSWORD = "your-secure-password"
#
ADMIN_PASSWORD = _os.environ.get("ADMIN_PASSWORD") or "admin123"
