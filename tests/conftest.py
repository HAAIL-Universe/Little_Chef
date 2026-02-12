import warnings

warnings.filterwarnings(
    "ignore",
    message=".*'app' shortcut is now deprecated.*",
    category=DeprecationWarning,
)

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.deps import get_current_user
from app.schemas import UserMe
from app.services.prefs_service import get_prefs_service
import app.api.routers.chat as chat_router
from app.services.chat_service import ChatService
from app.services.inventory_service import get_inventory_service
import app.api.routers.recipes as recipes_router
import app.api.routers.alexa as alexa_router
import app.api.routers.household as household_router
from app.services.recipe_service import get_recipe_service, reset_recipe_service_cache
from app.services.shopping_service import reset_shopping_service_cache
from app.services.mealplan_service import reset_mealplan_service_cache
from app.services.llm_client import get_llm_client
import os


@pytest.fixture
def _clear_db_env():
    os.environ["LC_DISABLE_DOTENV"] = "1"
    os.environ["DATABASE_URL"] = ""
    yield
    os.environ["DATABASE_URL"] = ""
    os.environ["LC_DISABLE_DOTENV"] = "1"


@pytest.fixture
def app_instance(tmp_path, monkeypatch):
    # Redirect recipe file storage to temp dir so tests don't pollute data/recipe_books/
    import app.repos.recipe_repo as _recipe_repo_mod
    monkeypatch.setattr(_recipe_repo_mod, "DATA_DIR", str(tmp_path / "recipe_books"))

    # Reset cached services/state for deterministic tests
    get_prefs_service.cache_clear()
    get_inventory_service.cache_clear()
    reset_recipe_service_cache()
    reset_shopping_service_cache()
    reset_mealplan_service_cache()
    chat_router.reset_chat_state_for_tests()
    recipes_router.reset_recipes_for_tests()
    alexa_router.reset_alexa_for_tests()
    household_router.reset_household_for_tests()
    return create_app()


@pytest.fixture
def client(app_instance, _clear_db_env):
    with TestClient(app_instance) as c:
        yield c


@pytest.fixture
def authed_client(app_instance, _clear_db_env):
    app_instance.dependency_overrides[get_current_user] = lambda: UserMe(
        user_id="test-user", provider_subject="sub", email=None
    )
    with TestClient(app_instance) as c:
        yield c
    app_instance.dependency_overrides.clear()
