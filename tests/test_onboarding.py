import pytest
from fastapi.testclient import TestClient

from app.schemas import UserMe, InventoryEventCreateRequest
from app.services.inventory_service import get_inventory_service
from app.main import create_app
import app.api.routers.auth as auth_router
from app.services.prefs_service import get_prefs_service
from app.services.recipe_service import reset_recipe_service_cache
from app.services.shopping_service import reset_shopping_service_cache
from app.services.mealplan_service import reset_mealplan_service_cache
import app.api.routers.chat as chat_router
import app.api.routers.recipes as recipes_router
import os


@pytest.fixture
def fresh_app():
    os.environ["LC_DISABLE_DOTENV"] = "1"
    os.environ["DATABASE_URL"] = ""
    get_prefs_service.cache_clear()
    get_inventory_service.cache_clear()
    reset_recipe_service_cache()
    reset_shopping_service_cache()
    reset_mealplan_service_cache()
    chat_router.reset_chat_state_for_tests()
    recipes_router.reset_recipes_for_tests()
    return create_app()


def patch_auth(monkeypatch, user_id="u1"):
    monkeypatch.setattr(auth_router, "_extract_bearer_token", lambda authorization: "token")

    class FakeAuth:
        def resolve_user(self, token):
            return UserMe(user_id=user_id, provider_subject="sub", email=None)

    monkeypatch.setattr(auth_router, "get_auth_service", lambda: FakeAuth())


def test_auth_me_onboarded_false_when_no_inventory(monkeypatch, fresh_app):
    patch_auth(monkeypatch, user_id="u1")
    with TestClient(fresh_app) as client:
        resp = client.get("/auth/me", headers={"Authorization": "Bearer dummy"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded"] is False


def test_auth_me_onboarded_true_when_inventory_exists(monkeypatch, fresh_app):
    patch_auth(monkeypatch, user_id="u2")
    inv = get_inventory_service()
    inv.create_event(
        "u2",
        "sub",
        None,
        InventoryEventCreateRequest(event_type="add", item_name="eggs", quantity=1, unit="count", note="test", source="test"),
    )
    with TestClient(fresh_app) as client:
        resp = client.get("/auth/me", headers={"Authorization": "Bearer dummy"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["onboarded"] is True
