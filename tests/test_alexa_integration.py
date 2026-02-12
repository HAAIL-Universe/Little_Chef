"""Phase 13.2 — Alexa integration tests.

Verifies the Alexa webhook endpoint handles the minimal command set:
  - WhatCanIMakeIntent
  - CanICookIntent
  - AddToListIntent
  - WeCookedIntent
  - LaunchRequest / SessionEndedRequest / Help / Stop
"""

import pytest


ALEXA_URL = "/alexa/webhook"


def _alexa_intent(intent_name: str, slots: dict | None = None) -> dict:
    """Build a minimal Alexa IntentRequest body."""
    intent: dict = {"name": intent_name}
    if slots:
        intent["slots"] = {k: {"name": k, "value": v} for k, v in slots.items()}
    return {
        "version": "1.0",
        "request": {
            "type": "IntentRequest",
            "intent": intent,
        },
    }


def _alexa_launch() -> dict:
    return {"version": "1.0", "request": {"type": "LaunchRequest"}}


def _alexa_session_ended() -> dict:
    return {"version": "1.0", "request": {"type": "SessionEndedRequest"}}


# ---------------------------------------------------------------------------
# Launch / Session
# ---------------------------------------------------------------------------

class TestAlexaSession:
    def test_launch_request(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_launch())
        body = resp.json()
        assert resp.status_code == 200
        assert body["version"] == "1.0"
        assert "Welcome" in body["response"]["outputSpeech"]["text"]
        assert body["response"]["shouldEndSession"] is False

    def test_session_ended(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_session_ended())
        body = resp.json()
        assert resp.status_code == 200
        assert "Goodbye" in body["response"]["outputSpeech"]["text"]

    def test_help_intent(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("AMAZON.HelpIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert "say" in body["response"]["outputSpeech"]["text"].lower()
        assert body["response"]["shouldEndSession"] is False

    def test_stop_intent(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("AMAZON.StopIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert "Goodbye" in body["response"]["outputSpeech"]["text"]

    def test_cancel_intent(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("AMAZON.CancelIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert "Goodbye" in body["response"]["outputSpeech"]["text"]


# ---------------------------------------------------------------------------
# WhatCanIMakeIntent
# ---------------------------------------------------------------------------

class TestAlexaMatch:
    def test_what_can_i_make(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("WhatCanIMakeIntent"))
        body = resp.json()
        assert resp.status_code == 200
        speech = body["response"]["outputSpeech"]["text"]
        assert len(speech) > 10  # Non-trivial response
        assert body["response"]["card"]["title"] == "What Can I Make?"


# ---------------------------------------------------------------------------
# CanICookIntent
# ---------------------------------------------------------------------------

class TestAlexaCheck:
    def test_can_i_cook_with_recipe(self, authed_client):
        resp = authed_client.post(
            ALEXA_URL, json=_alexa_intent("CanICookIntent", {"RecipeName": "tomato pasta"})
        )
        body = resp.json()
        assert resp.status_code == 200
        speech = body["response"]["outputSpeech"]["text"]
        assert len(speech) > 5

    def test_can_i_cook_no_recipe(self, authed_client):
        """Missing RecipeName slot prompts user."""
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("CanICookIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert "tell me" in body["response"]["outputSpeech"]["text"].lower()
        assert body["response"]["shouldEndSession"] is False


# ---------------------------------------------------------------------------
# AddToListIntent
# ---------------------------------------------------------------------------

class TestAlexaAddToList:
    def test_add_item_to_list(self, authed_client):
        resp = authed_client.post(
            ALEXA_URL, json=_alexa_intent("AddToListIntent", {"ItemName": "milk"})
        )
        body = resp.json()
        assert resp.status_code == 200
        assert "milk" in body["response"]["outputSpeech"]["text"].lower()
        assert "staple" in body["response"]["outputSpeech"]["text"].lower()

    def test_add_item_no_name(self, authed_client):
        """Missing ItemName slot prompts user."""
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("AddToListIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert body["response"]["shouldEndSession"] is False

    def test_add_item_persists_as_staple(self, authed_client):
        """Item added via Alexa appears in staples list."""
        authed_client.post(
            ALEXA_URL, json=_alexa_intent("AddToListIntent", {"ItemName": "butter"})
        )
        # Verify via the REST API
        resp = authed_client.get("/inventory/staples")
        body = resp.json()
        staple_names = [s["item_name"] for s in body["staples"]]
        assert "butter" in staple_names


# ---------------------------------------------------------------------------
# WeCookedIntent
# ---------------------------------------------------------------------------

class TestAlexaCooked:
    def test_we_cooked(self, authed_client):
        resp = authed_client.post(
            ALEXA_URL, json=_alexa_intent("WeCookedIntent", {"RecipeName": "tomato pasta"})
        )
        body = resp.json()
        assert resp.status_code == 200
        speech = body["response"]["outputSpeech"]["text"]
        assert "recorded" in speech.lower() or "cooked" in speech.lower()

    def test_we_cooked_no_recipe(self, authed_client):
        """Missing RecipeName prompts user."""
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("WeCookedIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert body["response"]["shouldEndSession"] is False

    def test_we_cooked_unknown_recipe(self, authed_client):
        """Unknown recipe returns helpful message."""
        resp = authed_client.post(
            ALEXA_URL, json=_alexa_intent("WeCookedIntent", {"RecipeName": "quantum soup"})
        )
        body = resp.json()
        assert resp.status_code == 200
        # Should get a "couldn't find" type response
        speech = body["response"]["outputSpeech"]["text"]
        assert len(speech) > 5


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestAlexaEdge:
    def test_unknown_intent(self, authed_client):
        resp = authed_client.post(ALEXA_URL, json=_alexa_intent("SomeRandomIntent"))
        body = resp.json()
        assert resp.status_code == 200
        assert "not sure" in body["response"]["outputSpeech"]["text"].lower()

    def test_unknown_request_type(self, authed_client):
        resp = authed_client.post(
            ALEXA_URL, json={"version": "1.0", "request": {"type": "UnknownType"}}
        )
        body = resp.json()
        assert resp.status_code == 200

    def test_alexa_endpoint_in_openapi(self, authed_client):
        resp = authed_client.get("/openapi.json")
        schema = resp.json()
        paths = list(schema["paths"].keys())
        assert "/alexa/webhook" in paths

    def test_response_has_card(self, authed_client):
        """All Alexa responses include a Simple card."""
        resp = authed_client.post(ALEXA_URL, json=_alexa_launch())
        body = resp.json()
        assert body["response"]["card"]["type"] == "Simple"
        assert body["response"]["card"]["title"]
        assert body["response"]["card"]["content"]
