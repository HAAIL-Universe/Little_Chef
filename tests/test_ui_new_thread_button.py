from pathlib import Path


def test_new_thread_button_and_thread_reset_hooks_present():
    src = Path("web/src/main.ts").read_text()
    assert "New Thread" in src
    assert "startNewThread" in src
    # thread id regeneration uses crypto.randomUUID in startNewThread or ensureThread
    assert "crypto.randomUUID" in src
    # history clear in startNewThread
    assert "duetState.history = []" in src

