from pathlib import Path


def test_onboarding_copy_present():
    main_ts = Path("web/src/main.ts").read_text(encoding="utf-8")
    assert "Welcome — I’m Little Chef. To start onboarding" in main_ts
    assert "Press and hold to start onboarding with preferences" in main_ts
    assert "flow-menu-item" in main_ts and "Preferences" in main_ts
    assert "To get started, let’s set your preferences" in main_ts
    assert "setPointerCapture" in main_ts
    assert "elementFromPoint" in main_ts
    assert "onboardMenuActive" in main_ts
    assert "lostpointercapture" in main_ts
    assert "onboardIgnoreDocClickUntilMs" in main_ts
