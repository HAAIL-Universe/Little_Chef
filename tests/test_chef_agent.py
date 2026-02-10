def test_chef_agent_requires_auth(client):
    resp = client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 5 days", "thread_id": "t-chef-1"},
    )
    assert resp.status_code == 401


def test_chef_agent_requires_thread_id(authed_client):
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 3 days"},
    )
    assert resp.status_code == 400


def test_chef_agent_requires_fill_mode(authed_client):
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "ask", "message": "plan for 3 days", "thread_id": "t-chef-2"},
    )
    assert resp.status_code == 400


def test_chef_agent_propose_and_confirm(authed_client):
    thread = "t-chef-plan"
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 5 days, 3 meals per day", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposal_id"] is not None
    proposal_id = body["proposal_id"]
    assert len(body["proposed_actions"]) == 1
    action = body["proposed_actions"][0]
    assert action["action_type"] == "generate_mealplan"
    plan = action["mealplan"]
    assert len(plan["days"]) == 5
    for day in plan["days"]:
        assert len(day["meals"]) == 3

    # Confirm
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert resp.status_code == 200
    confirm_body = resp.json()
    assert confirm_body["applied"] is True
    assert len(confirm_body["applied_event_ids"]) == 1
    assert confirm_body["applied_event_ids"][0] == plan["plan_id"]


def test_chef_agent_propose_and_decline(authed_client):
    thread = "t-chef-decline"
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 2 days, 2 meals per day", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    proposal_id = body["proposal_id"]

    # Decline
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": False, "thread_id": thread},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is False


def test_chef_agent_defaults_when_no_params(authed_client):
    """When message has no explicit days/meals, prefs defaults should be used."""
    thread = "t-chef-defaults"
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "make me a meal plan", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    action = body["proposed_actions"][0]
    plan = action["mealplan"]
    # defaults from prefs: plan_days=7, meals_per_day=3
    assert len(plan["days"]) == 7
    for day in plan["days"]:
        assert len(day["meals"]) == 3


def test_chef_agent_thread_isolation(authed_client):
    """Proposals from different threads don't interfere."""
    thread_a = "t-chef-iso-a"
    thread_b = "t-chef-iso-b"

    resp_a = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 2 days", "thread_id": thread_a},
    )
    resp_b = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 4 days", "thread_id": thread_b},
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200

    pid_a = resp_a.json()["proposal_id"]
    pid_b = resp_b.json()["proposal_id"]
    assert pid_a != pid_b

    # Confirm A with thread B should fail (proposal not found for wrong thread)
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid_a, "confirm": True, "thread_id": thread_b},
    )
    assert resp.status_code == 400

    # Confirm A with correct thread
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid_a, "confirm": True, "thread_id": thread_a},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is True
