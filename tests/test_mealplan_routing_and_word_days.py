"""Regression tests for mealplan routing and word-number day parsing.

Bug: "generate a three-day plan" in the Meal Plan flow returned fallback
"I can help set preferences or inventory..." because:
1. Frontend sent mealplan flow to /chat (not /chat/mealplan)
2. _parse_days() only matched digits, not word-numbers like "three"
"""

import pytest
from app.services.chef_agent import ChefAgent


# ---------------------------------------------------------------------------
# _parse_days word-number support
# ---------------------------------------------------------------------------

class TestParseDaysWordNumbers:
    """_parse_days must accept both digit and word-form numbers."""

    @pytest.mark.parametrize("msg,expected", [
        ("generate a 3 day plan", 3),
        ("generate a 3-day plan", 3),
        ("generate a three-day plan", 3),
        ("generate a three day plan", 3),
        ("make a five-day meal plan", 5),
        ("plan for seven days", 7),
        ("I want a two day plan", 2),
        ("plan for 1 day", 1),
        ("plan for one day", 1),
    ])
    def test_parse_days_variants(self, msg: str, expected: int):
        result = ChefAgent._parse_days(msg)
        assert result == expected, f"_parse_days({msg!r}) → {result}, expected {expected}"

    def test_parse_days_no_match(self):
        assert ChefAgent._parse_days("hello world") is None

    def test_parse_days_digit_preferred_over_word(self):
        """When both digit and word appear, digit regex runs first."""
        result = ChefAgent._parse_days("3 day plan with two extra days")
        assert result == 3


# ---------------------------------------------------------------------------
# _parse_meals_per_day word-number support
# ---------------------------------------------------------------------------

class TestParseMealsPerDayWordNumbers:
    @pytest.mark.parametrize("msg,expected", [
        ("3 meals per day", 3),
        ("three meals per day", 3),
        ("two meals a day", 2),
        ("4 meals a day", 4),
    ])
    def test_parse_meals_variants(self, msg: str, expected: int):
        result = ChefAgent._parse_meals_per_day(msg)
        assert result == expected

    def test_parse_meals_no_match(self):
        assert ChefAgent._parse_meals_per_day("plan for three days") is None


# ---------------------------------------------------------------------------
# /chat/mealplan endpoint integration
# ---------------------------------------------------------------------------

class TestMealplanEndpoint:
    """Verify /chat/mealplan accepts fill-mode plan generation requests."""

    def test_mealplan_endpoint_three_day_plan(self, authed_client):
        """'generate a three-day plan' via /chat/mealplan must produce a plan, not fallback."""
        r = authed_client.post("/chat/mealplan", json={
            "mode": "fill",
            "message": "generate a three-day plan",
            "thread_id": "test-mp-word-days",
        })
        assert r.status_code == 200
        data = r.json()
        assert "I can help set preferences" not in data["reply_text"]
        # Should contain meal plan content (day references)
        reply_lower = data["reply_text"].lower()
        assert "day" in reply_lower or "meal" in reply_lower or len(data.get("proposed_actions", [])) > 0

    def test_mealplan_endpoint_numeric_days(self, authed_client):
        r = authed_client.post("/chat/mealplan", json={
            "mode": "fill",
            "message": "plan 2 days",
            "thread_id": "test-mp-numeric",
        })
        assert r.status_code == 200
        data = r.json()
        assert "I can help set preferences" not in data["reply_text"]

    def test_mealplan_endpoint_requires_fill(self, authed_client):
        """mealplan endpoint must reject mode=ask."""
        r = authed_client.post("/chat/mealplan", json={
            "mode": "ask",
            "message": "generate a three-day plan",
            "thread_id": "test-mp-ask-reject",
        })
        assert r.status_code == 400

    def test_mealplan_endpoint_requires_thread(self, authed_client):
        """mealplan endpoint must reject missing thread_id."""
        r = authed_client.post("/chat/mealplan", json={
            "mode": "fill",
            "message": "generate a three-day plan",
        })
        assert r.status_code == 400
