"""
AUDIT LOG — Records admin actions with timestamps for security auditing.

Provides a simple append-only JSON log of all admin actions.
Supports the security recommendation from SECURITY.md (finding #11).

Usage:
    from audit_log import log_admin_action
    log_admin_action("Marked lead as contacted", {"lead_id": "...", "lead_name": "John"})
"""

import json
import os
from datetime import datetime

AUDIT_LOG_FILE = os.path.join(os.path.dirname(__file__), "audit_log.json")
_MAX_LOG_ENTRIES = 10000  # Prevent unbounded growth


def _ensure_file():
    """Create the audit log file if it doesn't exist."""
    if not os.path.exists(AUDIT_LOG_FILE):
        _write([])


def _read():
    """Read all audit log entries."""
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write(entries):
    """Write audit log entries to file."""
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def log_admin_action(action, details=None):
    """Record an admin action in the audit log.

    Args:
        action: Short description of the action (e.g., "Marked lead as contacted")
        details: Optional dict with extra context (lead_id, lead_name, etc.)
    """
    _ensure_file()
    entries = _read()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "details": details or {},
    }
    entries.append(entry)

    # Trim oldest entries if over the limit
    if len(entries) > _MAX_LOG_ENTRIES:
        entries = entries[-_MAX_LOG_ENTRIES:]

    _write(entries)


def get_audit_log(limit=50):
    """Get the most recent audit log entries.

    Args:
        limit: Max number of entries to return (newest first)
    """
    entries = _read()
    return list(reversed(entries))[:limit]


def get_audit_summary():
    """Get a summary of audit log stats."""
    entries = _read()
    if not entries:
        return {"total_actions": 0, "unique_actions": [], "last_24h": 0}

    now = datetime.now()
    last_24h = sum(
        1 for e in entries
        if (now - datetime.fromisoformat(e["timestamp"])).total_seconds() < 86400
    )

    actions = {}
    for e in entries:
        action = e["action"]
        actions[action] = actions.get(action, 0) + 1

    return {
        "total_actions": len(entries),
        "unique_actions": sorted(actions.items(), key=lambda x: x[1], reverse=True),
        "last_24h": last_24h,
    }


def export_audit_json():
    """Export the full audit log as JSON string."""
    return json.dumps(_read(), indent=2, default=str)
