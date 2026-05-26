"""
EMAIL SENDER — Sends automated follow-up emails to captured leads using Resend.

Requires:
  1. A free Resend account (resend.com) — 3,000 emails/month free
  2. An API key (starts with "re_")

Set the API key via one of these methods (checked in order):
  A. Environment variable:  RESEND_API_KEY="re_..." in .env file
  B. Streamlit secrets:     [resend]\n                            api_key = "re_..." in .streamlit/secrets.toml
  C. Streamlit Cloud:       Settings \u2192 Secrets (same TOML format as B)

Usage:
    from email_sender import send_followup_email
    success, message = send_followup_email("John", "john@email.com", "Need pricing")
"""

import os
import streamlit as st
from business_config import (
    BUSINESS_NAME,
    SUPPORT_EMAIL,
    WEBSITE_URL,
    FOLLOW_UP_SUBJECT,
    FOLLOW_UP_BODY,
)


def get_resend_api_key():
    """Get the Resend API key from env var, then Streamlit secrets."""
    # Check .env / environment variable first (for local dev)
    env_key = os.environ.get("RESEND_API_KEY")
    if env_key:
        return env_key
    # Fallback to Streamlit secrets (for Streamlit Cloud and secrets.toml)
    try:
        return st.secrets["resend"]["api_key"]
    except (KeyError, FileNotFoundError):
        return None


def send_followup_email(lead_name, lead_email, lead_question="", lead_phone=""):
    """
    Send a follow-up email to a captured lead using Resend.

    Returns: (success: bool, message: str)
    """
    api_key = get_resend_api_key()
    if not api_key:
        return False, (
            "❌ Resend API key not configured.\n\n"
            "To set it up:\n"
            "1. Sign up at resend.com (free)\n"
            "2. Create an API key\n"
            "3. Add it to .streamlit/secrets.toml:\n\n"
            "   [resend]\n"
            "   api_key = \"re_...\""
        )

    try:
        import resend

        resend.api_key = api_key

        # Personalize the email body
        personalized_body = FOLLOW_UP_BODY
        personalized_body = personalized_body.replace("{name}", lead_name)
        personalized_body = personalized_body.replace("{BUSINESS_NAME}", BUSINESS_NAME)
        personalized_body = personalized_body.replace("{WEBSITE_URL}", WEBSITE_URL)

        if lead_question:
            personalized_body = personalized_body.replace(
                "{question}", f'<blockquote style="color: #666; font-style: italic;">"{lead_question}"</blockquote>'
            )
        else:
            personalized_body = personalized_body.replace("{question}", "")
        if lead_phone:
            personalized_body = personalized_body.replace("{phone}", f"📞 Phone: {lead_phone}<br>")
        else:
            personalized_body = personalized_body.replace("{phone}", "")

        params = {
            "from": SUPPORT_EMAIL,
            "to": [lead_email],
            "subject": FOLLOW_UP_SUBJECT.replace("{name}", lead_name),
            "html": personalized_body,
        }

        response = resend.Emails.send(params)
        return True, f"✅ Email sent to {lead_email} (ID: {response.get('id', 'ok')})"

    except Exception as e:
        error_msg = str(e)
        # Check for common errors
        if "api key" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return False, (
                "❌ Invalid Resend API key.\n\n"
                "Check your API key in .streamlit/secrets.toml.\n"
                f"Error: {error_msg}"
            )
        if "sender" in error_msg.lower() or "from" in error_msg.lower():
            return False, (
                "❌ Invalid sender email.\n\n"
                f"The 'from' address is set to: {SUPPORT_EMAIL}\n"
                "On Resend's free tier, you must verify your domain or "
                "use their default 'onboarding@resend.dev' sender.\n\n"
                f"Error: {error_msg}"
            )
        return False, f"❌ Failed to send email: {error_msg}"
