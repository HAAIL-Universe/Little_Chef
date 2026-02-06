import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.deps import get_current_user
from app.schemas import UserMe, ChatRequest
from app.services.prefs_service import get_prefs_service
import app.api.routers.chat as chat_router
import app.api.routers.recipes as recipes_router
from app.services.recipe_service import reset_recipe_service_cache
from app.services.shopping_service import reset_shopping_service_cache
from app.services.mealplan_service import reset_mealplan_service_cache


@pytest.fixture
def client():
    get_prefs_service.cache_clear()
    reset_recipe_service_cache()
    reset_shopping_service_cache()
    reset_mealplan_service_cache()
    chat_router.reset_chat_state_for_tests()
    recipes_router.reset_recipes_for_tests()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: UserMe(user_id="u1", provider_subject="sub", email=None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_prefs_missing_loop_and_confirm(client, monkeypatch):
    # monkeypatch prefs_repo upsert to record calls
    calls = []

    from app.services import prefs_service as ps

    original_upsert = ps.get_prefs_service().upsert_prefs

    def fake_upsert(user_id, provider_subject, email, prefs):
        calls.append(prefs)
        return prefs

    monkeypatch.setattr(ps.get_prefs_service(), "upsert_prefs", fake_upsert)

    thread = "11111111-1111-4111-8111-111111111111"

    # missing fields -> ask question
    resp1 = client.post(
        "/chat",
        json={"mode": "fill", "message": "allergies peanuts", "include_user_library": True, "thread_id": thread},
    )
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["confirmation_required"] is False
    assert "servings" in data1["reply_text"].lower() or "meals" in data1["reply_text"].lower()

    # supply required fields
    resp2 = client.post(
        "/chat",
        json={"mode": "fill", "message": "2 servings and 3 meals per day", "include_user_library": True, "thread_id": thread},
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["confirmation_required"] is True
    proposal_id = data2["proposal_id"]
    assert proposal_id

    # confirm writes once
    resp3 = client.post("/chat/confirm", json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread})
    assert resp3.status_code == 200
    assert resp3.json()["applied"] is True
    assert len(calls) == 1
    saved = calls[0]
    assert saved.servings == 2
    assert saved.meals_per_day == 3

