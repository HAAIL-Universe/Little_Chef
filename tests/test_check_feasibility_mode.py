"""Phase 10.5 — Feasibility check (CHECK): "Can I cook X?"

Tests that:
- CHECK queries via POST /chat return feasibility assessment
- Recipe search uses substring matching
- Feasibility labels: feasible / almost / not feasible
- Missing ingredients listed
- Alternatives suggested when available
- Informational only (no proposal, no confirmation_required)
"""

import pytest

from app.services.chef_agent import _CHECK_RE
from app.services.recipe_service import get_recipe_service
from app.services.inventory_service import get_inventory_service


@pytest.fixture(autouse=True)
def _reset_inventory_cache(_clear_db_env):
    """Ensure inventory service uses in-memory repo after _clear_db_env sets DATABASE_URL=''."""
    get_inventory_service.cache_clear()
    yield
    get_inventory_service.cache_clear()


# ── Unit: CHECK regex detection ──────────────────────────────────────────

@pytest.mark.parametrize("msg,expected_name", [
    ("can I cook Tomato Pasta?", "Tomato Pasta"),
    ("Can I make garlic butter chicken?", "garlic butter chicken"),
    ("can I prepare Veggie Stir Fry?", "Veggie Stir Fry"),
    ("can i cook tomato pasta", "tomato pasta"),
    ("do i have enough for tomato pasta?", "tomato pasta"),
    ("do i have what i need to cook Veggie Stir Fry?", "Veggie Stir Fry"),
])
def test_check_regex_detects_queries(msg, expected_name):
    m = _CHECK_RE.search(msg)
    assert m, f"CHECK regex should detect: {msg!r}"
    name = (m.group(1) or m.group(2) or m.group(3) or "").strip().rstrip("?").strip()
    assert name.lower() == expected_name.lower()


@pytest.mark.parametrize("msg", [
    "what can I make?",
    "suggest meals",
    "hello",
    "set my preferences",
    "add 2 eggs to inventory",
])
def test_check_regex_ignores_non_check_queries(msg):
    assert not _CHECK_RE.search(msg), f"CHECK regex should NOT detect: {msg!r}"


# ── Integration: CHECK via POST /chat ────────────────────────────────────

def test_check_feasible_with_full_inventory(authed_client):
    """Recipe is feasible when all ingredients are in stock."""
    # Simple Tomato Pasta needs: tomato, pasta
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "tomato", "quantity": 5, "unit": "count",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "pasta", "quantity": 500, "unit": "g",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Tomato Pasta?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Feasible" in body["reply_text"]
    assert "100%" in body["reply_text"]
    assert "Simple Tomato Pasta" in body["reply_text"]
    assert body["confirmation_required"] is False
    assert body["proposal_id"] is None


def test_check_almost_feasible(authed_client):
    """Recipe is 'almost' feasible when >= 50% ingredients are in stock."""
    # Veggie Stir Fry needs: mixed veggies, soy sauce (2 ingredients)
    # With 1 of 2 in stock = 50% → 'Almost'
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "mixed veggies", "quantity": 250, "unit": "g",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Veggie Stir Fry?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Almost" in body["reply_text"]
    assert "Veggie Stir Fry" in body["reply_text"]


def test_check_not_feasible(authed_client):
    """Recipe is 'not feasible' when < 50% ingredients are in stock."""
    # Empty inventory → 0% match
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Veggie Stir Fry?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Not feasible" in body["reply_text"]
    assert "Missing:" in body["reply_text"]


def test_check_shows_missing_ingredients(authed_client):
    """Missing ingredients are listed in the response."""
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "tomato", "quantity": 5, "unit": "count",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Tomato Pasta?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Missing:" in body["reply_text"]
    assert "pasta" in body["reply_text"].lower()


def test_check_recipe_not_found(authed_client):
    """Unknown recipe name returns a 'not found' message."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Unicorn Soufflé?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "couldn't find" in body["reply_text"].lower()


def test_check_substring_match(authed_client):
    """Substring matching finds recipes by partial name."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook tomato?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Should match "Simple Tomato Pasta" via substring
    assert "Simple Tomato Pasta" in body["reply_text"]


def test_check_suggests_alternatives(authed_client):
    """Alternatives with better coverage are suggested."""
    # Seed inventory to make Tomato Pasta fully feasible,
    # then check a recipe with lower coverage — alternatives should appear
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "tomato", "quantity": 5, "unit": "count",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "pasta", "quantity": 500, "unit": "g",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Garlic Butter Chicken?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    # Garlic Butter Chicken is 0% → alternatives should include Tomato Pasta at 100%
    assert "Alternative" in body["reply_text"]
    assert "Simple Tomato Pasta" in body["reply_text"]


def test_check_no_proposal(authed_client):
    """CHECK is informational — no proposal created."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Tomato Pasta?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is False
    assert body["proposal_id"] is None
    assert body["proposed_actions"] == []


def test_check_suggested_next_questions(authed_client):
    """CHECK response includes suggested follow-up questions."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Tomato Pasta?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["suggested_next_questions"]) > 0


def test_check_with_pack_recipe(authed_client):
    """Pack recipes are searchable via CHECK."""
    from app.api.routers.chat import _chat_service
    _chat_service.chef_agent.recipe_service = get_recipe_service()

    svc = get_recipe_service()
    svc.repo.create_pack_book(
        "Lemon Herb Salmon",
        "lemon_herb_salmon.md",
        "# Lemon Herb Salmon\n\n## Ingredients\n\n- 2 count salmon fillet\n- 1 count lemon\n- 10 g dill\n\n## Procedure\n\nBake at 200C.\n",
        "seafood",
    )

    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "salmon fillet", "quantity": 2, "unit": "count",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "lemon", "quantity": 3, "unit": "count",
    })
    authed_client.post("/inventory/events", json={
        "event_type": "add", "item_name": "dill", "quantity": 20, "unit": "g",
    })

    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "can I cook Lemon Herb Salmon?"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "Lemon Herb Salmon" in body["reply_text"]
    assert "Feasible" in body["reply_text"]
    assert "100%" in body["reply_text"]
