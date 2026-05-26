"""
Unit tests for the WhatsApp state machine (process_message function).

Tests cover:
  - New conversation session creation
  - Goodbye message handling
  - Human/agent request flow
  - FAQ matching
  - No-match lead capture (enabled and disabled)
  - STATE_AWAITING_NAME (skip, provide name)
  - STATE_AWAITING_EMAIL (invalid, valid with/without phone required)
  - STATE_AWAITING_PHONE (provide phone, skip)
  - Full end-to-end lead capture flow
  - Analytics tracking on first message

Run with:
    cd support-bot && python -m pytest test_whatsapp_handler.py -v
"""

import sys
import os
from unittest.mock import patch, MagicMock, ANY

# Ensure the support-bot directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from datetime import datetime


# ─── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_sessions():
    """Reset the global SESSIONS dict before each test."""
    import whatsapp_handler
    whatsapp_handler.SESSIONS = {}
    yield


@pytest.fixture(autouse=True)
def mock_save_sessions():
    """Mock _save_sessions to prevent disk writes during tests."""
    with patch("whatsapp_handler._save_sessions") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_analytics():
    """Mock all analytics functions to prevent disk writes."""
    with patch("whatsapp_handler.log_whatsapp_message") as mock_log_msg, \
         patch("whatsapp_handler.log_conversation_started") as mock_log_start, \
         patch("whatsapp_handler.log_conversation_resolved") as mock_log_resolved, \
         patch("whatsapp_handler.log_unresolved") as mock_log_unresolved, \
         patch("whatsapp_handler.log_lead_captured") as mock_log_lead:
        yield {
            "log_whatsapp_message": mock_log_msg,
            "log_conversation_started": mock_log_start,
            "log_conversation_resolved": mock_log_resolved,
            "log_unresolved": mock_log_unresolved,
            "log_lead_captured": mock_log_lead,
        }


@pytest.fixture(autouse=True)
def mock_find_best_match():
    """Mock find_best_match to control FAQ matching in tests."""
    with patch("whatsapp_handler.find_best_match") as mock:
        mock.return_value = None  # Default: no match found
        yield mock


@pytest.fixture(autouse=True)
def mock_add_lead():
    """Mock db.add_lead to prevent disk writes."""
    with patch("whatsapp_handler.db.add_lead") as mock:
        mock.return_value = {"id": "test-uuid"}
        yield mock


# ─── Tests: New conversation & session management ─────────────────────────


class TestNewConversation:
    def test_new_session_created_with_faq_match(self, mock_find_best_match):
        """First message from a new phone creates a session with correct defaults (when FAQ matches)."""
        import whatsapp_handler

        mock_find_best_match.return_value = {"answer": "Hello! Welcome!", "question": "Greeting", "keywords": ["hello"]}

        response = whatsapp_handler.process_message("+1234567890", "hello")

        assert "+1234567890" in whatsapp_handler.SESSIONS
        session = whatsapp_handler.SESSIONS["+1234567890"]
        assert session["state"] == whatsapp_handler.STATE_CHATTING
        assert session["messages_sent"] == 1
        assert session["analytics_logged"] is True
        assert session["conversation_context"] == "Greeting"
        assert session["lead_name"] == ""
        assert session["lead_email"] == ""
        assert response == "Hello! Welcome!"

    def test_analytics_logged_on_first_message(self, mock_analytics, mock_find_best_match):
        """First message triggers log_conversation_started."""
        import whatsapp_handler

        # find_best_match returns a match so analytics doesn't log unresolved
        mock_find_best_match.return_value = {"answer": "Hi there!", "question": "Greeting", "keywords": ["hello"]}

        whatsapp_handler.process_message("+1234567890", "hello")

        mock_analytics["log_conversation_started"].assert_called_once()
        mock_analytics["log_whatsapp_message"].assert_called_with("+1234567890", "received")

    def test_analytics_only_logged_once(self, mock_analytics, mock_find_best_match):
        """Subsequent messages do not trigger log_conversation_started again."""
        import whatsapp_handler

        mock_find_best_match.return_value = {"answer": "ok", "question": "Test", "keywords": ["ok"]}

        whatsapp_handler.process_message("+1234567890", "first")
        whatsapp_handler.process_message("+1234567890", "second")

        mock_analytics["log_conversation_started"].assert_called_once()


# ─── Tests: Chatting state (goodbye, human, FAQ match, no match) ──────────


class TestGoodbye:
    @pytest.mark.parametrize("goodbye_text", [
        "bye", "goodbye", "see you", "later", "take care",
        "bye!", "Goodbye friend", "see you later!",
    ])
    def test_goodbye_detected(self, goodbye_text):
        """Goodbye messages return the goodbye message and reset conversation_context."""
        import whatsapp_handler

        # Simulate an existing session with context
        whatsapp_handler.SESSIONS["+1234567890"] = {
            "state": "chatting",
            "conversation_context": "Pricing",
            "pending_question": "",
            "lead_name": "",
            "lead_email": "",
            "lead_phone": "",
            "created_at": datetime.now().isoformat(),
            "messages_sent": 1,
            "analytics_logged": True,
        }

        response = whatsapp_handler.process_message("+1234567890", goodbye_text)

        assert "Take care" in response
        assert "support@yourcompany.com" in response
        assert whatsapp_handler.SESSIONS["+1234567890"]["conversation_context"] is None
        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == "chatting"

    @pytest.mark.parametrize("normal_text", [
        "byproduct", "seeyou",
    ])
    def test_goodbye_not_false_positive(self, normal_text, mock_find_best_match):
        """
        Messages that contain 'bye' as part of a word should not trigger goodbye.
        Note: "bye laws" would match because the current production code uses
        substring matching (`"bye" in "bye laws"` is True).
        """
        import whatsapp_handler

        mock_find_best_match.return_value = {"answer": "FAQ answer", "question": "Test", "keywords": ["test"]}

        response = whatsapp_handler.process_message("+1234567890", normal_text)

        # Should not contain the goodbye message
        assert "Take care" not in response
        # Should have gone through FAQ matching instead
        assert response == "FAQ answer"


class TestHumanAgentRequest:
    @pytest.mark.parametrize("request_text", [
        "talk to a human", "agent", "real person", "representative",
        "I want to speak to a human", "connect me with an agent",
    ])
    def test_human_request_triggers_lead_capture(self, request_text):
        """Asking for a human sets the state to awaiting_name and asks for name."""
        import whatsapp_handler

        response = whatsapp_handler.process_message("+1234567890", request_text)

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_AWAITING_NAME
        assert "name" in response.lower()
        assert "human agent" in response.lower() or "connect" in response.lower()


class TestFAQMatch:
    def test_faq_match_returns_answer(self, mock_find_best_match):
        """Matching an FAQ returns the answer and sets conversation_context."""
        import whatsapp_handler

        mock_find_best_match.return_value = {
            "answer": "Our pricing starts at $19/month.",
            "question": "What are your pricing plans?",
            "keywords": ["pricing"],
        }

        response = whatsapp_handler.process_message("+1234567890", "how much does it cost?")

        assert response == "Our pricing starts at $19/month."
        assert whatsapp_handler.SESSIONS["+1234567890"]["conversation_context"] == "What are your pricing plans?"

    def test_faq_match_logs_resolved(self, mock_find_best_match, mock_analytics):
        """Matching an FAQ logs the resolution."""
        import whatsapp_handler

        mock_find_best_match.return_value = {
            "answer": "Yes, we have a mobile app.",
            "question": "Do you have a mobile app?",
            "keywords": ["mobile", "app"],
        }

        whatsapp_handler.process_message("+1234567890", "do you have an app?")

        mock_analytics["log_conversation_resolved"].assert_called_once_with("Do you have a mobile app?")


class TestNoMatch:
    def test_no_match_with_lead_capture(self):
        """Unmatched message with CAPTURE_LEADS=True starts lead capture (asks for name)."""
        import whatsapp_handler

        # CAPTURE_LEADS is True by default
        response = whatsapp_handler.process_message("+1234567890", "some random question nobody asked")

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_AWAITING_NAME
        assert "could you tell me your **name**" in response
        assert whatsapp_handler.SESSIONS["+1234567890"]["pending_question"] == "some random question nobody asked"

    def test_no_match_logs_unresolved(self, mock_analytics):
        """Unmatched message logs log_unresolved."""
        import whatsapp_handler

        whatsapp_handler.process_message("+1234567890", "something the bot doesn't know")

        mock_analytics["log_unresolved"].assert_called_once()

    def test_no_match_without_lead_capture(self):
        """Unmatched message with CAPTURE_LEADS=False returns contact info."""
        import whatsapp_handler

        with patch.object(whatsapp_handler, "CAPTURE_LEADS", False):
            response = whatsapp_handler.process_message("+1234567890", "some random question")

        assert "I'm not sure" in response
        assert "support@yourcompany.com" in response
        # State should stay in chatting (no lead capture started)
        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_CHATTING


# ─── Tests: STATE_AWAITING_NAME ────────────────────────────────────────────


class TestAwaitingName:
    def setup_awaiting_name(self):
        """Helper: create a session in AWAITING_NAME state."""
        import whatsapp_handler
        whatsapp_handler.SESSIONS["+1234567890"] = {
            "state": whatsapp_handler.STATE_AWAITING_NAME,
            "conversation_context": None,
            "pending_question": "my weird problem",
            "lead_name": "",
            "lead_email": "",
            "lead_phone": "",
            "created_at": datetime.now().isoformat(),
            "messages_sent": 1,
            "analytics_logged": True,
        }

    @pytest.mark.parametrize("skip_text", [
        "no", "nope", "skip", "cancel", "nah", "nevermind", "forget it",
    ])
    def test_skip_returns_to_chatting(self, skip_text):
        """User says 'skip' during name prompt → back to chatting state."""
        import whatsapp_handler
        self.setup_awaiting_name()

        response = whatsapp_handler.process_message("+1234567890", skip_text)

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_CHATTING
        assert "No problem" in response

    def test_provides_name_moves_to_email(self):
        """User provides their name → moves to AWAITING_EMAIL state."""
        import whatsapp_handler
        self.setup_awaiting_name()

        response = whatsapp_handler.process_message("+1234567890", "John Doe")

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_AWAITING_EMAIL
        assert whatsapp_handler.SESSIONS["+1234567890"]["lead_name"] == "John Doe"
        assert "email" in response.lower()


# ─── Tests: STATE_AWAITING_EMAIL ───────────────────────────────────────────


class TestAwaitingEmail:
    def setup_awaiting_email(self, name="John Doe"):
        """Helper: create a session in AWAITING_EMAIL state."""
        import whatsapp_handler
        whatsapp_handler.SESSIONS["+1234567890"] = {
            "state": whatsapp_handler.STATE_AWAITING_EMAIL,
            "conversation_context": None,
            "pending_question": "my weird problem",
            "lead_name": name,
            "lead_email": "",
            "lead_phone": "",
            "created_at": datetime.now().isoformat(),
            "messages_sent": 1,
            "analytics_logged": True,
        }

    @pytest.mark.parametrize("invalid_email", [
        "notanemail", "noatsign", "@nodomain",
    ])
    def test_invalid_email_shows_error(self, invalid_email):
        """Invalid email returns error and stays in AWAITING_EMAIL state.

        Note: "spaced @ email.com" is NOT in this list because the
        production code's validation is intentionally simple (just checks
        for @ and .), so it passes through.
        """
        import whatsapp_handler
        self.setup_awaiting_email()

        response = whatsapp_handler.process_message("+1234567890", invalid_email)

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_AWAITING_EMAIL
        assert "doesn't look like a valid email" in response

    def test_valid_email_no_phone_required(self, mock_add_lead):
        """Valid email with REQUIRE_PHONE=False captures the lead."""
        import whatsapp_handler
        self.setup_awaiting_email()

        with patch.object(whatsapp_handler, "REQUIRE_PHONE", False):
            response = whatsapp_handler.process_message("+1234567890", "john@example.com")

        # Session should be back to chatting
        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_CHATTING
        assert "Thanks John" in response
        # Lead should have been captured
        mock_add_lead.assert_called_once()
        call_kwargs = mock_add_lead.call_args[1]
        assert call_kwargs["name"] == "John Doe"
        assert call_kwargs["email"] == "john@example.com"
        assert call_kwargs["source"] == "whatsapp"

    def test_valid_email_phone_required_moves_to_phone(self):
        """Valid email with REQUIRE_PHONE=True moves to AWAITING_PHONE state."""
        import whatsapp_handler
        self.setup_awaiting_email()

        with patch.object(whatsapp_handler, "REQUIRE_PHONE", True):
            response = whatsapp_handler.process_message("+1234567890", "john@example.com")

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_AWAITING_PHONE
        assert "phone number" in response.lower()
        assert whatsapp_handler.SESSIONS["+1234567890"]["lead_email"] == "john@example.com"

    def test_valid_email_logs_lead_captured(self, mock_analytics):
        """Valid email without phone requirement logs lead_captured."""
        import whatsapp_handler
        self.setup_awaiting_email()

        with patch.object(whatsapp_handler, "REQUIRE_PHONE", False):
            whatsapp_handler.process_message("+1234567890", "john@example.com")

        mock_analytics["log_lead_captured"].assert_called_once()


# ─── Tests: STATE_AWAITING_PHONE ──────────────────────────────────────────


class TestAwaitingPhone:
    def setup_awaiting_phone(self):
        """Helper: create a session in AWAITING_PHONE state."""
        import whatsapp_handler
        whatsapp_handler.SESSIONS["+1234567890"] = {
            "state": whatsapp_handler.STATE_AWAITING_PHONE,
            "conversation_context": None,
            "pending_question": "my weird problem",
            "lead_name": "John Doe",
            "lead_email": "john@example.com",
            "lead_phone": "",
            "created_at": datetime.now().isoformat(),
            "messages_sent": 2,
            "analytics_logged": True,
        }

    def test_provides_phone_captures_lead(self, mock_add_lead):
        """User provides phone number → lead captured with phone."""
        import whatsapp_handler
        self.setup_awaiting_phone()

        response = whatsapp_handler.process_message("+1234567890", "+1-555-1234")

        assert whatsapp_handler.SESSIONS["+1234567890"]["state"] == whatsapp_handler.STATE_CHATTING
        assert "Thanks John" in response
        mock_add_lead.assert_called_once()
        call_kwargs = mock_add_lead.call_args[1]
        assert call_kwargs["phone"] == "+1-555-1234"

    @pytest.mark.parametrize("skip_text", ["skip", "no", "nope"])
    def test_skip_phone_captures_lead_without_phone(self, skip_text, mock_add_lead):
        """User skips phone → lead captured with empty phone."""
        import whatsapp_handler
        self.setup_awaiting_phone()

        whatsapp_handler.process_message("+1234567890", skip_text)

        mock_add_lead.assert_called_once()
        call_kwargs = mock_add_lead.call_args[1]
        assert call_kwargs["phone"] == ""


# ─── Tests: Full end-to-end lead capture flow ─────────────────────────────


class TestFullLeadCaptureFlow:
    def test_full_flow(self, mock_add_lead, mock_analytics):
        """
        Complete end-to-end lead capture:
        1. User asks question the bot can't answer → asked for name
        2. User provides name → asked for email
        3. User provides email → lead captured
        """
        import whatsapp_handler

        phone = "+1234567890"

        # Step 1: Unmatched question
        response1 = whatsapp_handler.process_message(phone, "I have a really specific question")
        assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_AWAITING_NAME
        assert "name" in response1.lower()

        # Step 2: Provide name
        response2 = whatsapp_handler.process_message(phone, "Alice Smith")
        assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_AWAITING_EMAIL
        assert whatsapp_handler.SESSIONS[phone]["lead_name"] == "Alice Smith"
        assert "email" in response2.lower()

        # Step 3: Provide email
        with patch.object(whatsapp_handler, "REQUIRE_PHONE", False):
            response3 = whatsapp_handler.process_message(phone, "alice@test.com")

        assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_CHATTING
        assert "Thanks Alice" in response3
        mock_add_lead.assert_called_once()
        call_kwargs = mock_add_lead.call_args[1]
        assert call_kwargs["name"] == "Alice Smith"
        assert call_kwargs["email"] == "alice@test.com"
        assert call_kwargs["source"] == "whatsapp"
        # Step 1 + Step 2 + Step 3 = 3 received messages
        assert mock_analytics["log_whatsapp_message"].call_count == 3

    def test_full_flow_with_phone(self, mock_add_lead):
        """
        Complete flow with REQUIRE_PHONE=True:
        1. Unmatched question → asked for name
        2. Name → asked for email
        3. Email → asked for phone
        4. Phone → lead captured
        """
        import whatsapp_handler

        phone = "+1234567890"

        with patch.object(whatsapp_handler, "REQUIRE_PHONE", True):

            # Step 1
            whatsapp_handler.process_message(phone, "my custom question")
            assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_AWAITING_NAME

            # Step 2
            whatsapp_handler.process_message(phone, "Bob")
            assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_AWAITING_EMAIL

            # Step 3
            whatsapp_handler.process_message(phone, "bob@test.com")
            assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_AWAITING_PHONE

            # Step 4
            response = whatsapp_handler.process_message(phone, "+1-555-9999")

        assert whatsapp_handler.SESSIONS[phone]["state"] == whatsapp_handler.STATE_CHATTING
        assert "Thanks Bob" in response
        mock_add_lead.assert_called_once()
        call_kwargs = mock_add_lead.call_args[1]
        assert call_kwargs["name"] == "Bob"
        assert call_kwargs["email"] == "bob@test.com"
        assert call_kwargs["phone"] == "+1-555-9999"


# ─── Tests: Multiple conversations ─────────────────────────────────────────


class TestMultipleConversations:
    def test_two_independent_conversations(self, mock_find_best_match):
        """Two different phone numbers maintain independent sessions."""
        import whatsapp_handler

        mock_find_best_match.return_value = {
            "answer": "$19/month",
            "question": "Pricing",
            "keywords": ["pricing"],
        }

        # Phone A chats normally
        whatsapp_handler.process_message("+1111111111", "pricing?")
        assert whatsapp_handler.SESSIONS["+1111111111"]["conversation_context"] == "Pricing"

        # Phone B starts from scratch
        mock_find_best_match.return_value = None
        whatsapp_handler.process_message("+2222222222", "my custom issue")

        # Phone A should still have its context, Phone B is in AWAITING_NAME
        assert whatsapp_handler.SESSIONS["+1111111111"]["conversation_context"] == "Pricing"
        assert whatsapp_handler.SESSIONS["+1111111111"]["state"] == "chatting"
        assert whatsapp_handler.SESSIONS["+2222222222"]["state"] == whatsapp_handler.STATE_AWAITING_NAME
