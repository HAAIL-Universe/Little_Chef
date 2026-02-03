import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.deps import get_current_user
from app.schemas import UserMe
from app.services.prefs_service import get_prefs_service
import app.api.routers.chat as chat_router
from app.services.chat_service import ChatService


@pytest.fixture
def app_instance():
    # Reset cached services/state for deterministic tests
    get_prefs_service.cache_clear()
    chat_router._proposal_store.clear()
    chat_router._chat_service = ChatService(get_prefs_service(), chat_router._proposal_store)
    return create_app()


@pytest.fixture
def client(app_instance):
    with TestClient(app_instance) as c:
        yield c


@pytest.fixture
def authed_client(app_instance):
    app_instance.dependency_overrides[get_current_user] = lambda: UserMe(
        user_id="test-user", provider_subject="sub", email=None
    )
    with TestClient(app_instance) as c:
        yield c
    app_instance.dependency_overrides.clear()
