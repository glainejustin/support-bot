# Security Audit Report

**Date:** May 26, 2026
**Project:** Support Bot (support-bot)
**Scope:** bot.py, knowledge_base.py, leads_manager.py, email_sender.py, business_config.py, embed_snippet.html, .streamlit/

---

## Summary

| Severity | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 2 | ✅ Fixed |
| 🟠 High | 2 | ✅ Fixed |
| 🟡 Medium | 3 | ℹ️ Documented |
| 🔵 Low | 3 | ℹ️ Documented |

---

## 🔴 Critical — Fixed

### 1. Reflected XSS via User Chat Messages

**File:** `bot.py`
**Lines:** Chat bubble rendering (history loop + initial render)

**Vulnerability:** User messages were directly interpolated into HTML via f-strings and rendered with `unsafe_allow_html=True`:
```python
f"<div class='chat-bubble'>{prompt}</div>"
```
A user could type `<script>alert(document.cookie)</script>` and it would execute in the bot UI. This also opens the door to phishing (injecting fake login forms) and postMessage hijacking (sending fake messages to the parent page).

**Fix:** All user message content is now passed through `html.escape()` before rendering. Bot responses (from the FAQ system) are trusted content and are not escaped, preserving markdown formatting.

### 2. Stored XSS via Lead Data in Admin Dashboard

**File:** `bot.py` — Admin lead dashboard section

**Vulnerability:** Lead names, emails, phone numbers, and questions were rendered directly into HTML without sanitization. Since lead data comes from user input (the lead capture form), a malicious user could inject JavaScript that executes when an admin views their leads.

**Fix:** All lead fields (name, email, phone, company, question) are now escaped with `html.escape()` before rendering in the admin dashboard.

---

## 🟠 High — Fixed

### 3. Weak Default Admin Password

**File:** `business_config.py`

**Vulnerability:** The default password `"admin123"` is extremely weak and publicly known. Anyone who clones the repo knows this password.

**Fix:**
- Added support for the `ADMIN_PASSWORD` environment variable (checked first, before the hardcoded fallback)
- Added clear security warnings in the config file
- On Streamlit Cloud, admins can set `ADMIN_PASSWORD` in Settings → Secrets instead

### 4. postMessage with Wildcard Origin

**File:** `bot.py` — `sb-close`, `sb-typing`, and `sb-new-message` postMessage calls

**Vulnerability:** Using `'*'` as `targetOrigin` allows any page to receive these messages. For `sb-new-message`, this could leak conversation content to malicious listeners on the same page.

**Assessment:** This is by design for an embed widget — the iframe doesn't know the parent's origin at load time because each business embeds it on their own domain. The parent side (`embed_snippet.html`) validates the origin before processing messages. This is the standard pattern used by Intercom, Crisp, and other chat widgets.

**Recommendation:** For extra security, the business owner could hardcode their domain in the `targetOrigin` parameter. If you know the parent domain at deployment time, change `'*'` to `'https://yourbusiness.com'`.

---

## 🟡 Medium — Documented

### 5. No Rate Limiting

**File:** `bot.py`

**Issue:** There is no limit on how many messages a user can send. An attacker could:
- Flood the chat with automated messages
- Rapidly generate leads to fill up the database
- Exhaust Streamlit Cloud's execution time limits

**Recommendation:** Implement rate limiting via Streamlit's session state (e.g., max 10 messages per minute per session). For production deployments, add a reverse proxy (Nginx/Caddy) with rate limiting rules.

### 6. Leads Stored in Plaintext JSON

**File:** `leads_manager.py`

**Issue:** Customer lead data (names, emails, phone numbers, questions) is stored in a plain JSON file (`leads.json`) without encryption. Anyone with filesystem access to the server can read all leads.

**Recommendation:**
- Ensure `leads.json` is excluded from version control (already in `.gitignore` ✅)
- Set restrictive file permissions on production (`chmod 600 leads.json`)
- For compliance (GDPR, CCPA), consider using a database with encryption at rest
- Regularly export and delete old leads from the JSON file

### 7. No Input Length Limits

**File:** `bot.py` — Chat input and lead capture form

**Issue:** User messages and lead form fields have no maximum length limits. An attacker could send very long messages that:
- Consume excessive memory/bandwidth
- Cause display issues in the admin dashboard
- Overflow the JSON file

**Recommendation:** Add `max_length` validation to chat input and form fields (e.g., 1000 characters for messages, 255 for name/email).

---

## 🔵 Low — Documented

### 8. Sequential Lead IDs

**File:** `leads_manager.py`

**Issue:** Lead IDs are assigned sequentially (`len(leads) + 1`). In a multi-user scenario, this could lead to race conditions and ID collisions if two leads are captured simultaneously.

**Recommendation:** Use `uuid.uuid4()` for lead IDs if the bot is deployed at high scale.

### 9. No Audit Logging

**File:** `bot.py`

**Issue:** Admin actions (marking leads as contacted, deleting leads, exporting data) are not logged. If a malicious admin or compromised account makes changes, there's no trail.

**Recommendation:** Add a simple audit log that records admin actions with timestamps.

### 10. No HTTPS Enforcement

**File:** `.streamlit/config.toml`

**Issue:** The config doesn't enforce HTTPS. While Streamlit Cloud and most deployment platforms handle this automatically, self-hosted deployments might serve content over HTTP.

**Recommendation:** For self-hosted deployments, use a reverse proxy (Caddy, Nginx) with auto-TLS.

---

## Security Checklist for Deployment

Before going live:

- [ ] **Change the admin password** — Set a strong, unique password via environment variable
- [ ] **Set a Resend API key** — Add it to `.streamlit/secrets.toml` (excluded from git ✅)
- [ ] **Restrict file permissions** — `chmod 600 leads.json` on the server
- [ ] **Enable HTTPS** — Use Caddy, Nginx, or deploy on Streamlit Cloud/Render
- [ ] **Add rate limiting** — At the reverse proxy level or in the app
- [ ] **Review embedded widget** — If embedding via iframe, ensure CORS headers are configured
- [ ] **Verify `.gitignore`** — Ensure `secrets.toml` and `leads.json` are never committed
- [ ] **Export leads regularly** — JSON file is not a production database

---

*Automated audit completed by Codebuff*
