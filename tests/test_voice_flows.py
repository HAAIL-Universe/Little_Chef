"""Phase 13.1 — Voice flow stabilization tests.

Verifies that speech-to-text (dictation) transcripts correctly trigger
MATCH, CHECK, PLAN, and CONSUME flows, producing valid responses with
voice_hint when voice_input=True.
"""

import pytest


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _ask(client, message: str, *, voice: bool = False, thread_id: str | None = None):
    """Send an ask-mode chat message."""
    payload = {"mode": "ask", "message": message, "voice_input": voice}
    if thread_id:
        payload["thread_id"] = thread_id
    return client.post("/chat", json=payload)


def _plan(client, message: str, thread_id: str, *, voice: bool = False):
    """Send a plan (fill-mode) message to /chat/mealplan."""
    return client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": message, "thread_id": thread_id, "voice_input": voice},
    )


# ---------------------------------------------------------------------------
# 13.1 — STT normalization unit tests
# ---------------------------------------------------------------------------

class TestSttNormalization:
    """Test the normalize_stt utility in isolation."""

    def test_fillers_removed(self):
        from app.services.stt_normalize import normalize_stt
        assert "um" not in normalize_stt("um what can I make uh today")
        assert normalize_stt("um what can I make uh today").strip() == "what can I make today"

    def test_contractions_restored(self):
        from app.services.stt_normalize import normalize_stt
        assert "what's" in normalize_stt("whats possible")
        assert "can't" in normalize_stt("I cant cook that")
        assert "I've" in normalize_stt("Ive got tomatoes")

    def test_multi_spaces_collapsed(self):
        from app.services.stt_normalize import normalize_stt
        assert "  " not in normalize_stt("what   can   I   make")

    def test_voice_hint_truncation(self):
        from app.services.stt_normalize import voice_hint_for
        long_text = "First sentence. Second sentence with much more detail about recipes and ingredients."
        hint = voice_hint_for(long_text)
        assert hint == "First sentence."

    def test_voice_hint_short_text(self):
        from app.services.stt_normalize import voice_hint_for
        short = "You can make pasta."
        assert voice_hint_for(short) == short


# ---------------------------------------------------------------------------
# 13.1 — MATCH via voice
# ---------------------------------------------------------------------------

class TestVoiceMatch:
    """Dictation-style 'what can I make' queries."""

    def test_voice_match_basic(self, authed_client):
        """'what can i make' via voice produces ranked suggestions."""
        resp = _ask(authed_client, "what can i make", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert "voice_hint" in body
        assert body["voice_hint"] is not None
        assert body["confirmation_required"] is False

    def test_voice_match_with_fillers(self, authed_client):
        """Fillers (um, uh) don't prevent MATCH detection."""
        resp = _ask(authed_client, "um what um can i make", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        # Should match MATCH pattern after filler removal
        assert body["confirmation_required"] is False
        assert body["voice_hint"] is not None

    def test_voice_match_dropped_apostrophe(self, authed_client):
        """'whats possible' (no apostrophe) triggers MATCH."""
        resp = _ask(authed_client, "whats possible for dinner", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["voice_hint"] is not None

    def test_voice_match_suggest_meals(self, authed_client):
        """'suggest some meals' triggers MATCH."""
        resp = _ask(authed_client, "suggest some meals please", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is False


# ---------------------------------------------------------------------------
# 13.1 — CHECK via voice
# ---------------------------------------------------------------------------

class TestVoiceCheck:
    """Dictation-style 'can I cook X?' queries."""

    def test_voice_check_basic(self, authed_client):
        """'can i cook tomato pasta' via voice returns feasibility."""
        resp = _ask(authed_client, "can i cook tomato pasta", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is False
        assert body["voice_hint"] is not None

    def test_voice_check_with_fillers(self, authed_client):
        """'um can i make uh garlic butter chicken' routes correctly."""
        resp = _ask(authed_client, "um can i make uh garlic butter chicken", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is False

    def test_voice_check_dropped_contraction(self, authed_client):
        """'do i have enough for veggie stir fry' works with STT."""
        resp = _ask(authed_client, "do i have enough for veggie stir fry", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["voice_hint"] is not None


# ---------------------------------------------------------------------------
# 13.1 — PLAN via voice (/chat/mealplan)
# ---------------------------------------------------------------------------

class TestVoicePlan:
    """Dictation-style meal plan requests."""

    def test_voice_plan_basic(self, authed_client):
        """'plan my meals for 3 days' via voice creates a proposal."""
        resp = _plan(authed_client, "plan my meals for 3 days", "t-voice-plan-1", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True
        assert body["voice_hint"] is not None
        assert "3-day" in body["reply_text"]

    def test_voice_plan_with_fillers(self, authed_client):
        """'um plan uh 2 days of meals' parses correctly after normalization."""
        resp = _plan(authed_client, "um plan uh 2 days of meals", "t-voice-plan-2", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True
        assert "2-day" in body["reply_text"]

    def test_voice_plan_no_voice_flag(self, authed_client):
        """Plan without voice_input flag works normally (no voice_hint)."""
        resp = _plan(authed_client, "plan 1 day of meals", "t-voice-plan-3", voice=False)
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True
        assert body.get("voice_hint") is None


# ---------------------------------------------------------------------------
# 13.1 — CONSUME via voice
# ---------------------------------------------------------------------------

class TestVoiceConsume:
    """Dictation-style 'I cooked X' consumption confirmations."""

    def test_voice_consume_basic(self, authed_client):
        """'i cooked simple tomato pasta' via voice creates consume proposal."""
        resp = _ask(authed_client, "i cooked simple tomato pasta", voice=True, thread_id="t-voice-consume-1")
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True
        assert body["voice_hint"] is not None

    def test_voice_consume_we_made(self, authed_client):
        """'we made garlic butter chicken' via voice."""
        resp = _ask(authed_client, "we made garlic butter chicken", voice=True, thread_id="t-voice-consume-2")
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True

    def test_voice_consume_with_fillers(self, authed_client):
        """'um i cooked uh the tomato pasta tonight' works after normalization."""
        resp = _ask(
            authed_client,
            "um i cooked uh the tomato pasta tonight",
            voice=True,
            thread_id="t-voice-consume-3",
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True

    def test_voice_consume_prepared(self, authed_client):
        """'i prepared veggie stir fry yesterday' via voice."""
        resp = _ask(
            authed_client,
            "i prepared veggie stir fry yesterday",
            voice=True,
            thread_id="t-voice-consume-4",
        )
        body = resp.json()
        assert resp.status_code == 200
        assert body["confirmation_required"] is True


# ---------------------------------------------------------------------------
# 13.1 — Cross-cutting voice concerns
# ---------------------------------------------------------------------------

class TestVoiceCrossCutting:
    """Edge cases and cross-cutting voice behavior."""

    def test_voice_input_flag_defaults_false(self, authed_client):
        """ChatRequest without voice_input defaults to False."""
        resp = authed_client.post("/chat", json={"mode": "ask", "message": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        # No voice_hint when voice_input not set
        assert body.get("voice_hint") is None

    def test_voice_flag_in_openapi_schema(self, authed_client):
        """voice_input field appears in the ChatRequest schema."""
        resp = authed_client.get("/openapi.json")
        schema = resp.json()
        chat_req = schema["components"]["schemas"]["ChatRequest"]
        assert "voice_input" in chat_req["properties"]

    def test_voice_hint_in_response_schema(self, authed_client):
        """voice_hint field appears in the ChatResponse schema."""
        resp = authed_client.get("/openapi.json")
        schema = resp.json()
        chat_resp = schema["components"]["schemas"]["ChatResponse"]
        assert "voice_hint" in chat_resp["properties"]

    def test_voice_low_stock_query(self, authed_client):
        """'what am i low on' with voice gets voice_hint."""
        resp = _ask(authed_client, "what am i low on", voice=True)
        body = resp.json()
        # 'low on' keyword triggers low-stock check
        assert resp.status_code == 200
        # Lowered message contains "low on" → triggers low stock path
        assert "low" in body["reply_text"].lower() or "not low" in body["reply_text"].lower()

    def test_voice_inventory_query(self, authed_client):
        """'whats in my inventory' with voice works."""
        resp = _ask(authed_client, "whats in my inventory", voice=True)
        body = resp.json()
        assert resp.status_code == 200
        assert body["voice_hint"] is not None
