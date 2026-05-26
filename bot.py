"""
UNIVERSAL BUSINESS BOT v4.0 — A customizable customer service + lead capture bot.

Features:
  - Customizable business info, branding, and FAQ answers
  - Multi-language support (auto-detect + translate)
  - Live agent handoff with admin dashboard responses
  - Conversation analytics with charts
  - FAQ training from admin dashboard
  - Slack/Webhook alerts on new leads
  - Lead capture when the bot can't answer
  - Admin dashboard to view, manage, and export leads
  - 24/7 operation when deployed on Streamlit Cloud
  - Conversation context tracking
  - Beautiful animated UI with dark mode
"""

import streamlit as st
from datetime import datetime
import json
from knowledge_base import find_best_match, get_all_faqs, save_custom_faqs, load_custom_faqs
from leads_manager import LeadsManager
from business_config import (
    BUSINESS_NAME, BUSINESS_TAGLINE, WEBSITE_URL,
    SUPPORT_EMAIL, SUPPORT_PHONE, SUPPORT_HOURS,
    PRIMARY_COLOR, BOT_AVATAR, BOT_NAME,
    CAPTURE_LEADS, REQUIRE_PHONE, REQUIRE_COMPANY,
    ADMIN_PASSWORD,
    AUTO_SEND_EMAIL, EMAIL_FROM,
    ENABLE_TRANSLATION, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE,
    ENABLE_HANDOFF, HANDOFF_MESSAGE,
    WEBHOOK_URL, WEBHOOK_TITLE, WEBHOOK_ENABLED,
)
from email_sender import send_followup_email, get_resend_api_key
from analytics import (
    log_conversation_started, log_conversation_resolved,
    log_unresolved, log_lead_captured, log_feedback,
    log_language, get_summary, reset_analytics, export_analytics_json,
)
import random
import os
import html

# ─── MULTI-LANGUAGE TRANSLATION ─────────────────────────────────────────────
# Wrapped in try/except so the bot works even if translation libs aren't installed
_TRANSLATOR_AVAILABLE = False
try:
    from googletrans import Translator as GoogleTranslator
    _translator = GoogleTranslator()
    _TRANSLATOR_AVAILABLE = True
except Exception:
    pass

try:
    from langdetect import detect as _detect_lang
    _LANGDETECT_AVAILABLE = True
except Exception:
    _LANGDETECT_AVAILABLE = False


def detect_language(text):
    """Detect the language of a text. Returns ISO 639-1 code or None."""
    if not _LANGDETECT_AVAILABLE or not text:
        return None
    try:
        return _detect_lang(text)
    except Exception:
        return None


def translate_text(text, dest_lang="en", src_lang=None):
    """Translate text to the destination language. Returns translated text or original on failure."""
    if not _TRANSLATOR_AVAILABLE or not text:
        return text
    try:
        params = {"dest": dest_lang}
        if src_lang:
            params["src"] = src_lang
        result = _translator.translate(text, **params)
        return result.text if result and result.text else text
    except Exception:
        return text


def is_language_supported(lang_code):
    """Check if a language is in the supported list (empty list = all supported)."""
    if not lang_code:
        return True
    if not SUPPORTED_LANGUAGES:
        return True
    return lang_code in SUPPORTED_LANGUAGES


def process_multilingual(prompt):
    """
    Detect language, translate to English for FAQ matching.
    Returns (translated_prompt, original_language, user_facing_response_lang).
    """
    if not ENABLE_TRANSLATION or not _LANGDETECT_AVAILABLE:
        return prompt, "en", "en"

    lang = detect_language(prompt)
    if lang:
        log_language(lang)
        # Short code normalization (e.g., 'zh-cn' -> 'zh-cn', 'ko' -> 'ko')
        lang_short = lang.split("-")[0] if "-" in lang else lang

        # If already English, no translation needed
        if lang_short == "en":
            return prompt, "en", "en"

        # If language is not supported, still try to answer in English
        if not is_language_supported(lang_short):
            translated = translate_text(prompt, dest_lang="en", src_lang=lang_short)
            return translated, lang_short, "en"

        # Translate to English for FAQ matching
        translated = translate_text(prompt, dest_lang="en", src_lang=lang_short)
        return translated, lang_short, lang_short

    return prompt, DEFAULT_LANGUAGE, DEFAULT_LANGUAGE


def translate_response(response, target_lang):
    """Translate a bot response to the user's language."""
    if target_lang == "en" or not _TRANSLATOR_AVAILABLE or not response:
        return response
    try:
        return translate_text(response, dest_lang=target_lang)
    except Exception:
        return response


# ─── WEBHOOK HELPER ─────────────────────────────────────────────────────────

def send_webhook_alert(lead_name, lead_email, lead_question):
    """Send a webhook notification when a new lead is captured."""
    if not WEBHOOK_ENABLED or not WEBHOOK_URL:
        return

    try:
        payload = {
            "text": f"*{WEBHOOK_TITLE}*\n"
                    f"• *Name:* {lead_name}\n"
                    f"• *Email:* {lead_email}\n"
                    f"• *Question:* {lead_question[:200]}\n"
                    f"• *Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        }
        # Support both Slack-style and generic webhooks
        headers = {"Content-Type": "application/json"}
        _requests.post(WEBHOOK_URL, json=payload, headers=headers, timeout=10)
    except Exception:
        pass  # Silently fail — don't break the user experience


# ─── HANDOFF MESSAGES ───────────────────────────────────────────────────────

_HANDOFF_FILE = os.path.join(os.path.dirname(__file__), "handoff_messages.json")


def _read_handoffs():
    try:
        with open(_HANDOFF_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_handoffs(handoffs):
    with open(_HANDOFF_FILE, "w") as f:
        json.dump(handoffs, f, indent=2)


def request_handoff(user_name, user_email, user_question):
    """Create a handoff request for a human agent."""
    handoffs = _read_handoffs()
    handoff = {
        "id": len(handoffs) + 1,
        "user_name": user_name,
        "user_email": user_email,
        "user_question": user_question,
        "status": "pending",  # pending | assigned | resolved
        "messages": [
            {"role": "user", "text": user_question, "timestamp": datetime.now().isoformat()}
        ],
        "agent_responses": [],
        "created_at": datetime.now().isoformat(),
    }
    handoffs.append(handoff)
    _write_handoffs(handoffs)
    return handoff


def add_agent_response(handoff_id, agent_text):
    """Add an agent's response to a handoff conversation."""
    handoffs = _read_handoffs()
    for h in handoffs:
        if h["id"] == handoff_id:
            h["status"] = "assigned"
            h["agent_responses"].append({
                "text": agent_text,
                "timestamp": datetime.now().isoformat(),
            })
            h["messages"].append({
                "role": "agent",
                "text": agent_text,
                "timestamp": datetime.now().isoformat(),
            })
            _write_handoffs(handoffs)
            return True
    return False


def resolve_handoff(handoff_id):
    """Mark a handoff as resolved."""
    handoffs = _read_handoffs()
    for h in handoffs:
        if h["id"] == handoff_id:
            h["status"] = "resolved"
            _write_handoffs(handoffs)
            return True
    return False


def get_pending_handoffs():
    """Get all handoffs that need attention."""
    return [h for h in _read_handoffs() if h["status"] in ("pending", "assigned")]


def get_agent_responses_for_user(user_email):
    """Get any new agent responses for a user since they last checked."""
    handoffs = _read_handoffs()
    for h in handoffs:
        if h["user_email"] == user_email and h["agent_responses"]:
            latest = h["agent_responses"][-1]
            return latest["text"], h["id"]
    return None, None


# ─── INIT ───────────────────────────────────────────────────────────────────

db = LeadsManager()

# Detect embed mode (?embed=1) — hides sidebar and Streamlit chrome for iframe embedding
EMBED_MODE = st.query_params.get("embed", "0") == "1"

st.set_page_config(
    page_title=f"{BUSINESS_NAME} Support",
    page_icon=BOT_AVATAR,
    layout="centered",
    initial_sidebar_state="collapsed" if EMBED_MODE else "expanded",
)

# ─── CUSTOM CSS (dynamic branding from business_config.py) ──────────────────

# ─── EMBED NOTIFICATION (postMessage to parent widget) ─────────
# Injects a script that sends parent the new message preview so the embed widget
# can show a badge count + toast notification

if EMBED_MODE and st.session_state.pending_notification:
    st.markdown(
        f"<script>try {{ parent.postMessage({{type:'sb-new-message', text:{st.session_state.pending_notification}}}, '*'); }} catch(e){{}}</script>",
        unsafe_allow_html=True,
    )
    st.session_state.pending_notification = None

st.markdown(f"""<style>
    /* ── DESIGN TOKENS ────────────────────────────────────────── */
    :root {{
        --primary: {PRIMARY_COLOR};
        --primary-light: {PRIMARY_COLOR}22;
        --primary-glow: {PRIMARY_COLOR}44;
        --bg: #f8f9fc;
        --bg-card: #ffffff;
        --text-primary: #1a1a2e;
        --text-secondary: #64748b;
        --border: #e2e8f0;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.06);
        --shadow-md: 0 4px 16px rgba(0,0,0,0.08);
        --shadow-lg: 0 8px 32px rgba(0,0,0,0.10);
        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 24px;
    }}

    @media (prefers-color-scheme: dark) {{
        :root {{
            --bg: #0f0f1a;
            --bg-card: #1a1a2e;
            --text-primary: #e2e8f0;
            --text-secondary: #94a3b8;
            --border: #2d2d44;
            --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
            --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
            --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
        }}
    }}

    /* ── GLOBAL ───────────────────────────────────────────────── */
    .stApp {{ background: var(--bg); }}
    .main > div {{ max-width: 800px; margin: 0 auto; }}

    /* ── HEADER ───────────────────────────────────────────────── */
    .chat-header {{
        text-align: center; padding: 2.5rem 1rem 1.5rem; position: relative;
    }}
    .chat-header::after {{
        content: ''; position: absolute; bottom: 0; left: 50%;
        transform: translateX(-50%); width: 60px; height: 3px;
        background: linear-gradient(90deg, transparent, var(--primary), transparent);
        border-radius: 2px;
    }}
    .chat-header .avatar {{
        font-size: 3.5rem; display: block; margin-bottom: 0.5rem;
        animation: float 3s ease-in-out infinite;
    }}
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-6px); }}
    }}
    .chat-header h1 {{
        font-size: 1.8rem; font-weight: 700; color: var(--text-primary);
        margin: 0.3rem 0 0.2rem; letter-spacing: -0.02em;
    }}
    .chat-header .tagline {{
        color: var(--text-secondary); font-size: 0.95rem; margin: 0;
    }}

    /* ── CHAT BUBBLES ─────────────────────────────────────────── */
    .chat-bubble {{
        padding: 0.75rem 1rem; border-radius: var(--radius-md);
        margin-bottom: 0.6rem; animation: messageIn 0.3s ease-out;
        line-height: 1.5; font-size: 0.95rem;
    }}
    @keyframes messageIn {{
        from {{ opacity: 0; transform: translateY(8px) scale(0.97); }}
        to {{ opacity: 1; transform: translateY(0) scale(1); }}
    }}
    div[data-testid="chat-message-user"] .chat-bubble {{
        background: linear-gradient(135deg, var(--primary), {PRIMARY_COLOR}dd);
        color: white;
        border-radius: var(--radius-md) var(--radius-md) 4px var(--radius-md);
        box-shadow: 0 2px 8px {PRIMARY_COLOR}44;
    }}
    div[data-testid="chat-message-assistant"] .chat-bubble {{
        background: var(--bg-card); color: var(--text-primary);
        border: 1px solid var(--border);
        border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
        box-shadow: var(--shadow-sm);
    }}

    /* ── TYPING INDICATOR ─────────────────────────────────────── */
    .typing-indicator {{
        display: inline-flex; align-items: center; gap: 4px;
        padding: 0.75rem 1rem; background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
        box-shadow: var(--shadow-sm); animation: messageIn 0.2s ease-out;
    }}
    .typing-dot {{
        width: 8px; height: 8px; border-radius: 50%; background: var(--primary);
        animation: typingBounce 1.4s ease-in-out infinite;
    }}
    .typing-dot:nth-child(2) {{ animation-delay: 0.2s; }}
    .typing-dot:nth-child(3) {{ animation-delay: 0.4s; }}
    @keyframes typingBounce {{
        0%, 60%, 100% {{ transform: translateY(0); opacity: 0.4; }}
        30% {{ transform: translateY(-6px); opacity: 1; }}
    }}

    /* ── SUGGESTION BUTTONS ───────────────────────────────────── */
    .suggestion-grid {{
        display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-top: 0.5rem;
    }}
    .suggestion-btn {{
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--radius-sm); padding: 0.6rem 0.8rem;
        text-align: center; cursor: pointer; color: var(--text-primary);
        font-size: 0.85rem; transition: all 0.2s ease; box-shadow: var(--shadow-sm);
    }}
    .suggestion-btn:hover {{
        border-color: var(--primary); background: var(--primary-light);
        transform: translateY(-1px); box-shadow: 0 4px 12px var(--primary-glow);
    }}

    /* ── LEAD CAPTURE FORM ────────────────────────────────────── */
    .lead-capture-form {{
        background: linear-gradient(135deg, var(--bg-card), var(--bg-card));
        border: 1px solid var(--border); border-radius: var(--radius-lg);
        padding: 1.5rem; margin: 1rem 0; box-shadow: var(--shadow-md);
        animation: messageIn 0.4s ease-out; position: relative; overflow: hidden;
    }}
    .lead-capture-form::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
        background: linear-gradient(90deg, var(--primary), {PRIMARY_COLOR}88, var(--primary));
    }}
    .lead-capture-form h4 {{ margin: 0 0 0.3rem; color: var(--text-primary); font-size: 1.1rem; }}
    .lead-capture-form p {{ color: var(--text-secondary); font-size: 0.85rem; margin: 0 0 1rem; }}

    /* ── SIDEBAR / STATS ──────────────────────────────────────── */
    .stat-box {{
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--radius-md); padding: 0.8rem 0.5rem;
        text-align: center; transition: transform 0.2s; box-shadow: var(--shadow-sm);
    }}
    .stat-box:hover {{ transform: translateY(-2px); box-shadow: var(--shadow-md); }}
    .stat-number {{ font-size: 1.6rem; font-weight: 700; color: var(--primary); line-height: 1.2; }}
    .stat-label {{ font-size: 0.7rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }}

    /* ── LEAD CARDS ───────────────────────────────────────────── */
    .lead-card {{
        background: var(--bg-card); border: 1px solid var(--border);
        border-radius: var(--radius-md); padding: 0.8rem 1rem;
        margin-bottom: 0.6rem; border-left: 3px solid var(--primary);
        box-shadow: var(--shadow-sm); transition: all 0.2s ease;
        animation: messageIn 0.3s ease-out;
    }}
    .lead-card:hover {{ box-shadow: var(--shadow-md); transform: translateX(2px); }}
    .lead-name {{ font-weight: 600; font-size: 0.9rem; color: var(--text-primary); }}
    .lead-email {{ color: var(--primary); font-size: 0.8rem; }}
    .lead-question {{ color: var(--text-secondary); font-size: 0.78rem; font-style: italic; }}
    .lead-time {{ color: var(--text-secondary); font-size: 0.72rem; opacity: 0.7; }}

    /* ── BADGES ───────────────────────────────────────────────── */
    .badge {{
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 0.68rem; font-weight: 600; letter-spacing: 0.02em;
    }}
    .badge-pending {{ background: #fef3c7; color: #92400e; }}
    .badge-contacted {{ background: #d1fae5; color: #065f46; }}
    .badge-closed {{ background: #e2e8f0; color: #475569; }}
    .badge-email-sent {{ background: #dbeafe; color: #1e40af; margin-left: 4px; }}
    .badge-handoff {{ background: #ede9fe; color: #5b21b6; margin-left: 4px; }}

    @media (prefers-color-scheme: dark) {{
        .badge-pending {{ background: #78350f44; color: #fbbf24; }}
        .badge-contacted {{ background: #064e3b44; color: #34d399; }}
        .badge-closed {{ background: #1e293b44; color: #94a3b8; }}
        .badge-email-sent {{ background: #1e3a5f44; color: #60a5fa; }}
        .badge-handoff {{ background: #3b1f6e44; color: #a78bfa; }}
    }}

    /* ── SUCCESS / ERROR TOASTS ───────────────────────────────── */
    .stSuccess, .stInfo {{
        border-radius: var(--radius-md) !important; border: none !important;
        box-shadow: var(--shadow-sm) !important; animation: messageIn 0.3s ease-out !important;
    }}

    /* ── BUTTONS ──────────────────────────────────────────────── */
    .stButton > button {{
        border-radius: var(--radius-sm) !important;
        transition: all 0.2s ease !important;
        font-weight: 500 !important;
        border: 1px solid transparent !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px var(--primary-glow) !important;
    }}
    div[data-testid="baseButton-primary"] > button {{
        background: linear-gradient(135deg, var(--primary), {PRIMARY_COLOR}dd) !important;
    }}

    /* ── FEEDBACK BUTTONS ─────────────────────────────────────── */
    .feedback-btn {{
        background: transparent; border: none; font-size: 1.1rem; cursor: pointer;
        padding: 4px 8px; border-radius: var(--radius-sm);
        transition: all 0.2s; opacity: 0.5;
    }}
    .feedback-btn:hover {{ opacity: 1; background: var(--primary-light); transform: scale(1.1); }}

    /* ── DIVIDER ──────────────────────────────────────────────── */
    .section-divider {{
        border: none; height: 1px;
        background: linear-gradient(90deg, transparent, var(--border), transparent);
        margin: 1rem 0;
    }}

    /* ── SCROLLBAR ────────────────────────────────────────────── */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--text-secondary); }}

    /* ── EMBED MODE (?embed=1) ────────────────────────────────── */
    .embed-mode .stApp {{ border-radius: 0 !important; }}
    .embed-mode header {{ display: none !important; }}
    .embed-mode footer {{ display: none !important; }}
    .embed-mode #stDecoration {{ display: none !important; }}
    .embed-mode .stAppToolbar {{ display: none !important; }}
    .embed-mode .stAppDeployButton {{ display: none !important; }}
    .embed-mode .main > div {{ max-width: 100% !important; padding: 0 !important; }}
    .embed-mode .block-container {{ padding-top: 0.5rem !important; padding-bottom: 0.5rem !important; max-width: 100% !important; }}
    .embed-mode .chat-header {{ padding: 0.8rem 0.8rem 0.6rem !important; }}
    .embed-mode .chat-header .avatar {{ font-size: 2rem !important; margin-bottom: 0 !important; }}
    .embed-mode .chat-header h1 {{ font-size: 1.1rem !important; }}
    .embed-mode .chat-header .tagline {{ font-size: 0.75rem !important; }}
    .embed-mode .chat-header::after {{ width: 40px !important; }}
    .embed-mode .chat-bubble {{ padding: 0.5rem 0.75rem !important; font-size: 0.85rem !important; }}
    .embed-mode .lead-capture-form {{ padding: 1rem !important; }}
    .embed-mode .suggestion-grid {{ grid-template-columns: 1fr 1fr !important; gap: 0.3rem !important; }}
    .embed-mode .stChatInput {{ font-size: 0.85rem !important; }}
    .embed-mode .chat-bubble img {{ max-width: 100% !important; }}
    .embed-mode div[data-testid="collapsed-control"] {{ display: none !important; }}
</style>

<script>
    // Apply embed-mode class immediately to prevent flash of full UI
    if (document.body && document.body.parentElement) {{
        document.body.parentElement.classList.add('embed-mode');
    }} else {{
        document.addEventListener('DOMContentLoaded', function() {{
            if (document.body && document.body.parentElement) {{
                document.body.parentElement.classList.add('embed-mode');
            }}
        }});
    }}

    // Send 'sb-close' message to parent widget (when embedded via iframe)
    window.sbClose = function() {{
        try {{ parent.postMessage('sb-close', '*'); }} catch(e) {{ /* not in iframe */ }}
    }};
</script>""", unsafe_allow_html=True)

# ─── SESSION STATE ──────────────────────────────────────────────────────────

for key, default in [
    ("messages", []),
    ("session_start", datetime.now()),
    ("questions_asked", 0),
    ("resolved_count", 0),
    ("unresolved_count", 0),
    ("show_lead_form", False),
    ("lead_capture_pending", False),
    ("lead_capture_reason", ""),
    ("admin_authenticated", False),
    ("show_kb", False),
    ("show_leads", False),
    ("show_analytics", False),
    ("show_training", False),
    ("show_handoffs", False),
    ("last_lead_captured", None),
    ("confirm_clear", False),
    ("conversation_context", None),
    ("typing_active", False),
    ("feedback_log", []),
    ("pending_notification", None),
    ("handoff_requested", False),
    ("handoff_id", None),
    ("user_language", "en"),
    ("analytics_logged_conversation", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─── HELPER FUNCTIONS ───────────────────────────────────────────────────────

def get_business_context():
    """Return business info for dynamic responses."""
    return {
        "name": BUSINESS_NAME,
        "email": SUPPORT_EMAIL,
        "phone": SUPPORT_PHONE,
        "hours": SUPPORT_HOURS,
        "website": WEBSITE_URL,
    }


def format_cant_answer_response():
    """Response when the bot can't find a match."""
    biz = get_business_context()
    return (
        "🤔 **I'm not sure about that one.**\n\n"
        "No worries though! Let me connect you with a human agent who can help.\n\n"
        f"📧 **Email:** {biz['email']}\n"
        f"📞 **Phone:** {biz['phone']} ({biz['hours']})\n"
        f"🌐 **Website:** {biz['website']}\n\n"
        "Or leave your contact info below and we'll get back to you! 👇"
    )


def capture_lead_from_form(name, email, phone, company, question):
    """Capture a lead from the form."""
    source = st.session_state.get("lead_capture_reason", "unanswered")
    lead = db.add_lead(
        name=name,
        email=email,
        phone=phone,
        company=company,
        question=question,
        source=source,
    )
    st.session_state.last_lead_captured = lead
    st.session_state.lead_capture_pending = False
    st.session_state.show_lead_form = False

    log_lead_captured()
    send_webhook_alert(name, email, question)

    # Request live agent handoff if enabled
    if ENABLE_HANDOFF:
        handoff = request_handoff(name, email, question)
        st.session_state.handoff_requested = True
        st.session_state.handoff_id = handoff["id"]

    # Auto-send follow-up email if configured
    if AUTO_SEND_EMAIL and get_resend_api_key() is not None:
        try:
            success, msg = send_followup_email(name, email, question, phone)
            if success:
                db.mark_email_sent(lead["id"])
                st.session_state._email_result = "📧 Follow-up email sent!"
            else:
                st.session_state._email_result = msg
        except Exception as e:
            st.session_state._email_result = f"Could not send auto-email: {e}"

    return lead


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — Admin Dashboard + Business Info
# ═══════════════════════════════════════════════════════════════════════════════

if not EMBED_MODE:
    with st.sidebar:
        # ── BUSINESS INFO ──────────────────────────────────────────────────
        st.markdown(f"### {BOT_AVATAR} {BUSINESS_NAME}")
        st.markdown(f"*{BUSINESS_TAGLINE}*")
        st.markdown("---")

        # ── STATS ─────────────────────────────────────────────────────────
        total_lead_count, pending_lead_count = db.get_lead_count()
        total_lead_stats, email_sent_count = db.get_email_stats()
        has_api_key = get_resend_api_key() is not None
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"<div class='stat-box'>"
                f"<div class='stat-number'>{st.session_state.questions_asked}</div>"
                f"<div class='stat-label'>Chats</div></div>",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(
                f"<div class='stat-box'>"
                f"<div class='stat-number'>{total_lead_count}</div>"
                f"<div class='stat-label'>Leads</div></div>",
                unsafe_allow_html=True,
            )
        with col3:
            st.markdown(
                f"<div class='stat-box'>"
                f"<div class='stat-number'>{email_sent_count}</div>"
                f"<div class='stat-label'>Emailed</div></div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # ── SESSION METRICS ────────────────────────────────────────────────
        with st.expander("📊 Session Metrics"):
            st.markdown(
                f"**Resolved:** {st.session_state.resolved_count} "
                f"• **Unresolved:** {st.session_state.unresolved_count}"
            )
            session_duration = datetime.now() - st.session_state.session_start
            mins = int(session_duration.total_seconds() // 60)
            secs = int(session_duration.total_seconds() % 60)
            st.markdown(f"**Duration:** {mins}m {secs}s")
            if st.session_state.feedback_log:
                ups = sum(1 for f in st.session_state.feedback_log if f == "up")
                downs = sum(1 for f in st.session_state.feedback_log if f == "down")
                st.markdown(f"**Feedback:** 👍 {ups}  👎 {downs}")
            if _TRANSLATOR_AVAILABLE:
                st.markdown(f"**🌐 Translation:** Active")
                if st.session_state.user_language != "en":
                    st.markdown(f"**User language:** {st.session_state.user_language}")

        # ── ADMIN LOGIN ────────────────────────────────────────────────────
        st.markdown("### 🔐 Admin Panel")
        if not st.session_state.admin_authenticated:
            password = st.text_input("Password", type="password", key="admin_pwd")
            if password:
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
        else:
            st.success("✅ Authenticated")
            if st.button("🔒 Logout", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.rerun()

            st.markdown("---")

            # ── ADMIN NAVIGATION ───────────────────────────────────────────
            nav_col1, nav_col2 = st.columns(2)
            with nav_col1:
                st.button("📋 Leads", key="nav_leads", use_container_width=True,
                          on_click=lambda: st.session_state.update(show_leads=True, show_analytics=False, show_training=False, show_handoffs=False))
            with nav_col2:
                st.button("📊 Analytics", key="nav_analytics", use_container_width=True,
                          on_click=lambda: st.session_state.update(show_analytics=True, show_leads=False, show_training=False, show_handoffs=False))

            nav_col3, nav_col4 = st.columns(2)
            with nav_col3:
                st.button("🧠 Train FAQ", key="nav_training", use_container_width=True,
                          on_click=lambda: st.session_state.update(show_training=True, show_leads=False, show_analytics=False, show_handoffs=False))
            with nav_col4:
                pending_count = len(get_pending_handoffs())
                handoff_label = f"🤝 Handoffs ({pending_count})" if pending_count else "🤝 Handoffs"
                st.button(handoff_label, key="nav_handoffs", use_container_width=True,
                          on_click=lambda: st.session_state.update(show_handoffs=True, show_leads=False, show_analytics=False, show_training=False))

            # ─── DEFAULT VIEW: LEAD DASHBOARD ──────────────────────────────
            if not any([st.session_state.show_leads, st.session_state.show_analytics,
                        st.session_state.show_training, st.session_state.show_handoffs]):
                st.session_state.show_leads = True

            # ═══════════════════════════════════════════════════════════════
            # LEAD DASHBOARD VIEW
            # ═══════════════════════════════════════════════════════════════
            if st.session_state.show_leads:
                st.markdown("### 📋 Lead Dashboard")

                filter_option = st.radio(
                    "Show:", ["All Leads", "Pending Only", "Contacted"],
                    horizontal=True, key="lead_filter",
                )

                search_query = st.text_input("🔍 Search leads...", key="lead_search", placeholder="Name, email, or question")

                all_leads = db.get_all_leads()
                if search_query:
                    sq = search_query.lower()
                    all_leads = [
                        l for l in all_leads
                        if sq in l["name"].lower()
                        or sq in l["email"].lower()
                        or sq in l.get("question", "").lower()
                        or sq in l.get("company", "").lower()
                    ]

                if filter_option == "Pending Only":
                    filtered_leads = [l for l in all_leads if l["status"] == "pending"]
                elif filter_option == "Contacted":
                    filtered_leads = [l for l in all_leads if l["status"] in ("contacted", "closed")]
                else:
                    filtered_leads = all_leads

                if filtered_leads:
                    st.markdown(f"**{len(filtered_leads)} lead{'s' if len(filtered_leads) != 1 else ''}**")
                    for lead in filtered_leads[:20]:
                        status_class = f"badge-{lead['status']}"
                        email_badge = ""
                        if lead.get("email_sent"):
                            email_badge = "<span class='badge badge-email-sent'>📧 SENT</span>"
                        source_tag = f"<span style='font-size:0.7rem;color:var(--text-secondary);margin-left:4px;'>via {lead.get('source', 'chat')}</span>" if lead.get('source') else ""
                        safe_name = html.escape(lead['name'])
                        safe_email = html.escape(lead['email'])
                        safe_phone = html.escape(lead.get('phone', ''))
                        safe_company = html.escape(lead.get('company', ''))
                        safe_question = html.escape(lead['question'][:80])
                        safe_timestamp = html.escape(lead['timestamp'])
                        st.markdown(
                            f"<div class='lead-card'>"
                            f"<div class='lead-name'>{safe_name} "
                            f"<span class='badge {status_class}'>{lead['status'].upper()}</span>"
                            f"{email_badge}{source_tag}</div>"
                            f"<div class='lead-email'>{safe_email}</div>"
                            + (f"<div class='lead-email'>{safe_phone}</div>" if lead.get('phone') else "")
                            + (f"<div>{safe_company}</div>" if lead.get('company') else "")
                            + f"<div class='lead-question'>\"{safe_question}{'...' if len(lead['question']) > 80 else ''}\"</div>"
                            + f"<div class='lead-time'>{safe_timestamp}</div>"
                            + f"</div>",
                            unsafe_allow_html=True,
                        )

                        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                        with col1:
                            if lead["status"] == "pending":
                                if st.button(f"✅", key=f"contact_{lead['id']}", help="Mark contacted"):
                                    db.mark_contacted(lead["id"])
                                    st.rerun()
                        with col2:
                            if lead["status"] == "contacted":
                                if st.button(f"📁", key=f"close_{lead['id']}", help="Mark closed"):
                                    db.mark_closed(lead["id"])
                                    st.rerun()
                        with col3:
                            if not lead.get("email_sent") and has_api_key:
                                if st.button(f"📧", key=f"email_{lead['id']}", help="Send email"):
                                    with st.spinner("Sending..."):
                                        success, msg = send_followup_email(
                                            lead["name"], lead["email"],
                                            lead["question"], lead.get("phone", "")
                                        )
                                        if success:
                                            db.mark_email_sent(lead["id"])
                                            st.success(msg)
                                        else:
                                            st.error(msg)
                                    st.rerun()
                        with col4:
                            if lead.get("notes"):
                                st.caption(f"📝 {lead['notes']}")
                            else:
                                with st.popover("📝", help="Add note"):
                                    note = st.text_area("Note", key=f"note_input_{lead['id']}", label_visibility="collapsed")
                                    if st.button("Save", key=f"save_note_{lead['id']}"):
                                        db.add_note(lead["id"], note)
                                        st.rerun()

                        st.markdown("<hr style='margin: 6px 0; opacity: 0.2;'>", unsafe_allow_html=True)
                else:
                    st.info("No leads match your filters. They'll appear here once customers start chatting!")

                # ── ADMIN: RESEND CONFIG STATUS ───────────────────────────
                st.markdown("---")
                st.markdown("### 📧 Email Follow-up")
                if has_api_key:
                    st.success(f"✅ Resend connected (from: {EMAIL_FROM})")
                    st.caption(f"Auto-send: {'ON' if AUTO_SEND_EMAIL else 'OFF'} • Sent: {email_sent_count}/{total_lead_count}")
                else:
                    st.warning("⚠️ Resend API key not set")
                    with st.expander("🔧 How to set up email"):
                        st.markdown("""
                    1. Go to **[resend.com](https://resend.com)** and sign up (free)
                    2. Create an API key
                    3. Edit `.streamlit/secrets.toml`:

                       ```toml
                       [resend]
                       api_key = "re_..."
                       ```

                    Or on Streamlit Cloud:
                    Settings → Secrets → paste the same format.
                    """)

                # ── ADMIN: EXPORT ──────────────────────────────────────────
                st.markdown("---")
                st.markdown("### 📤 Export Leads")
                csv_data = db.export_csv()
                if csv_data:
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"leads_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

                # ── ADMIN: QUICK ACTIONS ───────────────────────────────────
                st.markdown("---")
                st.markdown("### ⚙️ Quick Actions")

                if st.button("🔄 Reset Chat", use_container_width=True):
                    st.session_state.messages = []
                    st.session_state.questions_asked = 0
                    st.session_state.resolved_count = 0
                    st.session_state.unresolved_count = 0
                    st.session_state.show_lead_form = False
                    st.session_state.lead_capture_pending = False
                    st.session_state.conversation_context = None
                    st.session_state.feedback_log = []
                    st.session_state.handoff_requested = False
                    st.session_state.handoff_id = None
                    st.session_state.user_language = "en"
                    st.rerun()

                if st.button("📖 View FAQs", use_container_width=True):
                    st.session_state.show_kb = not st.session_state.get("show_kb", False)

                if st.button("🗑️ Clear All Leads", use_container_width=True):
                    if st.session_state.confirm_clear:
                        leads_path = os.path.join(os.path.dirname(__file__), "leads.json")
                        if os.path.exists(leads_path):
                            os.remove(leads_path)
                        st.session_state.confirm_clear = False
                        st.rerun()
                    else:
                        st.session_state.confirm_clear = True
                        st.warning("Click again to confirm — this cannot be undone!")

                # Show FAQs if toggled
                if st.session_state.get("show_kb", False):
                    st.markdown("---")
                    st.markdown("### 📚 Current FAQs")
                    for i, faq in enumerate(get_all_faqs(), 1):
                        with st.expander(f"{i}. {faq['question']}"):
                            st.markdown(f"**Keywords:** {', '.join(faq['keywords'])}")
                            st.markdown(f"**Answer:** {faq['answer']}")

            # ═══════════════════════════════════════════════════════════════
            # ANALYTICS VIEW
            # ═══════════════════════════════════════════════════════════════
            if st.session_state.show_analytics:
                st.markdown("### 📊 Conversation Analytics")
                summary = get_summary()

                # Overview metrics
                met_col1, met_col2, met_col3, met_col4 = st.columns(4)
                with met_col1:
                    st.metric("Total Chats", summary["total_conversations"])
                with met_col2:
                    st.metric("Resolved", summary["resolved"])
                with met_col3:
                    st.metric("Resolution Rate", f"{summary['resolution_rate']}%")
                with met_col4:
                    lead_rate = round(summary["lead_captures"] / max(summary["total_conversations"], 1) * 100, 1)
                    st.metric("Lead Conversion", f"{lead_rate}%")

                met_col1, met_col2, met_col3, met_col4 = st.columns(4)
                with met_col1:
                    st.metric("👍 Feedback", summary["feedback_ups"])
                with met_col2:
                    st.metric("👎 Feedback", summary["feedback_downs"])
                with met_col3:
                    st.metric("Unmatched", summary["unmatched_count"])
                with met_col4:
                    st.metric("Leads Captured", summary["lead_captures"])

                # Daily chart (last 14 days)
                daily = summary["daily_data"]
                if daily and any(d["chats"] > 0 for d in daily):
                    st.markdown("---")
                    st.markdown("#### 📈 Daily Activity (Last 14 Days)")
                    chart_data = {
                        "Date": [d["date"][-5:] for d in daily],  # MM-DD
                        "Chats": [d["chats"] for d in daily],
                        "Leads": [d["leads"] for d in daily],
                    }
                    st.bar_chart(chart_data, x="Date", y=["Chats", "Leads"], stack=False)

                    # Resolution trend
                    res_data = {
                        "Date": [d["date"][-5:] for d in daily],
                        "Resolved": [d["resolved"] for d in daily],
                    }
                    if any(v > 0 for v in res_data["Resolved"]):
                        st.markdown("#### ✅ Resolutions Over Time")
                        st.bar_chart(res_data, x="Date", y="Resolved")
                else:
                    st.info("📊 Chart data will appear once conversations start rolling in!")

                # Top FAQs
                if summary["top_faqs"]:
                    st.markdown("---")
                    st.markdown("#### 🔥 Most Asked Questions")
                    for q, count in summary["top_faqs"]:
                        st.markdown(f"- **{q}** — {count} times")

                # Language distribution
                if summary["languages"]:
                    st.markdown("---")
                    st.markdown("#### 🌐 Languages Detected")
                    for lang, count in sorted(summary["languages"].items(), key=lambda x: x[1], reverse=True):
                        flag = {"en": "🇺🇸", "es": "🇪🇸", "fr": "🇫🇷", "de": "🇩🇪", "pt": "🇵🇹",
                                "ja": "🇯🇵", "ko": "🇰🇷", "zh-cn": "🇨🇳", "it": "🇮🇹",
                                "nl": "🇳🇱", "ru": "🇷🇺", "ar": "🇸🇦", "hi": "🇮🇳"}.get(lang, "🌐")
                        st.markdown(f"{flag} **{lang.upper()}** — {count} messages")

                # Export & Reset
                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    json_data = export_analytics_json()
                    st.download_button(
                        "📥 Export JSON", data=json_data,
                        file_name=f"analytics_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json", use_container_width=True,
                    )
                with col_b:
                    if st.button("🔄 Reset Analytics", use_container_width=True):
                        reset_analytics()
                        st.rerun()

            # ═══════════════════════════════════════════════════════════════
            # FAQ TRAINING VIEW
            # ═══════════════════════════════════════════════════════════════
            if st.session_state.show_training:
                st.markdown("### 🧠 Train the Bot")
                st.markdown("Add new FAQs that the bot will learn instantly — no restart needed.")

                with st.form("add_faq_form"):
                    st.markdown("#### ➕ Add New FAQ")
                    new_question = st.text_input("Question (what the customer would ask)", placeholder="e.g., Do you have a mobile app?")
                    new_keywords = st.text_input("Keywords (comma-separated)", placeholder="e.g., mobile app, ios, android, app")
                    new_answer = st.text_area("Answer (markdown supported)", placeholder="e.g., Yes! We have apps for both iOS and Android...", height=150)

                    col_s, col_c = st.columns([1, 3])
                    with col_s:
                        submitted_faq = st.form_submit_button("➕ Add FAQ", type="primary", use_container_width=True)
                    with col_c:
                        st.caption("The bot will learn this instantly — no restart needed!")

                    if submitted_faq:
                        if new_question and new_keywords and new_answer:
                            keyword_list = [k.strip() for k in new_keywords.split(",") if k.strip()]
                            custom_faqs = load_custom_faqs()
                            custom_faqs.append({
                                "keywords": keyword_list,
                                "question": new_question,
                                "answer": new_answer,
                            })
                            save_custom_faqs(custom_faqs)
                            st.success(f"✅ FAQ added: '{new_question}' — the bot will use it immediately!")
                            st.rerun()
                        else:
                            st.error("Please fill in all fields (question, keywords, and answer).")

                st.markdown("---")

                # Show existing custom FAQs with delete option
                custom_faqs = load_custom_faqs()
                if custom_faqs:
                    st.markdown(f"#### 📚 Custom FAQs ({len(custom_faqs)})")
                    for i, faq in enumerate(custom_faqs):
                        with st.expander(f"✏️ {faq['question']}"):
                            st.markdown(f"**Keywords:** {', '.join(faq['keywords'])}")
                            st.markdown(f"**Answer:** {faq['answer'][:200]}{'...' if len(faq['answer']) > 200 else ''}")
                            if st.button(f"🗑️ Delete", key=f"del_faq_{i}"):
                                custom_faqs.pop(i)
                                save_custom_faqs(custom_faqs)
                                st.rerun()
                else:
                    st.info("No custom FAQs yet. Add one above!")

                # Show built-in FAQ count
                built_in_count = len(get_all_faqs()) - len(custom_faqs)
                st.caption(f"📖 {built_in_count} built-in FAQs + {len(custom_faqs)} custom FAQs")

            # ═══════════════════════════════════════════════════════════════
            # LIVE HANDOFF VIEW
            # ═══════════════════════════════════════════════════════════════
            if st.session_state.show_handoffs:
                st.markdown("### 🤝 Live Agent Handoffs")
                handoffs = get_pending_handoffs()

                if handoffs:
                    st.markdown(f"**{len(handoffs)} pending handoff{'s' if len(handoffs) != 1 else ''}**")
                    for h in handoffs:
                        status_badge = "🟡 Pending" if h["status"] == "pending" else "🔵 Assigned"
                        with st.expander(f"{status_badge} — {html.escape(h['user_name'])} — {html.escape(h['user_email'])}"):
                            st.markdown(f"**Question:** {html.escape(h['user_question'][:200])}")

                            # Show conversation
                            for msg in h["messages"]:
                                if msg["role"] == "user":
                                    st.markdown(f"**{html.escape(h['user_name'])}:** {html.escape(msg['text'][:300])}")
                                else:
                                    st.markdown(f"**🧑‍💼 Agent:** {msg['text']}")

                            # Agent reply form
                            with st.form(key=f"handoff_reply_{h['id']}"):
                                agent_msg = st.text_area("Your response:", key=f"agent_msg_{h['id']}", placeholder="Type your reply...")
                                col_r, col_x = st.columns([1, 1])
                                with col_r:
                                    if st.form_submit_button("📨 Send Reply", type="primary", use_container_width=True):
                                        if agent_msg:
                                            add_agent_response(h["id"], agent_msg)
                                            st.success(f"✅ Response sent to {h['user_name']}!")
                                            st.rerun()
                                with col_x:
                                    if st.form_submit_button("✅ Mark Resolved", use_container_width=True):
                                        resolve_handoff(h["id"])
                                        st.rerun()

                            st.caption(f"Created: {h.get('created_at', 'unknown')}")
                else:
                    st.success("🎉 No pending handoffs! All customers are being helped by the bot.")
                    st.markdown("When a customer asks something the bot can't answer, their conversation will appear here for you to respond to.")

        # ── FOOTER ─────────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown(
            f"<div style='text-align: center; color: var(--text-secondary); font-size: 0.72rem; opacity: 0.6;'>"
            f"{BOT_NAME} v4.0 • Built with Streamlit 🎈"
            f"</div>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CHAT AREA
# ═══════════════════════════════════════════════════════════════════════════════

# ─── HEADER ─────────────────────────────────────────────────────────────────

if EMBED_MODE:
    st.markdown(
        f"<div class='chat-header' style='position:relative;'>"
        f"<button onclick='window.sbClose()' "
        f"style='position:absolute;top:4px;right:4px;width:28px;height:28px;"
        f"border-radius:50%;border:none;background:rgba(0,0,0,0.06);"
        f"cursor:pointer;font-size:14px;color:#64748b;display:flex;"
        f"align-items:center;justify-content:center;transition:all 0.2s;"
        f"z-index:999;line-height:1;'"
        f"title='Close chat' aria-label='Close chat'>"
        f"✕</button>"
        f"<span class='avatar'>{BOT_AVATAR}</span>"
        f"<h1>{BUSINESS_NAME} Support</h1>"
        f"</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"<div class='chat-header'>"
        f"<span class='avatar'>{BOT_AVATAR}</span>"
        f"<h1>{BUSINESS_NAME} Support</h1>"
        f"<p class='tagline'>{BUSINESS_TAGLINE}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

# ─── DISPLAY CHAT HISTORY ───────────────────────────────────────────────────

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "typing":
            st.markdown(
                "<div class='typing-indicator'>"
                "<div class='typing-dot'></div>"
                "<div class='typing-dot'></div>"
                "<div class='typing-dot'></div>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            content = html.escape(message['content']) if message["role"] == "user" else message['content']
            st.markdown(
                f"<div class='chat-bubble'>{content}</div>",
                unsafe_allow_html=True,
            )
            # Show feedback buttons on bot responses
            if message["role"] == "assistant" and message.get("id"):
                col1, col2 = st.columns([1, 10])
                with col1:
                    st.button("👍", key=f"fb_up_{message['id']}",
                              on_click=lambda _id=message['id']: (
                                  log_feedback("up"),
                                  st.session_state.feedback_log.append("up"),
                                  st.toast("Glad I could help! 😊")
                              ))
                with col2:
                    st.button("👎", key=f"fb_down_{message['id']}",
                              on_click=lambda _id=message['id']: (
                                  log_feedback("down"),
                                  st.session_state.feedback_log.append("down"),
                                  st.toast("Thanks — I'll learn from this! 💪")
                              ))

# ─── AGENT HANDOFF RESPONSE ────────────────────────────────────────────────
# Check if the user has pending agent responses to display
if st.session_state.last_lead_captured and ENABLE_HANDOFF:
    agent_email = st.session_state.last_lead_captured.get("email", "")
    if agent_email:
        agent_text, handoff_id = get_agent_responses_for_user(agent_email)
        if agent_text:
            # Check if we've already shown this response
            last_shown_key = f"_last_agent_response_{handoff_id}"
            if st.session_state.get(last_shown_key) != agent_text:
                with st.chat_message("assistant"):
                    st.markdown(
                        f"<div class='chat-bubble'><b>🧑‍💼 Agent:</b> {agent_text}</div>",
                        unsafe_allow_html=True,
                    )
                st.session_state[last_shown_key] = agent_text

# ─── LEAD CAPTURE FORM (shown inline when triggered) ───────────────────────

if st.session_state.show_lead_form and CAPTURE_LEADS:
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='lead-capture-form'>"
        f"<h4>📬 Let us get back to you!</h4>"
        f"<p>Leave your details and we'll follow up within 24 hours.</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.form(key="lead_capture_form"):
        col1, col2 = st.columns(2)
        with col1:
            lead_name = st.text_input("👤 Your Name *")
        with col2:
            lead_email = st.text_input("📧 Your Email *")

        lead_phone = ""
        lead_company = ""
        if REQUIRE_PHONE:
            lead_phone = st.text_input("📞 Phone Number")
        if REQUIRE_COMPANY:
            lead_company = st.text_input("🏢 Company Name")

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submitted = st.form_submit_button("📨 Send", type="primary", use_container_width=True)
        with col2:
            skipped = st.form_submit_button("Skip", use_container_width=True)

        if submitted:
            if lead_name and lead_email:
                last_question = ""
                for msg in reversed(st.session_state.messages):
                    if msg["role"] == "user":
                        last_question = msg["content"]
                        break
                capture_lead_from_form(lead_name, lead_email, lead_phone, lead_company, last_question)
                st.session_state.show_lead_form = False
                st.rerun()
            else:
                st.error("Please enter your name and email.")
        if skipped:
            st.session_state.show_lead_form = False
            st.session_state.lead_capture_pending = False
            st.rerun()

# ─── LEAD CAPTURED SUCCESS MESSAGE ─────────────────────────────────────────

if st.session_state.last_lead_captured:
    lead = st.session_state.last_lead_captured
    email_msg = st.session_state.pop("_email_result", None)

    if email_msg:
        st.success(email_msg)
    else:
        st.success(
            f"✅ Thanks {lead['name']}! We'll get back to you at **{lead['email']}** within 24 hours. 🙌"
        )

    # Show handoff message if enabled
    if st.session_state.handoff_requested and ENABLE_HANDOFF:
        st.info(f"🧑‍💼 {HANDOFF_MESSAGE}")

    if st.button("Continue chatting", use_container_width=True, key="dismiss_lead"):
        st.session_state.last_lead_captured = None
        st.rerun()

# ─── CHAT INPUT ─────────────────────────────────────────────────────────────

# ─── CLOSE CHAT BUTTON (embed mode only) ────────────────────────────────

if EMBED_MODE and st.session_state.messages and not st.session_state.last_lead_captured:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✕ Close Chat", use_container_width=True, type="secondary", key="close_chat_btn"):
            st.markdown(
                "<script>window.sbClose();</script>",
                unsafe_allow_html=True,
            )

if not st.session_state.last_lead_captured:
    if prompt := st.chat_input(f"Ask me about {BUSINESS_NAME}..."):
        # ── Send typing indicator to parent widget (embed mode) ───────────
        if EMBED_MODE:
            st.markdown(
                "<script>try { parent.postMessage('sb-typing', '*'); } catch(e) {}</script>",
                unsafe_allow_html=True,
            )

        # ── Multi-language processing ───────────────────────────────────────
        original_prompt = prompt
        translated_prompt, detected_lang, response_lang = process_multilingual(prompt)
        st.session_state.user_language = detected_lang or "en"

        # Log conversation start (first message only)
        if not st.session_state.analytics_logged_conversation:
            log_conversation_started()
            st.session_state.analytics_logged_conversation = True

        # Show language indicator if not English
        if detected_lang and detected_lang != "en" and ENABLE_TRANSLATION:
            flag_map = {"es": "🇪🇸", "fr": "🇫🇷", "de": "🇩🇪", "pt": "🇵🇹",
                        "ja": "🇯🇵", "ko": "🇰🇷", "zh-cn": "🇨🇳", "it": "🇮🇹",
                        "nl": "🇳🇱", "ru": "🇷🇺", "ar": "🇸🇦", "hi": "🇮🇳"}
            flag = flag_map.get(detected_lang, "🌐")
            st.caption(f"{flag} Detected: {detected_lang.upper()}")

        # Use the translated prompt for matching (or original if English)
        match_prompt = translated_prompt if ENABLE_TRANSLATION else original_prompt

        # ── Handle user message ────────────────────────────────────────────
        # Store original message (not translated one) in history
        st.session_state.messages.append({"role": "user", "content": original_prompt})
        st.session_state.questions_asked += 1

        with st.chat_message("user"):
            safe_prompt = html.escape(original_prompt)
            st.markdown(
                f"<div class='chat-bubble'>{safe_prompt}</div>",
                unsafe_allow_html=True,
            )

        # ── Check for goodbye/end signals ──────────────────────────────────
        goodbye_keywords = ["bye", "goodbye", "see you", "that's all", "no thanks",
                            "i'm done", "that's it", "thanks bye", "done"]
        is_goodbye = any(kw in original_prompt.lower() for kw in goodbye_keywords)

        # ── Generate bot response ─────────────────────────────────────────
        match = find_best_match(match_prompt, context=st.session_state.conversation_context)

        with st.chat_message("assistant"):
            if match:
                response = match["answer"]
                # Translate response to user's language if needed
                if response_lang != "en" and ENABLE_TRANSLATION:
                    translated_response = translate_response(response, response_lang)
                    if translated_response and translated_response != response:
                        response = translated_response

                st.markdown(
                    f"<div class='chat-bubble'>{response}</div>",
                    unsafe_allow_html=True,
                )
                st.session_state.resolved_count += 1
                log_conversation_resolved(match["question"])
                st.session_state.conversation_context = match["question"]

                # If goodbye, gently offer lead capture
                if is_goodbye and CAPTURE_LEADS:
                    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
                    st.markdown(
                        "*💡 Want us to keep you updated? Leave your email and we'll send tips & offers.*"
                    )
                    st.session_state.show_lead_form = True
                    st.session_state.lead_capture_reason = "goodbye"

                # In embed mode, show a close button after goodbye
                if is_goodbye and EMBED_MODE:
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_a, col_b, col_c = st.columns([1, 1, 1])
                    with col_b:
                        st.markdown(
                            "<div style='text-align:center;'>"
                            "<button onclick='window.sbClose()' "
                            "style='padding:6px 20px;border-radius:20px;border:1px solid var(--border);"
                            "background:var(--bg-card);color:var(--text-secondary);cursor:pointer;"
                            "font-size:0.85rem;transition:all 0.2s;'>"
                            "✕ Close Window</button></div>",
                            unsafe_allow_html=True,
                        )
            else:
                # Bot can't answer → trigger lead capture
                response = format_cant_answer_response()
                if response_lang != "en" and ENABLE_TRANSLATION:
                    translated_response = translate_response(response, response_lang)
                    if translated_response and translated_response != response:
                        response = translated_response

                st.markdown(
                    f"<div class='chat-bubble'>{response}</div>",
                    unsafe_allow_html=True,
                )
                st.session_state.unresolved_count += 1
                log_unresolved()
                if CAPTURE_LEADS:
                    st.session_state.show_lead_form = True
                    st.session_state.lead_capture_reason = "unanswered"

            # Add bot message to history (store the final response as-is)
            msg_id = random.randint(10000, 99999)
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "id": msg_id,
            })
            st.session_state.pending_notification = json.dumps(response)

        st.rerun()

# ─── SUGGESTIONS (empty chat) ───────────────────────────────────────────────

if not st.session_state.messages and not st.session_state.last_lead_captured:
    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)
    st.markdown("#### 💬 Try asking:")
    suggestions = [
        "What do you offer?",
        "How much does it cost?",
        "How do I get started?",
        "I need help with something",
    ]
    st.markdown("<div class='suggestion-grid'>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"💬 {suggestion}", use_container_width=True, key=f"sg_{i}"):
                st.session_state.messages.append({"role": "user", "content": suggestion})
                st.session_state.questions_asked += 1
                match = find_best_match(suggestion, context=st.session_state.conversation_context)
                if match:
                    bot_response = match["answer"]
                    st.session_state.resolved_count += 1
                    log_conversation_resolved(match["question"])
                    st.session_state.conversation_context = match["question"]
                else:
                    bot_response = format_cant_answer_response()
                    st.session_state.unresolved_count += 1
                    log_unresolved()
                    if CAPTURE_LEADS:
                        st.session_state.show_lead_form = True
                        st.session_state.lead_capture_reason = "unanswered"
                msg_id = random.randint(10000, 99999)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": bot_response,
                    "id": msg_id,
                })
                st.session_state.pending_notification = json.dumps(bot_response)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
