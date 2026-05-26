"""
LEADS MANAGER — Stores and manages customer leads captured by the bot.

Leads are stored in a JSON file so they persist between page refreshes
(but not between app restarts on Streamlit Cloud — export regularly!).

Usage:
    from leads_manager import LeadsManager
    db = LeadsManager()
    db.add_lead("John", "john@email.com", "Need help with pricing")
    all_leads = db.get_all_leads()
    db.mark_contacted(lead_id)
    csv_data = db.export_csv()
"""

import json
import csv
import io
import os
import uuid
from datetime import datetime, timedelta

LEADS_FILE = os.path.join(os.path.dirname(__file__), "leads.json")
ARCHIVED_LEADS_FILE = os.path.join(os.path.dirname(__file__), "archived_leads.json")


class LeadsManager:
    def __init__(self, filepath=LEADS_FILE):
        self.filepath = filepath
        self._ensure_file()
        self._ensure_file_archived()

    def _ensure_file(self):
        """Create the leads file if it doesn't exist."""
        if not os.path.exists(self.filepath):
            self._write([])

    def _ensure_file_archived(self):
        """Create the archived leads file if it doesn't exist."""
        if not os.path.exists(ARCHIVED_LEADS_FILE):
            with open(ARCHIVED_LEADS_FILE, "w") as f:
                json.dump([], f)

    def _read(self):
        """Read all leads from the JSON file."""
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _read_archived(self):
        """Read all archived leads."""
        try:
            with open(ARCHIVED_LEADS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_archived(self, leads):
        """Write archived leads to file."""
        with open(ARCHIVED_LEADS_FILE, "w") as f:
            json.dump(leads, f, indent=2)

    def _write(self, leads):
        """Write leads to the JSON file."""
        with open(self.filepath, "w") as f:
            json.dump(leads, f, indent=2)

    def add_lead(self, name, email, phone="", company="", question="", source="chat"):
        """Add a new lead. Returns the lead dict with assigned ID.

        Args:
            source: How the lead was captured ("unanswered", "goodbye", "chat", "form")
        """
        leads = self._read()
        lead = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "phone": phone,
            "company": company,
            "question": question,
            "source": source,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending",  # pending | contacted | closed
            "email_sent": False,   # Has follow-up email been sent?
            "email_sent_at": "",   # When was the email sent?
            "notes": "",
        }
        leads.append(lead)
        self._write(leads)
        return lead

    def search_leads(self, query):
        """Search leads by name, email, question, or company."""
        if not query:
            return self.get_all_leads()
        query = query.lower()
        leads = self._read()
        results = [
            l for l in leads
            if query in l["name"].lower()
            or query in l["email"].lower()
            or query in l.get("question", "").lower()
            or query in l.get("company", "").lower()
        ]
        return list(reversed(results))

    def get_all_leads(self):
        """Return all leads, newest first."""
        leads = self._read()
        return list(reversed(leads))

    def get_pending_leads(self):
        """Return only pending (uncontacted) leads."""
        return [l for l in self.get_all_leads() if l["status"] == "pending"]

    def get_lead_count(self):
        """Return total and pending counts."""
        leads = self._read()
        total = len(leads)
        pending = sum(1 for l in leads if l["status"] == "pending")
        return total, pending

    def mark_contacted(self, lead_id):
        """Mark a lead as contacted."""
        leads = self._read()
        for lead in leads:
            if lead["id"] == lead_id:
                lead["status"] = "contacted"
                self._write(leads)
                return True
        return False

    def mark_closed(self, lead_id):
        """Mark a lead as closed."""
        leads = self._read()
        for lead in leads:
            if lead["id"] == lead_id:
                lead["status"] = "closed"
                self._write(leads)
                return True
        return False

    def add_note(self, lead_id, note):
        """Add a note to a lead."""
        leads = self._read()
        for lead in leads:
            if lead["id"] == lead_id:
                lead["notes"] = note
                self._write(leads)
                return True
        return False

    def mark_email_sent(self, lead_id):
        """Mark that a follow-up email was sent to this lead."""
        leads = self._read()
        for lead in leads:
            if lead["id"] == lead_id:
                lead["email_sent"] = True
                lead["email_sent_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self._write(leads)
                return True
        return False

    def get_email_stats(self):
        """Get email sending stats."""
        leads = self._read()
        total = len(leads)
        sent = sum(1 for l in leads if l.get("email_sent"))
        return total, sent

    def export_csv(self):
        """Export all leads as CSV text."""
        leads = self._read()
        output = io.StringIO()
        if leads:
            writer = csv.DictWriter(output, fieldnames=[
                "id", "name", "email", "phone", "company",
                "question", "source", "timestamp", "status",
                "email_sent", "email_sent_at", "notes"
            ])
            writer.writeheader()
            writer.writerows(leads)
        return output.getvalue()

    def archive_old_leads(self, retention_days=90):
        """Move leads older than retention_days to the archive file.

        Returns the number of leads archived.
        Set retention_days to 0 to disable archiving.
        """
        if retention_days <= 0:
            return 0

        leads = self._read()
        if not leads:
            return 0

        cutoff = datetime.now() - timedelta(days=retention_days)
        active = []
        to_archive = []

        for lead in leads:
            try:
                lead_time = datetime.strptime(lead["timestamp"], "%Y-%m-%d %H:%M:%S")
                if lead_time < cutoff:
                    lead["archived_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    to_archive.append(lead)
                else:
                    active.append(lead)
            except (ValueError, KeyError):
                # If timestamp can't be parsed, keep in active
                active.append(lead)

        if not to_archive:
            return 0

        # Append to archived file
        archived = self._read_archived()
        archived.extend(to_archive)
        self._write_archived(archived)

        # Rewrite active leads file
        self._write(active)

        return len(to_archive)

    def get_archived_leads(self):
        """Return all archived leads, most recently archived first."""
        leads = self._read_archived()
        return list(reversed(leads))

    def get_archived_lead_count(self):
        """Return the number of archived leads."""
        return len(self._read_archived())

    def export_archived_csv(self):
        """Export all archived leads as CSV text."""
        leads = self._read_archived()
        output = io.StringIO()
        if leads:
            fields = [
                "id", "name", "email", "phone", "company",
                "question", "source", "timestamp", "status",
                "email_sent", "email_sent_at", "notes", "archived_at"
            ]
            writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(leads)
        return output.getvalue()

    def delete_lead(self, lead_id):
        """Delete a lead by ID."""
        leads = self._read()
        leads = [l for l in leads if l["id"] != lead_id]
        self._write(leads)
        return True
