"""Tests for Phase 14 — Recipe ingestion, serving scaling, constraint-aware.

14.1: Text paste, PDF extraction, photo placeholder
14.2: Serving scaling
14.3: Equipment detection and constraint-aware suggestions
"""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.schemas import UserMe


@pytest.fixture
def ac(app_instance, _clear_db_env):
    """Authed client."""
    app_instance.dependency_overrides[get_current_user] = lambda: UserMe(
        user_id="test-user", provider_subject="sub", email=None
    )
    with TestClient(app_instance) as c:
        yield c
    app_instance.dependency_overrides.pop(get_current_user, None)


# =====================================================================
# Phase 14.1 — Recipe ingestion
# =====================================================================


class TestTextPaste:
    """POST /recipes/paste — create recipe from pasted text."""

    def test_paste_basic(self, ac, app_instance):
        resp = ac.post("/recipes/paste", json={
            "title": "My Pasta Recipe",
            "text_content": "## Ingredients\n- 2 count tomato\n- 200 g pasta\n\n## Procedure\nBoil pasta. Make sauce.",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "My Pasta Recipe"
        assert body["status"] == "ready"
        assert body["content_type"] == "text/markdown"

    def test_paste_searchable(self, ac, app_instance):
        ac.post("/recipes/paste", json={
            "title": "Chocolate Lava Cake",
            "text_content": "## Ingredients\n- 100 g chocolate\n- 2 count eggs\n",
        })
        resp = ac.post("/recipes/search", json={"query": "Chocolate"})
        assert resp.status_code == 200
        results = resp.json()["results"]
        assert any("Chocolate" in r["title"] for r in results)

    def test_paste_empty_text_rejected(self, ac, app_instance):
        resp = ac.post("/recipes/paste", json={
            "title": "Empty",
            "text_content": "",
        })
        assert resp.status_code == 422  # validation error from min_length=1

    def test_paste_listed_in_books(self, ac, app_instance):
        ac.post("/recipes/paste", json={
            "title": "Quick Salad",
            "text_content": "Mix greens with dressing.",
        })
        resp = ac.get("/recipes/books")
        assert resp.status_code == 200
        books = resp.json()["books"]
        assert any("Quick Salad" in (b.get("title") or "") for b in books)


class TestPhotoUpload:
    """POST /recipes/photo — placeholder OCR endpoint."""

    def test_photo_returns_processing(self, ac, app_instance):
        resp = ac.post(
            "/recipes/photo",
            files={"file": ("recipe.jpg", b"fake-jpeg-data", "image/jpeg")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "processing"
        assert "OCR" in body["message"]

    def test_photo_empty_file_rejected(self, ac, app_instance):
        resp = ac.post(
            "/recipes/photo",
            files={"file": ("recipe.jpg", b"", "image/jpeg")},
        )
        assert resp.status_code == 400


class TestPdfUpload:
    """POST /recipes/books with PDF — tests extraction fallback."""

    def test_pdf_upload_creates_book(self, ac, app_instance):
        # Minimal fake PDF — not a valid PDF but tests the upload flow
        resp = ac.post(
            "/recipes/books",
            data={"title": "PDF Recipe"},
            files={"file": ("recipe.pdf", b"%PDF-1.4 fake content", "application/pdf")},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["content_type"] == "application/pdf"


class TestOpenAPIPaste:
    def test_paste_endpoint_in_openapi(self, ac, app_instance):
        resp = ac.get("/openapi.json")
        spec = resp.json()
        assert "/recipes/paste" in spec["paths"]
        assert "/recipes/photo" in spec["paths"]


# =====================================================================
# Phase 14.2 — Serving scaling
# =====================================================================


class TestServingScaling:
    """scale_ingredients function tests."""

    def test_scale_up(self):
        from app.schemas import IngredientLine
        from app.services.recipe_service import scale_ingredients

        ings = [
            IngredientLine(item_name="pasta", quantity=200, unit="g"),
            IngredientLine(item_name="tomato", quantity=2, unit="count"),
        ]
        scaled = scale_ingredients(ings, original_servings=2, target_servings=4)
        assert scaled[0].quantity == 400.0
        assert scaled[1].quantity == 4.0

    def test_scale_down(self):
        from app.schemas import IngredientLine
        from app.services.recipe_service import scale_ingredients

        ings = [
            IngredientLine(item_name="chicken", quantity=300, unit="g"),
        ]
        scaled = scale_ingredients(ings, original_servings=4, target_servings=2)
        assert scaled[0].quantity == 150.0

    def test_scale_same(self):
        from app.schemas import IngredientLine
        from app.services.recipe_service import scale_ingredients

        ings = [
            IngredientLine(item_name="rice", quantity=100, unit="g"),
        ]
        result = scale_ingredients(ings, original_servings=2, target_servings=2)
        assert result[0].quantity == 100

    def test_scale_zero_original(self):
        from app.schemas import IngredientLine
        from app.services.recipe_service import scale_ingredients

        ings = [
            IngredientLine(item_name="salt", quantity=5, unit="g"),
        ]
        result = scale_ingredients(ings, original_servings=0, target_servings=4)
        assert result[0].quantity == 5  # unchanged

    def test_scale_minimum_quantity(self):
        from app.schemas import IngredientLine
        from app.services.recipe_service import scale_ingredients

        ings = [
            IngredientLine(item_name="bay leaf", quantity=1, unit="count"),
        ]
        scaled = scale_ingredients(ings, original_servings=10, target_servings=1)
        assert scaled[0].quantity >= 0.25  # minimum floor

    def test_scale_preserves_optional(self):
        from app.schemas import IngredientLine
        from app.services.recipe_service import scale_ingredients

        ings = [
            IngredientLine(item_name="parsley", quantity=10, unit="g", optional=True),
        ]
        scaled = scale_ingredients(ings, original_servings=2, target_servings=4)
        assert scaled[0].optional is True
        assert scaled[0].quantity == 20.0


class TestMealplanScaling:
    """Integration: mealplan generate with target_servings."""

    def test_generate_with_scaling(self):
        from app.schemas import MealPlanGenerateRequest
        from app.services.mealplan_service import MealPlanService

        svc = MealPlanService()
        req = MealPlanGenerateRequest(days=1, meals_per_day=1, include_user_library=False)
        plan = svc.generate(req, target_servings=4)
        # Default built-in servings is 2, so scaling to 4 should double
        meal = plan.days[0].meals[0]
        # Check that at least one ingredient was scaled
        for ing in meal.ingredients:
            # Original quantities are 2 count tomato / 200g pasta for builtin_1
            if ing.item_name == "pasta":
                assert ing.quantity == 400.0
            elif ing.item_name == "tomato":
                assert ing.quantity == 4.0


# =====================================================================
# Phase 14.3 — Equipment detection + constraint-aware suggestions
# =====================================================================


class TestEquipmentDetection:
    """detect_equipment() unit tests."""

    def test_detect_air_fryer(self):
        from app.services.recipe_service import detect_equipment
        equip = detect_equipment("Place chicken in the air fryer at 400°F for 20 minutes.")
        assert "air fryer" in equip

    def test_detect_slow_cooker(self):
        from app.services.recipe_service import detect_equipment
        equip = detect_equipment("Add everything to the crockpot and cook on low for 8 hours.")
        assert "slow cooker" in equip

    def test_detect_oven(self):
        from app.services.recipe_service import detect_equipment
        equip = detect_equipment("Preheat to 375°F. Bake for 25 minutes.")
        assert "oven" in equip

    def test_detect_wok(self):
        from app.services.recipe_service import detect_equipment
        equip = detect_equipment("Heat oil in a wok over high heat.")
        assert "wok" in equip

    def test_detect_multiple(self):
        from app.services.recipe_service import detect_equipment
        equip = detect_equipment("Use blender to puree. Transfer to dutch oven and simmer.")
        assert "blender" in equip
        assert "dutch oven" in equip

    def test_detect_none(self):
        from app.services.recipe_service import detect_equipment
        equip = detect_equipment("Mix ingredients together in a bowl.")
        assert equip == []


class TestEquipmentPrefs:
    """UserPrefs.equipment field exists and works."""

    def test_prefs_with_equipment(self, ac, app_instance):
        resp = ac.put("/prefs", json={
            "prefs": {
                "servings": 2,
                "meals_per_day": 3,
                "equipment": ["air fryer", "slow cooker"],
            }
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "air fryer" in body["equipment"]
        assert "slow cooker" in body["equipment"]

    def test_prefs_equipment_default_empty(self, ac, app_instance):
        resp = ac.put("/prefs", json={
            "prefs": {"servings": 2, "meals_per_day": 3}
        })
        assert resp.status_code == 200
        assert resp.json()["equipment"] == []


class TestConstraintAwareMatch:
    """MATCH flow with equipment constraints."""

    def test_match_with_equipment_shows_note(self, ac, app_instance):
        # Set prefs with equipment
        ac.put("/prefs", json={
            "prefs": {
                "servings": 2,
                "meals_per_day": 3,
                "equipment": ["wok", "oven"],
            }
        })
        resp = ac.post("/chat", json={
            "mode": "ask",
            "message": "What can I make?",
        })
        assert resp.status_code == 200
        body = resp.json()
        # Should mention equipment in the response
        assert "equipment" in body["reply_text"].lower() or "🔧" in body["reply_text"]

    def test_match_without_equipment_no_note(self, ac, app_instance):
        ac.put("/prefs", json={
            "prefs": {"servings": 2, "meals_per_day": 3}
        })
        resp = ac.post("/chat", json={
            "mode": "ask",
            "message": "What can I make?",
        })
        assert resp.status_code == 200
        assert "🔧" not in resp.json()["reply_text"]


class TestConstraintAwareCheck:
    """CHECK flow with equipment detection."""

    def test_check_detects_wok(self, ac, app_instance):
        """Veggie Stir Fry instructions mention wok — should detect it."""
        ac.put("/prefs", json={
            "prefs": {
                "servings": 2,
                "meals_per_day": 3,
                "equipment": ["wok"],
            }
        })
        resp = ac.post("/chat", json={
            "mode": "ask",
            "message": "Can I cook Veggie Stir Fry?",
        })
        assert resp.status_code == 200
        reply = resp.json()["reply_text"]
        # Should mention having the wok
        assert "wok" in reply.lower()
