"""Phase 10.4 — Decision mode (MATCH): "What can I make right now?"

Tests that:
- MATCH queries via POST /chat return ranked suggestions with completion %
- Inventory-aware scoring ranks recipes with more matching ingredients higher
- Missing ingredients are listed per suggestion
- Allergy/dislike filtering applies
- Built-in fallback works when no packs installed
- Cook time prefs note appears when set
- MATCH is informational only (no proposal, no confirmation_required)
"""

import pytest

from app.services.chef_agent import ChefAgent, _MATCH_RE
from app.services.recipe_service import (
    get_recipe_service,
    reset_recipe_service_cache,
)
from app.schemas import IngredientLine


# ── Unit: MATCH regex detection ──────────────────────────────────────────

@pytest.mark.parametrize("msg", [
    "what can I make",
    "What can I cook?",
    "what should i eat",
    "what could I make tonight",
    "suggest meals",
    "suggest something",
    "recipe ideas",
    "meal ideas",
    "what to cook",
])
def test_match_regex_detects_match_queries(msg):
    assert _MATCH_RE.search(msg), f"MATCH regex should detect: {msg!r}"


@pytest.mark.parametrize("msg", [
    "set my preferences",
    "add 2 eggs to inventory",
    "tell me about pasta",
    "hello",
])
def test_match_regex_ignores_non_match_queries(msg):
    assert not _MATCH_RE.search(msg), f"MATCH regex should NOT detect: {msg!r}"


# ── Unit: recipe scoring ─────────────────────────────────────────────────

def test_score_recipe_full_match():
    ingredients = [
        IngredientLine(item_name="tomato", quantity=2, unit="count"),
        IngredientLine(item_name="pasta", quantity=200, unit="g"),
    ]
    stock = {"tomato", "pasta"}
    pct, missing = ChefAgent._score_recipe(ingredients, stock)
    assert pct == 1.0
    assert missing == []


def test_score_recipe_partial_match():
    ingredients = [
        IngredientLine(item_name="tomato", quantity=2, unit="count"),
        IngredientLine(item_name="pasta", quantity=200, unit="g"),
        IngredientLine(item_name="basil", quantity=1, unit="count"),
    ]
    stock = {"tomato"}
    pct, missing = ChefAgent._score_recipe(ingredients, stock)
    assert abs(pct - 1 / 3) < 0.01
    assert set(missing) == {"pasta", "basil"}


def test_score_recipe_no_match():
    ingredients = [
        IngredientLine(item_name="chicken", quantity=1, unit="count"),
    ]
    stock = {"tomato", "pasta"}
    pct, missing = ChefAgent._score_recipe(ingredients, stock)
    assert pct == 0.0
    assert missing == ["chicken"]


def test_score_recipe_empty_ingredients():
    pct, missing = ChefAgent._score_recipe([], set())
    assert pct == 0.0
    assert missing == []


# ── Integration: MATCH via POST /chat ────────────────────────────────────

def test_match_returns_suggestions_via_chat(authed_client):
    """'what can I make' via /chat returns ranked suggestions."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I make?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is False
    assert body["proposal_id"] is None
    # Should contain recipe names from built-in catalog
    assert "ingredients in stock" in body["reply_text"]


def test_match_with_inventory_ranks_by_completion(authed_client):
    """Recipes with more matching inventory items rank higher."""
    # Seed inventory with tomato + pasta (matches builtin_1: Simple Tomato Pasta)
    authed_client.post("/inventory/events", json={
        "event_type": "add",
        "item_name": "tomato",
        "quantity": 5,
        "unit": "count",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add",
        "item_name": "pasta",
        "quantity": 500,
        "unit": "g",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I make?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    reply = body["reply_text"]
    # Simple Tomato Pasta should rank first (100% match with tomato + pasta)
    assert "Simple Tomato Pasta" in reply
    assert "100%" in reply


def test_match_shows_missing_ingredients(authed_client):
    """Missing ingredients are listed for each suggestion."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I cook?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # With empty inventory, all ingredients are missing
    assert "Missing:" in body["reply_text"]


def test_match_with_pack_recipes(authed_client):
    """Pack recipes are included in MATCH suggestions."""
    # Align ChefAgent's recipe_service with the current cached instance
    # (fixture ordering causes instance divergence — see conftest.py)
    from app.api.routers.chat import _chat_service
    _chat_service.chef_agent.recipe_service = get_recipe_service()

    svc = get_recipe_service()
    svc.repo.create_pack_book(
        "Mushroom Risotto",
        "mushroom_risotto.md",
        "# Mushroom Risotto\n\n## Ingredients\n\n- 200 g rice\n- 150 g mushroom\n- 500 ml broth\n\n## Procedure\n\nStir frequently.\n",
        "italian",
    )
    # Seed inventory with rice and mushroom
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "rice", "quantity": 500, "unit": "g",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "mushroom", "quantity": 200, "unit": "g",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I make?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Mushroom Risotto" in body["reply_text"]


def test_match_excludes_allergy_recipes(authed_client):
    """Recipes matching allergies are excluded from suggestions."""
    authed_client.put("/prefs", json={"prefs": {
        "allergies": ["chicken"],
        "dislikes": [],
        "cuisine_likes": [],
        "servings": 2,
        "meals_per_day": 3,
    }})

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I make?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Garlic Butter Chicken should be excluded
    assert "Garlic Butter Chicken" not in body["reply_text"]


def test_match_cook_time_note(authed_client):
    """Cook time prefs note appears when set."""
    authed_client.put("/prefs", json={"prefs": {
        "allergies": [],
        "dislikes": [],
        "cuisine_likes": [],
        "servings": 2,
        "meals_per_day": 3,
        "cook_time_weekday_mins": 30,
    }})

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I cook?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "weekday" in body["reply_text"].lower()
    assert "30" in body["reply_text"]


def test_match_no_proposal_created(authed_client):
    """MATCH is informational — no proposal, no confirmation."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "what can I make?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is False
    assert body["proposal_id"] is None
    assert body["proposed_actions"] == []


def test_match_suggested_next_questions(authed_client):
    """MATCH response includes suggested follow-up questions."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "suggest meals"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["suggested_next_questions"]) > 0
