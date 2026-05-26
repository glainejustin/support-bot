"""
ANALYTICS — Tracks conversation metrics and generates chart data.

Stores data in analytics_data.json so it persists between page refreshes.
Metrics tracked:
  - Total conversations started
  - Resolved vs unanswered rates
  - Popular FAQ topics
  - Feedback stats (thumbs up/down)
  - Lead conversion rate
  - Language distribution (when multi-language enabled)
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter

ANALYTICS_FILE = os.path.join(os.path.dirname(__file__), "analytics_data.json")


def _ensure_file():
    if not os.path.exists(ANALYTICS_FILE):
        _write({
            "conversations": [],
            "feedback": {"up": 0, "down": 0},
            "faq_hits": {},           # question text -> count
            "unmatched_count": 0,
            "lead_captures": 0,
            "languages": {},          # language code -> count
            "daily_stats": {},        # "2024-01-15" -> {"chats": N, "resolved": N, "leads": N}
        })


def _read():
    try:
        with open(ANALYTICS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        _ensure_file()
        return _read()


def _write(data):
    with open(ANALYTICS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def log_conversation_started():
    """Log that a new conversation was started."""
    data = _read()
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in data["daily_stats"]:
        data["daily_stats"][today] = {"chats": 0, "resolved": 0, "unresolved": 0, "leads": 0}
    data["daily_stats"][today]["chats"] = data["daily_stats"][today].get("chats", 0) + 1
    data["conversations"].append({
        "started_at": datetime.now().isoformat(),
        "resolved": False,
        "faq_used": None,
    })
    _write(data)


def log_conversation_resolved(faq_question=None):
    """Mark the latest conversation as resolved."""
    data = _read()
    today = datetime.now().strftime("%Y-%m-%d")
    if today in data["daily_stats"]:
        data["daily_stats"][today]["resolved"] = data["daily_stats"][today].get("resolved", 0) + 1
    if data["conversations"]:
        data["conversations"][-1]["resolved"] = True
        data["conversations"][-1]["faq_used"] = faq_question
    if faq_question:
        data["faq_hits"][faq_question] = data["faq_hits"].get(faq_question, 0) + 1
    _write(data)


def log_unresolved():
    """Mark the latest conversation as unresolved."""
    data = _read()
    today = datetime.now().strftime("%Y-%m-%d")
    if today in data["daily_stats"]:
        data["daily_stats"][today]["unresolved"] = data["daily_stats"][today].get("unresolved", 0) + 1
    data["unmatched_count"] = data["unmatched_count"] + 1
    _write(data)


def log_feedback(vote):
    """Log a thumbs up/down."""
    data = _read()
    data["feedback"][vote] = data["feedback"].get(vote, 0) + 1
    _write(data)


def log_lead_captured():
    """Log that a lead was captured."""
    data = _read()
    today = datetime.now().strftime("%Y-%m-%d")
    if today not in data["daily_stats"]:
        data["daily_stats"][today] = {"chats": 0, "resolved": 0, "unresolved": 0, "leads": 0}
    data["daily_stats"][today]["leads"] = data["daily_stats"][today].get("leads", 0) + 1
    data["lead_captures"] = data["lead_captures"] + 1
    _write(data)


def log_language(lang_code):
    """Log a detected language."""
    if not lang_code:
        return
    data = _read()
    data["languages"][lang_code] = data["languages"].get(lang_code, 0) + 1
    _write(data)


def get_summary():
    """Return a summary dict of all analytics data."""
    data = _read()
    total_conversations = len(data["conversations"])
    resolved = sum(1 for c in data["conversations"] if c.get("resolved"))
    unresolved = total_conversations - resolved

    # Calculate resolution rate
    resolution_rate = (resolved / total_conversations * 100) if total_conversations > 0 else 0

    # Top FAQs
    top_faqs = sorted(data["faq_hits"].items(), key=lambda x: x[1], reverse=True)[:10]

    # Daily chart data (last 14 days)
    daily_data = []
    for i in range(13, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        stats = data["daily_stats"].get(day, {"chats": 0, "resolved": 0, "unresolved": 0, "leads": 0})
        daily_data.append({
            "date": day,
            "chats": stats.get("chats", 0),
            "resolved": stats.get("resolved", 0),
            "leads": stats.get("leads", 0),
        })

    return {
        "total_conversations": total_conversations,
        "resolved": resolved,
        "unresolved": unresolved,
        "resolution_rate": round(resolution_rate, 1),
        "lead_captures": data["lead_captures"],
        "unmatched_count": data["unmatched_count"],
        "feedback_ups": data["feedback"].get("up", 0),
        "feedback_downs": data["feedback"].get("down", 0),
        "top_faqs": top_faqs,
        "daily_data": daily_data,
        "languages": data.get("languages", {}),
    }


def reset_analytics():
    """Wipe all analytics data."""
    _write({
        "conversations": [],
        "feedback": {"up": 0, "down": 0},
        "faq_hits": {},
        "unmatched_count": 0,
        "lead_captures": 0,
        "languages": {},
        "daily_stats": {},
    })


def export_analytics_json():
    """Return analytics as JSON string for download."""
    return json.dumps(_read(), indent=2)
