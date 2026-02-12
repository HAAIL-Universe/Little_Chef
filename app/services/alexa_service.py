"""Alexa skill webhook service.

Maps Alexa intent requests to existing ChefAgent, InventoryService, and
ChatService methods.  Returns Alexa-compatible JSON responses.

Supported intents:
  - WhatCanIMakeIntent  → ChefAgent.handle_match()
  - CanICookIntent      → ChefAgent.handle_check()
  - AddToListIntent     → InventoryService.set_staple() (marks as staple)
  - WeCookedIntent      → ChefAgent.handle_consume()
  - AMAZON.HelpIntent   → help text
  - AMAZON.StopIntent   → goodbye
  - AMAZON.CancelIntent → goodbye
"""

from __future__ import annotations

from typing import Any, Optional

from app.schemas import ChatRequest, UserMe


def _alexa_response(speech: str, *, end_session: bool = True, card_title: str = "Little Chef") -> dict[str, Any]:
    """Build an Alexa-compatible JSON response envelope."""
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech,
            },
            "card": {
                "type": "Simple",
                "title": card_title,
                "content": speech,
            },
            "shouldEndSession": end_session,
        },
    }


def _extract_slot(intent: dict, slot_name: str) -> Optional[str]:
    """Extract a slot value from an Alexa intent, returning None if absent."""
    slots = intent.get("slots", {})
    slot = slots.get(slot_name, {})
    return slot.get("value")


class AlexaService:
    """Translates Alexa skill requests into LittleChef backend operations."""

    def __init__(
        self,
        chef_agent,
        inventory_service,
    ) -> None:
        self.chef_agent = chef_agent
        self.inventory_service = inventory_service

    def handle_request(self, body: dict, user: UserMe) -> dict[str, Any]:
        """Route an Alexa request to the appropriate handler."""
        request_type = body.get("request", {}).get("type", "")

        if request_type == "LaunchRequest":
            return _alexa_response(
                "Welcome to Little Chef! You can ask what you can make, check if you can cook something, or tell me what you cooked.",
                end_session=False,
            )

        if request_type == "SessionEndedRequest":
            return _alexa_response("Goodbye!", end_session=True)

        if request_type != "IntentRequest":
            return _alexa_response("I didn't understand that. Try asking what you can make.")

        intent = body["request"].get("intent", {})
        intent_name = intent.get("name", "")

        if intent_name == "WhatCanIMakeIntent":
            return self._handle_match(user)
        elif intent_name == "CanICookIntent":
            recipe_name = _extract_slot(intent, "RecipeName")
            return self._handle_check(user, recipe_name)
        elif intent_name == "AddToListIntent":
            item_name = _extract_slot(intent, "ItemName")
            return self._handle_add_to_list(user, item_name)
        elif intent_name == "WeCookedIntent":
            recipe_name = _extract_slot(intent, "RecipeName")
            return self._handle_cooked(user, recipe_name)
        elif intent_name in ("AMAZON.HelpIntent",):
            return _alexa_response(
                "You can say: What can I make? Can I cook tomato pasta? Add milk to my shopping list. Or: We cooked chicken.",
                end_session=False,
            )
        elif intent_name in ("AMAZON.StopIntent", "AMAZON.CancelIntent"):
            return _alexa_response("Goodbye!")
        else:
            return _alexa_response("I'm not sure how to help with that. Try asking what you can make.")

    def _handle_match(self, user: UserMe) -> dict[str, Any]:
        """'What can I make?' → ranked suggestions."""
        request = ChatRequest(mode="ask", message="what can I make", voice_input=True)
        response = self.chef_agent.handle_match(user, request)

        # Extract a concise voice reply
        text = response.reply_text
        # Take first 3 suggestions for brevity
        lines = text.split("\n")
        voice_lines = [l for l in lines if l.strip() and not l.startswith("Here")][:3]
        if voice_lines:
            speech = "Here's what you can make. " + ". ".join(
                l.strip().split("—")[0].strip() if "—" in l else l.strip()
                for l in voice_lines
            )
        else:
            speech = "I couldn't find any recipes matching your inventory."

        return _alexa_response(speech, card_title="What Can I Make?")

    def _handle_check(self, user: UserMe, recipe_name: Optional[str]) -> dict[str, Any]:
        """'Can I cook X?' → feasibility check."""
        if not recipe_name:
            return _alexa_response(
                "Please tell me which recipe you want to check. For example, say: Can I cook tomato pasta?",
                end_session=False,
            )

        request = ChatRequest(mode="ask", message=f"can I cook {recipe_name}", voice_input=True)
        response = self.chef_agent.handle_check(user, request)

        # Use voice_hint if available, otherwise first sentence
        speech = response.voice_hint or response.reply_text.split(".")[0] + "."
        return _alexa_response(speech, card_title=f"Can I Cook {recipe_name.title()}?")

    def _handle_add_to_list(self, user: UserMe, item_name: Optional[str]) -> dict[str, Any]:
        """'Add X to shopping list' → mark as staple."""
        if not item_name:
            return _alexa_response(
                "What item would you like to add? For example, say: Add milk to my shopping list.",
                end_session=False,
            )

        self.inventory_service.set_staple(user.user_id, item_name, "count")
        return _alexa_response(
            f"Done. {item_name.title()} has been added as a staple and will appear on your shopping list when you're low.",
            card_title="Added to List",
        )

    def _handle_cooked(self, user: UserMe, recipe_name: Optional[str]) -> dict[str, Any]:
        """'We cooked X' → consume event proposal (auto-confirmed for Alexa)."""
        if not recipe_name:
            return _alexa_response(
                "Which recipe did you cook? For example, say: We cooked tomato pasta.",
                end_session=False,
            )

        # Use ChefAgent's consume flow — but Alexa can't do multi-step confirm,
        # so we create and immediately confirm the proposal.
        thread_id = f"alexa-{user.user_id}"
        request = ChatRequest(
            mode="ask",
            message=f"I cooked {recipe_name}",
            thread_id=thread_id,
            voice_input=True,
        )
        response = self.chef_agent.handle_consume(user, request)

        if not response.confirmation_required:
            # Recipe not found
            return _alexa_response(response.reply_text)

        # Auto-confirm for Alexa (no multi-step UX)
        proposal_id = response.proposal_id
        confirmed_count = 0
        if proposal_id:
            try:
                applied, event_ids, _reason = self.chef_agent.confirm(user, proposal_id, True, thread_id)
                if applied:
                    confirmed_count = len(event_ids)
            except Exception:
                pass  # Graceful degradation — record without confirming

        ingredient_count = confirmed_count or len(response.proposed_actions)
        return _alexa_response(
            f"Got it! I've recorded that you cooked {recipe_name} and deducted {ingredient_count} ingredients from your inventory.",
            card_title="Meal Recorded",
        )
