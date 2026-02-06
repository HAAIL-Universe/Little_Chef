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


def test_onboard_menu_inventory_button_gated_by_onboarded():
    main_ts = Path("web/src/main.ts").read_text(encoding="utf-8")
    start = main_ts.index("function renderOnboardMenuButtons")
    end = main_ts.index("function hideOnboardMenu", start)
    section = main_ts[start:end]
    assert 'state.onboarded' in section
    assert 'textContent = "Inventory"' in section
    assert 'selectFlow("inventory")' in section


def test_prefs_overlay_strings_present():
    main_ts = Path("web/src/main.ts").read_text(encoding="utf-8")
    assert "setupPrefsOverlay" in main_ts
    assert "refreshPrefsOverlay" in main_ts
    assert "No preferences yet." in main_ts
    assert 'currentFlowKey === "prefs" && !!state.onboarded' in main_ts


def test_overlay_pointer_events_split():
    main_ts = Path("web/src/main.ts").read_text(encoding="utf-8")
    inv_start = main_ts.index("function setupInventoryGhostOverlay")
    inv_end = main_ts.index("function setPrefsOverlayStatus", inv_start)
    inv_section = main_ts[inv_start:inv_end]
    assert 'overlay.style.pointerEvents = "none";' in inv_section
    assert 'panel.style.pointerEvents = "auto";' in inv_section

    prefs_start = main_ts.index("function setupPrefsOverlay")
    prefs_end = main_ts.index("function ensureOnboardMenu", prefs_start)
    prefs_section = main_ts[prefs_start:prefs_end]
    assert 'overlay.style.pointerEvents = "none";' in prefs_section
    assert 'panel.style.pointerEvents = "auto";' in prefs_section


def test_overlay_and_bubble_zindex():
    main_ts = Path("web/src/main.ts").read_text(encoding="utf-8")
    assert 'overlay.style.zIndex = "1";' in main_ts
    assert 'userBubble.style.zIndex = "50";' in main_ts
    assert 'assistantBubble.style.zIndex = "50";' in main_ts
