import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.deps import get_current_user
from app.schemas import UserMe
import app.api.routers.chat as chat_router


class InMemoryThreadMessagesRepo:
    def __init__(self):
        self.data = []
        self.counts = {}

    def append_message(self, thread_id, user_id, role, content):
        n = self.counts.get(thread_id, 0) + 1
        self.counts[thread_id] = n
        msg_id = f"{thread_id}-{n}"
        self.data.append({"thread_id": thread_id, "user_id": user_id, "role": role, "content": content, "message_id": msg_id})
        return msg_id


@pytest.fixture
def client():
    chat_router.reset_chat_state_for_tests()
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: UserMe(user_id="u1", provider_subject="sub", email=None)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_thread_messages_insert_two_rows_per_chat_turn(client, monkeypatch):
    repo = InMemoryThreadMessagesRepo()
    chat_router._chat_service.thread_messages_repo = repo

    thread = "t-msg-1"
    resp = client.post("/chat", json={"mode": "ask", "message": "hello there", "thread_id": thread})
    assert resp.status_code == 200
    assert len(repo.data) == 2
    roles = [m["role"] for m in repo.data]
    assert roles == ["user", "assistant"]
    assert repo.data[0]["message_id"] == f"{thread}-1"
    assert repo.data[1]["message_id"] == f"{thread}-2"


def test_message_id_increments_within_thread(client, monkeypatch):
    repo = InMemoryThreadMessagesRepo()
    chat_router._chat_service.thread_messages_repo = repo

    thread = "t-msg-2"
    client.post("/chat", json={"mode": "ask", "message": "hi", "thread_id": thread})
    client.post("/chat", json={"mode": "ask", "message": "hi again", "thread_id": thread})

    ids = [m["message_id"] for m in repo.data]
    assert ids == [f"{thread}-1", f"{thread}-2", f"{thread}-3", f"{thread}-4"]
