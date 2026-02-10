"""Tests for /recipes/built-in-packs and /recipes/built-in-packs/install endpoints."""

import pytest
from unittest.mock import patch, MagicMock

# The service imports load_dataset at module level (with try/except fallback).
LOAD_DS_PATCH = "app.services.builtin_packs_service.load_dataset"


# ── catalogue listing ─────────────────────────────────────────────────────────

def test_list_packs_returns_catalogue(authed_client):
    resp = authed_client.get("/recipes/built-in-packs")
    assert resp.status_code == 200
    data = resp.json()
    assert "packs" in data
    assert len(data["packs"]) > 0
    pack = data["packs"][0]
    assert "pack_id" in pack
    assert "label" in pack
    assert "description" in pack
    assert "recipe_count" in pack


def test_list_packs_requires_auth(client):
    resp = client.get("/recipes/built-in-packs")
    assert resp.status_code == 401


# ── install ───────────────────────────────────────────────────────────────────

def test_install_pack_unknown_id_400(authed_client):
    resp = authed_client.post(
        "/recipes/built-in-packs/install",
        json={"pack_id": "nonexistent_pack_xyz"},
    )
    assert resp.status_code == 400


def _make_fake_dataset(rows):
    """Create a mock that behaves like a HF Dataset."""
    ds = MagicMock()
    ds.__len__ = lambda self: len(rows)
    ds.__iter__ = lambda self: iter(rows)
    ds.__getitem__ = lambda self, idx: rows[idx]
    return ds


def test_install_pack_writes_books(authed_client):
    fake_rows = [
        {
            "recipe_data": {
                "title": "Test Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Boil water. Add vegetables."},
                ],
            },
            "filename": "recipes/test_soup.html",
        },
        {
            "recipe_data": {
                "title": "Another Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Blend everything."},
                ],
            },
            "filename": "recipes/another_soup.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        resp = authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "soup", "max_recipes": 10},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["installed"] == 2
    assert len(data["books"]) == 2
    assert data["books"][0]["title"] == "Test Soup"

    # Verify books are in the listing
    books_resp = authed_client.get("/recipes/books")
    assert books_resp.status_code == 200
    assert len(books_resp.json()["books"]) == 2


def test_install_pack_idempotent(authed_client):
    fake_rows = [
        {
            "recipe_data": {
                "title": "Cake One",
                "infobox": {"category": "/wiki/Category:Cake_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Mix flour and sugar."},
                ],
            },
            "filename": "recipes/cake_one.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        resp1 = authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "cake"},
        )
        resp2 = authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "cake"},
        )

    assert resp1.status_code == 200
    assert resp1.json()["installed"] == 1
    # Second install should be idempotent — 0 new
    assert resp2.status_code == 200
    assert resp2.json()["installed"] == 0


def test_install_pack_requires_auth(client):
    resp = client.post(
        "/recipes/built-in-packs/install",
        json={"pack_id": "soup"},
    )
    assert resp.status_code == 401


def test_install_pack_filters_by_category(authed_client):
    """Install 'pasta' pack — should skip rows whose category doesn't match."""
    fake_rows = [
        {
            "recipe_data": {
                "title": "Pasta Carbonara",
                "infobox": {"category": "/wiki/Category:Pasta_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Cook pasta. Add eggs."},
                ],
            },
            "filename": "recipes/pasta_carbonara.html",
        },
        {
            "recipe_data": {
                "title": "Chocolate Cake",
                "infobox": {"category": "/wiki/Category:Cake_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Not pasta."},
                ],
            },
            "filename": "recipes/chocolate_cake.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        resp = authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "pasta"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["installed"] == 1
    assert data["books"][0]["title"] == "Pasta Carbonara"


# ── preview ───────────────────────────────────────────────────────────────────

def test_preview_pack_returns_titles(authed_client):
    fake_rows = [
        {
            "recipe_data": {
                "title": "Test Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Boil water."},
                ],
            },
            "filename": "recipes/test_soup.html",
        },
        {
            "recipe_data": {
                "title": "Another Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Blend everything."},
                ],
            },
            "filename": "recipes/another_soup.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        resp = authed_client.get("/recipes/built-in-packs/soup/preview?max_recipes=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["pack_id"] == "soup"
    assert data["label"] == "Soups"
    assert data["total_available"] == 2
    assert len(data["recipes"]) == 2
    assert data["recipes"][0]["title"] == "Test Soup"
    assert data["recipes"][0]["has_content"] is True
    assert data["recipes"][1]["title"] == "Another Soup"


def test_preview_pack_unknown_400(authed_client):
    resp = authed_client.get("/recipes/built-in-packs/nonexistent_xyz/preview")
    assert resp.status_code == 400


def test_preview_pack_requires_auth(client):
    resp = client.get("/recipes/built-in-packs/soup/preview")
    assert resp.status_code == 401


# ── selective install ─────────────────────────────────────────────────────────

def test_install_pack_selected_titles(authed_client):
    """Install only selected recipes by title."""
    fake_rows = [
        {
            "recipe_data": {
                "title": "Tomato Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Cook tomatoes."},
                ],
            },
            "filename": "recipes/tomato_soup.html",
        },
        {
            "recipe_data": {
                "title": "Onion Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Caramelize onions."},
                ],
            },
            "filename": "recipes/onion_soup.html",
        },
        {
            "recipe_data": {
                "title": "Mushroom Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Blend mushrooms."},
                ],
            },
            "filename": "recipes/mushroom_soup.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        resp = authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "soup", "selected_titles": ["Onion Soup"]},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["installed"] == 1
    assert data["books"][0]["title"] == "Onion Soup"


def test_install_pack_selected_titles_empty_list(authed_client):
    """Empty selected_titles list installs nothing."""
    fake_rows = [
        {
            "recipe_data": {
                "title": "Tomato Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Cook tomatoes."},
                ],
            },
            "filename": "recipes/tomato_soup.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        resp = authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "soup", "selected_titles": []},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["installed"] == 0
    assert len(data["books"]) == 0


# ── uninstall ─────────────────────────────────────────────────────────────────

def test_uninstall_pack_removes_books(authed_client):
    """Install a pack, then uninstall all — should remove everything."""
    fake_rows = [
        {
            "recipe_data": {
                "title": "Tomato Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Tomato goodness."},
                ],
            },
            "filename": "recipes/tomato_soup.html",
        },
        {
            "recipe_data": {
                "title": "Onion Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Onion goodness."},
                ],
            },
            "filename": "recipes/onion_soup.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "soup"},
        )

    # Uninstall all
    resp = authed_client.post(
        "/recipes/built-in-packs/uninstall",
        json={"pack_id": "soup"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["removed"] == 2

    # Verify pack is no longer installed
    packs_resp = authed_client.get("/recipes/built-in-packs")
    for p in packs_resp.json()["packs"]:
        if p["pack_id"] == "soup":
            assert p.get("installed") is not True


def test_uninstall_pack_selective(authed_client):
    """Install 2 recipes, uninstall 1 by title — should remove only that one."""
    fake_rows = [
        {
            "recipe_data": {
                "title": "Tomato Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Tomato goodness."},
                ],
            },
            "filename": "recipes/tomato_soup.html",
        },
        {
            "recipe_data": {
                "title": "Onion Soup",
                "infobox": {"category": "/wiki/Category:Soup_recipes"},
                "text_lines": [
                    {"line_type": "p", "section": None, "text": "Onion goodness."},
                ],
            },
            "filename": "recipes/onion_soup.html",
        },
    ]
    fake_ds = _make_fake_dataset(fake_rows)

    with patch(LOAD_DS_PATCH, return_value=fake_ds):
        authed_client.post(
            "/recipes/built-in-packs/install",
            json={"pack_id": "soup"},
        )

    # Uninstall only Tomato Soup
    resp = authed_client.post(
        "/recipes/built-in-packs/uninstall",
        json={"pack_id": "soup", "selected_titles": ["Tomato Soup"]},
    )
    assert resp.status_code == 200
    assert resp.json()["removed"] == 1

    # Verify Onion Soup still exists
    books_resp = authed_client.get("/recipes/books")
    titles = [b["title"] for b in books_resp.json()["books"]]
    assert "Onion Soup" in titles
    assert "Tomato Soup" not in titles


def test_uninstall_pack_unknown_400(authed_client):
    resp = authed_client.post(
        "/recipes/built-in-packs/uninstall",
        json={"pack_id": "nonexistent_pack_xyz"},
    )
    assert resp.status_code == 400


def test_uninstall_pack_requires_auth(client):
    resp = client.post(
        "/recipes/built-in-packs/uninstall",
        json={"pack_id": "soup"},
    )
    assert resp.status_code == 401
