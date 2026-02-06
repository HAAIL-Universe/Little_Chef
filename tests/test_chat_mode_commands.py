import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.deps import get_current_user
from app.schemas import UserMe
import app.api.routers.chat as chat_router


@pytest.fixture
def client():
    chat_router.reset_chat_state_for_tests()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: UserMe(user_id="u-mode", provider_subject="sub", email=None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_fill_command_sets_mode_and_echoes(client):
    thread = "t-mode-1"
    res = client.post("/chat", json={"mode": "ask", "message": "/fill", "thread_id": thread})
    assert res.status_code == 200
    body = res.json()
    assert "fill" in body["reply_text"].lower()
    assert body["mode"] == "fill"

    res2 = client.post("/chat", json={"mode": "ask", "message": "hello", "thread_id": thread})
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["mode"] == "fill"


def test_ask_command_flips_back(client):
    thread = "t-mode-2"
    client.post("/chat", json={"mode": "ask", "message": "/fill", "thread_id": thread})
    res = client.post("/chat", json={"mode": "ask", "message": "/ask", "thread_id": thread})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "ask"


def test_mode_command_requires_thread(client):
    res = client.post("/chat", json={"mode": "ask", "message": "/fill"})
    assert res.status_code == 200
    body = res.json()
    assert "thread id" in body["reply_text"].lower()


def test_override_controls_routing_even_if_request_mode_is_ask(client):
    thread = "t-mode-override"
    client.post("/chat", json={"mode": "ask", "message": "/fill", "thread_id": thread})
    res = client.post("/chat", json={"mode": "ask", "message": "hello", "thread_id": thread})
    assert res.status_code == 200
    body = res.json()
    assert body["mode"] == "fill"
    assert "try fill mode" not in body["reply_text"].lower()
