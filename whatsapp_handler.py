"""
WHATSAPP HANDLER — FastAPI server that bridges Twilio WhatsApp with the support-bot.

Architecture:
    WhatsApp user → Twilio → [this FastAPI server] → knowledge_base (FAQ match)
                                              → leads_manager (lead capture)
                                              → analytics (conversation tracking)

Run with:
    uvicorn whatsapp_handler:app --host 0.0.0.0 --port 8000

For local development, expose with ngrok:
    ngrok http 8000
    Then set the ngrok URL as your Twilio WhatsApp webhook.

Required env vars (set in .env or environment):
    TWILIO_ACCOUNT_SID=your_account_sid
    TWILIO_AUTH_TOKEN=your_auth_token
    TWILIO_WHATSAPP_NUMBER=+14155238886  (Twilio sandbox number)
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
import uvicorn

# ─── Twilio (optional — graceful fallback if not installed) ────────────────
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None

# ─── Load environment variables ────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── Bot modules (same codebase as the Streamlit app) ─────────────────────
from knowledge_base import find_best_match, get_all_faqs
from leads_manager import LeadsManager
from business_config import (
    BUSINESS_NAME, BUSINESS_TAGLINE, SUPPORT_EMAIL, SUPPORT_PHONE,
    SUPPORT_HOURS, WEBSITE_URL, BOT_NAME,
    ENABLE_TRANSLATION, DEFAULT_LANGUAGE,
    CAPTURE_LEADS, REQUIRE_PHONE,
    WHATSAPP_ENABLED,
)
from analytics import (
    log_conversation_started, log_conversation_resolved,
    log_unresolved, log_lead_captured, log_language,
    log_whatsapp_message, get_whatsapp_analytics,
    reset_whatsapp_analytics, export_whatsapp_analytics_json,
)

# ─── Logging setup ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("whatsapp_handler")

# ─── Twilio credentials from env ───────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")

# ─── FastAPI app ───────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{BUSINESS_NAME} WhatsApp Bot",
    description="Twilio WhatsApp webhook handler for the support-bot",
    version="1.0.0",
)

# ─── Shared lead manager ───────────────────────────────────────────────────
db = LeadsManager()

# ─── Session state store ───────────────────────────────────────────────────
# Maps phone number -> session dict
# In production, use Redis or a database. This is fine for small deployments.
SESSIONS: dict[str, dict] = {}

# Optional: persist sessions to disk for restarts
SESSIONS_FILE = os.path.join(os.path.dirname(__file__), "whatsapp_sessions.json")

# Session states for lead capture flow
STATE_CHATTING = "chatting"              # Normal conversation
STATE_AWAITING_NAME = "awaiting_name"    # Bot asked for name, waiting for response
STATE_AWAITING_EMAIL = "awaiting_email"  # Bot asked for email, waiting for response
STATE_AWAITING_PHONE = "awaiting_phone"  # (optional) Bot asked for phone


def _load_sessions():
    """Load sessions from disk if available."""
    global SESSIONS
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, "r") as f:
                SESSIONS = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        SESSIONS = {}


def _save_sessions():
    """Persist sessions to disk."""
    try:
        # Limit to 1000 sessions to prevent unbounded growth
        sessions_to_save = dict(list(SESSIONS.items())[-1000:])
        with open(SESSIONS_FILE, "w") as f:
            json.dump(sessions_to_save, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to persist sessions: {e}")


# Load existing sessions on startup
_load_sessions()

# Check WhatsApp config
if not WHATSAPP_ENABLED:
    logger.warning(
        "WHATSAPP_ENABLED is set to False in business_config.py. "
        "Set it to True once you've configured your Twilio credentials."
    )
if TWILIO_AVAILABLE and TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER:
    logger.info(f"Twilio configured — WhatsApp bot ready (number: {TWILIO_WHATSAPP_NUMBER})")
else:
    logger.warning(
        "Twilio credentials not fully configured. "
        "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER in .env"
    )


def get_or_create_session(phone: str) -> dict:
    """Get or create a session for a phone number."""
    if phone not in SESSIONS:
        SESSIONS[phone] = {
            "state": STATE_CHATTING,
            "conversation_context": None,
            "pending_question": "",
            "lead_name": "",
            "lead_email": "",
            "lead_phone": "",
            "created_at": datetime.now().isoformat(),
            "messages_sent": 0,
            "analytics_logged": False,
        }
        _save_sessions()
    return SESSIONS[phone]


def send_whatsapp_message(to_number: str, message: str):
    """Send a WhatsApp message via Twilio.

    Falls back gracefully if Twilio is not configured.
    """
    if not TWILIO_AVAILABLE:
        logger.warning("Twilio not installed. Message would be sent:")
        logger.warning(f"  To: {to_number}")
        logger.warning(f"  Body: {message[:100]}...")
        return

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_WHATSAPP_NUMBER:
        logger.warning("Twilio credentials not configured. Cannot send message.")
        return

    try:
        client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{to_number}",
        )
        logger.info(f"Sent WhatsApp message to {to_number}")
        # Track sent message in WhatsApp analytics
        log_whatsapp_message(to_number, "sent")
    except Exception as e:
        logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")


def get_welcome_message() -> str:
    """Return the welcome message for new WhatsApp conversations."""
    return (
        f"👋 Welcome to {BUSINESS_NAME}!\n\n"
        f"{BUSINESS_TAGLINE}\n\n"
        f"I can help you with:\n"
        f"💰 Pricing & Plans\n"
        f"⚙️ Features & Integrations\n"
        f"👤 Account & Billing\n"
        f"❓ Troubleshooting\n\n"
        f"Just type your question, or say *'help'* to see what I can do! 🚀"
    )


def get_cant_answer_message() -> str:
    """Response when the bot can't find a match."""
    return (
        "🤔 I'm not sure about that one.\n\n"
        "No worries — I can connect you with a human agent who can help!\n\n"
        "First, could you tell me your **name** so they know who to look for?"
        " (Reply *'skip'* if you'd rather not share)"
    )


def get_lead_success_message(name: str) -> str:
    """Confirmation message after lead capture."""
    return (
        f"✅ Thanks {name}! A member of our team will follow up with you "
        f"within 24 hours. 🙌\n\n"
        f"Is there anything else I can help with?"
    )


def process_message(phone: str, message_text: str) -> str:
    """Process an incoming WhatsApp message and return the bot response.

    This is the core conversation logic, using the same knowledge_base
    and state machine as the Streamlit chat bot.
    """
    session = get_or_create_session(phone)
    text = message_text.strip().lower()
    session["messages_sent"] += 1

    # Track received message in WhatsApp analytics (all inbound messages)
    log_whatsapp_message(phone, "received")

    # Log analytics for first message
    if not session["analytics_logged"]:
        log_conversation_started()
        session["analytics_logged"] = True

    # ─── STATE: Awaiting name (lead capture flow) ──────────────────────────
    if session["state"] == STATE_AWAITING_NAME:
        if text in ("no", "nope", "skip", "cancel", "nah", "nevermind", "forget it"):
            session["state"] = STATE_CHATTING
            _save_sessions()
            return "No problem! Feel free to ask more questions anytime. 😊"

        session["lead_name"] = message_text.strip()
        session["state"] = STATE_AWAITING_EMAIL
        _save_sessions()
        return "Great, thanks! What's your **email address** so we can reach you?"

    # ─── STATE: Awaiting email (lead capture flow) ─────────────────────────
    if session["state"] == STATE_AWAITING_EMAIL:
        if "@" not in text or "." not in text:
            return "That doesn't look like a valid email. Could you please enter a valid email address?"

        session["lead_email"] = message_text.strip()

        if REQUIRE_PHONE:
            session["state"] = STATE_AWAITING_PHONE
            _save_sessions()
            return "Almost done! What's your **phone number**? (Optional — just type 'skip' if you'd prefer not to share)"
        else:
            # Capture the lead
            lead = db.add_lead(
                name=session["lead_name"],
                email=session["lead_email"],
                question=session.get("pending_question", ""),
                source="whatsapp",
            )
            log_lead_captured()
            session["state"] = STATE_CHATTING
            session["pending_question"] = ""
            _save_sessions()
            return get_lead_success_message(session["lead_name"])

    # ─── STATE: Awaiting phone (optional) ─────────────────────────────────
    if session["state"] == STATE_AWAITING_PHONE:
        phone = "" if text in ("skip", "no", "nope") else message_text.strip()

        lead = db.add_lead(
            name=session["lead_name"],
            email=session["lead_email"],
            phone=phone,
            question=session.get("pending_question", ""),
            source="whatsapp",
        )
        log_lead_captured()
        session["state"] = STATE_CHATTING
        session["pending_question"] = ""
        _save_sessions()
        return get_lead_success_message(session["lead_name"])

    # ─── STATE: Normal chatting mode ──────────────────────────────────────
    # Check for goodbye
    goodbye_keywords = ["bye", "goodbye", "see you", "later", "take care"]
    is_goodbye = any(kw in text for kw in goodbye_keywords)

    if is_goodbye:
        session["state"] = STATE_CHATTING
        session["conversation_context"] = None
        _save_sessions()
        return (
            "Take care! 👋 If you ever need help, just message me anytime.\n\n"
            f"📧 {SUPPORT_EMAIL}\n"
            f"🌐 {WEBSITE_URL}\n\n"
            "Have a great day! 🚀"
        )

    # Handle "human" / "agent" requests
    if any(kw in text for kw in ["human", "agent", "real person", "representative"]):
        # Start lead capture
        session["state"] = STATE_AWAITING_NAME
        session["pending_question"] = message_text
        _save_sessions()
        return (
            "I'll connect you with a human agent! 🧑‍💼\n\n"
            "First, could you tell me your **name** so they know who to look for?"
        )

    # Match against FAQ using the existing knowledge base
    match = find_best_match(text, context=session.get("conversation_context"))

    if match:
        response = match["answer"]
        session["conversation_context"] = match["question"]
        log_conversation_resolved(match["question"])
        _save_sessions()
        return response

    # No match found → suggest lead capture
    if CAPTURE_LEADS:
        session["pending_question"] = message_text
        session["state"] = STATE_AWAITING_NAME
        log_unresolved()
        _save_sessions()
        return get_cant_answer_message()

    # If lead capture is disabled, give contact info
    log_unresolved()
    return (
        "🤔 I'm not sure about that one.\n\n"
        f"Here's how to reach us:\n"
        f"📧 {SUPPORT_EMAIL}\n"
        f"📞 {SUPPORT_PHONE} ({SUPPORT_HOURS})\n"
        f"🌐 {WEBSITE_URL}\n\n"
        f"Feel free to ask me something else!"
    )


# ─── REST API Endpoints ────────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Health check endpoint — use this to verify the server is running."""
    return {
        "status": "ok",
        "service": f"{BUSINESS_NAME} WhatsApp Bot",
        "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN),
        "active_sessions": len(SESSIONS),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/whatsapp", response_class=PlainTextResponse)
async def whatsapp_webhook(
    request: Request,
    Body: str = Form(""),
    From: str = Form(""),
    MessageSid: Optional[str] = Form(None),
    ProfileName: Optional[str] = Form(None),
):
    """Twilio WhatsApp webhook — receives incoming messages and replies.

    Twilio sends a POST with form-encoded body containing:
    - Body: The message text
    - From: The sender's WhatsApp number (e.g., 'whatsapp:+1234567890')
    - MessageSid: Twilio's message ID
    - ProfileName: Sender's WhatsApp profile name (if available)
    """
    if not Body or not From:
        logger.warning("Received empty message or missing sender")
        return PlainTextResponse("OK")

    # Strip 'whatsapp:' prefix if present
    phone = From.replace("whatsapp:", "").strip()
    message = Body.strip()

    logger.info(f"Received WhatsApp message from {phone}: {message[:100]}")

    if not phone:
        logger.warning("Could not parse phone number from From header")
        return PlainTextResponse("OK")

    try:
        # Check if this is a new conversation
        is_new = phone not in SESSIONS

        # Process the message (tracking is handled inside process_message)
        response = process_message(phone, message)

        # Send the response
        if response:
            # If it's a new conversation, prepend welcome
            if is_new:
                welcome = get_welcome_message()
                full_response = f"{welcome}\n\n---\n\n{response}"
            else:
                full_response = response

            send_whatsapp_message(phone, full_response)

    except Exception as e:
        logger.error(f"Error processing message from {phone}: {e}", exc_info=True)
        # Send a fallback message so the user knows something went wrong
        send_whatsapp_message(
            phone,
            "Sorry, I encountered an error processing your message. "
            "Please try again in a moment, or email us at "
            f"{SUPPORT_EMAIL} for assistance.",
        )

    # Twilio expects a TwiML or plaintext response
    # We return plaintext OK since we're sending replies via the REST API
    # (not via TwiML <Message> verb)
    return PlainTextResponse("OK")


# For backwards compatibility and easy testing
@app.post("/webhook", response_class=PlainTextResponse)
async def generic_webhook(request: Request):
    """Generic webhook that supports both form-encoded and JSON payloads.

    This allows more flexibility than the Twilio-specific /whatsapp endpoint.
    """
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
        body = data.get("Body", data.get("message", data.get("text", "")))
        sender = data.get("From", data.get("from", data.get("sender", "")))
    else:
        form = await request.form()
        body = form.get("Body", form.get("message", form.get("text", "")))
        sender = form.get("From", form.get("from", form.get("sender", "")))

    if body and sender:
        phone = sender.replace("whatsapp:", "").strip()
        response = process_message(phone, body.strip())
        if response:
            send_whatsapp_message(phone, response)
        return {"status": "ok", "response": response[:100] if response else ""}

    return {"status": "error", "message": "Missing Body or From fields"}


@app.get("/sessions")
async def list_sessions():
    """List active WhatsApp sessions (for debugging)."""
    summary = []
    for phone, session in SESSIONS.items():
        summary.append({
            "phone": phone[-4:],  # Only show last 4 digits for privacy
            "state": session["state"],
            "messages_sent": session["messages_sent"],
            "created_at": session.get("created_at", ""),
        })
    return {
        "total_sessions": len(summary),
        "sessions": summary[-20:],  # Show latest 20
    }


@app.get("/sessions/{phone}")
async def get_session(phone: str):
    """Get session details for a specific phone number."""
    if phone in SESSIONS:
        session = dict(SESSIONS[phone])
        # Remove captured lead info for privacy on inspection
        session.pop("lead_name", None)
        session.pop("lead_email", None)
        session.pop("lead_phone", None)
        return session
    raise HTTPException(status_code=404, detail="Session not found")


# ─── CLI entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting WhatsApp handler on port {port}")
    uvicorn.run(
        "whatsapp_handler:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
