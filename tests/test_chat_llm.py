import os


def test_chat_llm_disabled(monkeypatch, authed_client):
    monkeypatch.delenv("LLM_ENABLED", raising=False)
    import app.api.routers.chat as chat_router

    chat_router.reset_chat_state_for_tests()
    resp = authed_client.post("/chat", json={"mode": "ask", "message": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert "LLM disabled" in body["reply_text"]
    assert body["confirmation_required"] is False


def test_chat_llm_invalid_model(monkeypatch, authed_client):
    monkeypatch.setenv("LLM_ENABLED", "1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
    import app.api.routers.chat as chat_router

    chat_router.reset_chat_state_for_tests()
    resp = authed_client.post("/chat", json={"mode": "ask", "message": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert "gpt-5" in body["reply_text"]
    assert body["confirmation_required"] is False


def test_chat_llm_uses_mock(monkeypatch, authed_client):
    monkeypatch.setenv("LLM_ENABLED", "1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-nano")

    def fake_reply(system_prompt: str, user_text: str) -> str:  # pragma: no cover - deterministic path
        return "mocked llm reply"

    import app.services.llm_client as llm_client

    monkeypatch.setattr(llm_client.LlmClient, "generate_reply", staticmethod(fake_reply))
    import app.api.routers.chat as chat_router

    chat_router.reset_chat_state_for_tests()

    resp = authed_client.post("/chat", json={"mode": "ask", "message": "hi there"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["reply_text"] == "mocked llm reply"
    assert body["confirmation_required"] is False


def test_chat_llm_toggle(monkeypatch, authed_client):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5-nano")
    monkeypatch.setenv("LLM_ENABLED", "0")
    import app.api.routers.chat as chat_router
    import app.services.llm_client as llm_client

    chat_router.reset_chat_state_for_tests()
    # start disabled by default (LLM_ENABLED unset)
    resp = authed_client.post("/chat", json={"mode": "ask", "message": "hello"})
    assert "LLM disabled" in resp.json()["reply_text"]

    resp = authed_client.post("/chat", json={"mode": "ask", "message": "/llm on"})
    assert "enabled" in resp.json()["reply_text"].lower()

    orig_generate = llm_client.LlmClient.generate_reply
    monkeypatch.setattr(llm_client.LlmClient, "generate_reply", staticmethod(lambda s, u: "live reply"))

    resp = authed_client.post("/chat", json={"mode": "ask", "message": "hello"})
    assert resp.json()["reply_text"] == "live reply"

    resp = authed_client.post("/chat", json={"mode": "ask", "message": "/llm off"})
    assert "disabled" in resp.json()["reply_text"].lower()

    monkeypatch.setattr(llm_client.LlmClient, "generate_reply", orig_generate)

    resp = authed_client.post("/chat", json={"mode": "ask", "message": "hello"})
    assert "LLM disabled" in resp.json()["reply_text"]
