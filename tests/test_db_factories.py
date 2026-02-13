import importlib
import os

import pytest

from app.services import auth_service


def _clear_caches():
    # service caches may hold repos built with previous env
    auth_service.get_auth_service.cache_clear()


def test_factories_use_in_memory_when_no_db(monkeypatch):
    monkeypatch.setenv("LC_DISABLE_DOTENV", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    _clear_caches()
    prefs_repo = importlib.reload(importlib.import_module("app.repos.prefs_repo"))
    inventory_repo = importlib.reload(importlib.import_module("app.repos.inventory_repo"))
    mealplan_repo = importlib.reload(importlib.import_module("app.repos.mealplan_repo"))

    prefs_repo = importlib.reload(prefs_repo)
    inventory_repo = importlib.reload(inventory_repo)
    mealplan_repo = importlib.reload(mealplan_repo)

    assert isinstance(prefs_repo.get_prefs_repository(), prefs_repo.PrefsRepository)
    assert isinstance(inventory_repo.get_inventory_repository(), inventory_repo.InventoryRepository)
    assert isinstance(mealplan_repo.get_mealplan_repository(), mealplan_repo.MealPlanRepository)


def test_factories_select_db_when_env(monkeypatch):
    monkeypatch.setenv("LC_DISABLE_DOTENV", "1")
    monkeypatch.setenv("DATABASE_URL", "postgres://example")
    _clear_caches()
    prefs_repo = importlib.reload(importlib.import_module("app.repos.prefs_repo"))
    inventory_repo = importlib.reload(importlib.import_module("app.repos.inventory_repo"))
    mealplan_repo = importlib.reload(importlib.import_module("app.repos.mealplan_repo"))

    # ensure connect is not invoked until methods are used
    assert isinstance(prefs_repo.get_prefs_repository(), prefs_repo.DbPrefsRepository)
    assert isinstance(inventory_repo.get_inventory_repository(), inventory_repo.DbInventoryRepository)
    assert isinstance(mealplan_repo.get_mealplan_repository(), mealplan_repo.DbMealPlanRepository)


def test_deterministic_user_id_stable():
    first = auth_service._deterministic_user_id("subj-123")
    second = auth_service._deterministic_user_id("subj-123")
    assert first == second
    other = auth_service._deterministic_user_id("subj-456")
    assert other != first
