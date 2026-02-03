# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-03T13:44:07+00:00
- Branch: main
- HEAD: 9ab58ab18feeada6ea27bb40cadeb0c722f2ea83
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Implemented POST /mealplan/generate per physics with deterministic built-in meals, anchored recipe sources, and ingredients for shopping.
- Added meal plan schemas and in-memory MealPlanService; wired new router into app.
- Linked shopping diff to generated plans; added integration and auth tests.
- Hardened fixtures/reset hooks; updated test run history/latest snapshots.

## Files Changed (staged)
- app/api/routers/mealplan.py
- app/main.py
- app/schemas.py
- app/services/mealplan_service.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- tests/conftest.py
- tests/test_mealplan_generate.py
- tests/test_shopping_diff.py

## git status -sb
    ## main...origin/main
    A  app/api/routers/mealplan.py
    M  app/main.py
    M  app/schemas.py
    A  app/services/mealplan_service.py
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
     M evidence/updatedifflog.md
    M  tests/conftest.py
    A  tests/test_mealplan_generate.py
    M  tests/test_shopping_diff.py

## Minimal Diff Hunks
    diff --git a/app/api/routers/mealplan.py b/app/api/routers/mealplan.py
    new file mode 100644
    index 0000000..9784bc4
    --- /dev/null
    +++ b/app/api/routers/mealplan.py
    @@ -0,0 +1,17 @@
    +from fastapi import APIRouter, Depends
    +
    +from app.api.deps import get_current_user
    +from app.schemas import ErrorResponse, MealPlanGenerateRequest, MealPlanResponse, UserMe
    +from app.services.mealplan_service import get_mealplan_service
    +
    +router = APIRouter(prefix="", tags=["MealPlan"])
    +
    +
    +@router.post(
    +    "/mealplan/generate",
    +    response_model=MealPlanResponse,
    +    responses={"401": {"model": ErrorResponse}},
    +)
    +def generate_plan(request: MealPlanGenerateRequest, current_user: UserMe = Depends(get_current_user)) -> MealPlanResponse:
    +    service = get_mealplan_service()
    +    return service.generate(request)
    diff --git a/app/main.py b/app/main.py
    index 898920e..a32ff30 100644
    --- a/app/main.py
    +++ b/app/main.py
    @@ -1,6 +1,6 @@
     from fastapi import FastAPI
     
    -from app.api.routers import health, auth, prefs, chat, inventory, recipes, shopping
    +from app.api.routers import health, auth, prefs, chat, inventory, recipes, shopping, mealplan
     from app.errors import (
         UnauthorizedError,
         unauthorized_handler,
    @@ -20,6 +20,7 @@ def create_app() -> FastAPI:
         app.include_router(inventory.router)
         app.include_router(recipes.router)
         app.include_router(shopping.router)
    +    app.include_router(mealplan.router)
     
         app.add_exception_handler(UnauthorizedError, unauthorized_handler)
         app.add_exception_handler(BadRequestError, bad_request_handler)
    diff --git a/app/schemas.py b/app/schemas.py
    index db2f547..371708a 100644
    --- a/app/schemas.py
    +++ b/app/schemas.py
    @@ -184,6 +184,13 @@ class MealPlanResponse(BaseModel):
         notes: str = ""
     
     
    +class MealPlanGenerateRequest(BaseModel):
    +    days: int = Field(..., ge=1, le=31)
    +    meals_per_day: Optional[int] = Field(default=None, ge=1, le=6)
    +    include_user_library: bool = True
    +    notes: str = ""
    +
    +
     class ShoppingListItem(BaseModel):
         item_name: str
         quantity: float
    diff --git a/app/services/mealplan_service.py b/app/services/mealplan_service.py
    new file mode 100644
    index 0000000..f544bf7
    --- /dev/null
    +++ b/app/services/mealplan_service.py
    @@ -0,0 +1,78 @@
    +from functools import lru_cache
    +from uuid import uuid4
    +from datetime import datetime, timezone
    +from typing import List
    +
    +from app.schemas import (
    +    MealPlanGenerateRequest,
    +    MealPlanResponse,
    +    MealPlanDay,
    +    PlannedMeal,
    +    IngredientLine,
    +    RecipeSource,
    +)
    +from app.services.recipe_service import BUILT_IN_RECIPES
    +
    +
    +_INGREDIENTS_BY_RECIPE = {
    +    "builtin_1": [
    +        IngredientLine(item_name="tomato", quantity=2, unit="count", optional=False),
    +        IngredientLine(item_name="pasta", quantity=200, unit="g", optional=False),
    +    ],
    +    "builtin_2": [
    +        IngredientLine(item_name="chicken breast", quantity=300, unit="g", optional=False),
    +        IngredientLine(item_name="butter", quantity=20, unit="g", optional=False),
    +    ],
    +    "builtin_3": [
    +        IngredientLine(item_name="mixed veggies", quantity=250, unit="g", optional=False),
    +        IngredientLine(item_name="soy sauce", quantity=30, unit="ml", optional=False),
    +    ],
    +}
    +
    +
    +class MealPlanService:
    +    def generate(self, request: MealPlanGenerateRequest) -> MealPlanResponse:
    +        days = request.days
    +        meals_per_day = request.meals_per_day or 3
    +        created_at = datetime.now(timezone.utc).isoformat()
    +        plan_id = f"plan-{uuid4()}"
    +
    +        meals_catalog: List[dict] = BUILT_IN_RECIPES
    +        meals: List[MealPlanDay] = []
    +        for day_index in range(1, days + 1):
    +            day_meals: List[PlannedMeal] = []
    +            for meal_idx in range(meals_per_day):
    +                recipe = meals_catalog[meal_idx % len(meals_catalog)]
    +                recipe_id = recipe["id"]
    +                ingredients = _INGREDIENTS_BY_RECIPE.get(recipe_id, [])
    +                day_meals.append(
    +                    PlannedMeal(
    +                        name=recipe["title"],
    +                        slot=self._slot_for_index(meal_idx),
    +                        ingredients=ingredients,
    +                        instructions=[],
    +                        source=RecipeSource(
    +                            source_type="built_in",
    +                            built_in_recipe_id=recipe_id,
    +                            file_id=None,
    +                            book_id=None,
    +                            excerpt=None,
    +                        ),
    +                    )
    +                )
    +            meals.append(MealPlanDay(day_index=day_index, meals=day_meals))
    +
    +        return MealPlanResponse(plan_id=plan_id, created_at=created_at, days=meals, notes=request.notes or "")
    +
    +    def _slot_for_index(self, idx: int) -> str:
    +        order = ["breakfast", "lunch", "dinner", "supper", "snack"]
    +        return order[idx % len(order)]
    +
    +
    +@lru_cache(maxsize=1)
    +def get_mealplan_service() -> MealPlanService:
    +    return MealPlanService()
    +
    +
    +def reset_mealplan_service_cache() -> None:
    +    get_mealplan_service.cache_clear()
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index 5787e6a..6a59144 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -286,3 +286,73 @@ M  scripts/run_tests.ps1
      4 files changed, 84 insertions(+), 38 deletions(-)
     ```
     
    +## Test Run 2026-02-03T13:43:00Z
    +- Status: FAIL
    +- Start: 2026-02-03T13:43:00Z
    +- End: 2026-02-03T13:43:03Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 9ab58ab18feeada6ea27bb40cadeb0c722f2ea83
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 1
    +- pytest summary: 1 failed, 19 passed, 1 warning in 0.64s
    +- git status -sb:
    +```
    +## main...origin/main
    + M app/main.py
    + M app/schemas.py
    + M evidence/updatedifflog.md
    + M tests/conftest.py
    + M tests/test_shopping_diff.py
    +?? app/api/routers/mealplan.py
    +?? app/services/mealplan_service.py
    +?? tests/test_mealplan_generate.py
    +```
    +- git diff --stat:
    +```
    + app/main.py                 |   3 +-
    + app/schemas.py              |   7 +
    + evidence/updatedifflog.md   | 472 +++-----------------------------------------
    + tests/conftest.py           |   2 +
    + tests/test_shopping_diff.py |  18 ++
    + 5 files changed, 56 insertions(+), 446 deletions(-)
    +```
    +
    +## Test Run 2026-02-03T13:43:38Z
    +- Status: PASS
    +- Start: 2026-02-03T13:43:38Z
    +- End: 2026-02-03T13:43:41Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 9ab58ab18feeada6ea27bb40cadeb0c722f2ea83
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 20 passed, 1 warning in 0.51s
    +- git status -sb:
    +```
    +## main...origin/main
    + M app/main.py
    + M app/schemas.py
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
    + M evidence/updatedifflog.md
    + M tests/conftest.py
    + M tests/test_shopping_diff.py
    +?? app/api/routers/mealplan.py
    +?? app/services/mealplan_service.py
    +?? tests/test_mealplan_generate.py
    +```
    +- git diff --stat:
    +```
    + app/main.py                  |   3 +-
    + app/schemas.py               |   7 +
    + evidence/test_runs.md        |  33 +++
    + evidence/test_runs_latest.md |  34 ++--
    + evidence/updatedifflog.md    | 472 +++----------------------------------------
    + tests/conftest.py            |   2 +
    + tests/test_shopping_diff.py  |  18 ++
    + 7 files changed, 108 insertions(+), 461 deletions(-)
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index 309b597..93f44a2 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,31 +1,36 @@
     Status: PASS
    -Start: 2026-02-03T13:18:44Z
    -End: 2026-02-03T13:18:47Z
    +Start: 2026-02-03T13:43:38Z
    +End: 2026-02-03T13:43:41Z
     Branch: main
    -HEAD: d43185a8200d6f3c1338c57defbc21859dcda14f
    +HEAD: 9ab58ab18feeada6ea27bb40cadeb0c722f2ea83
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 17 passed, 1 warning in 0.43s
    +pytest summary: 20 passed, 1 warning in 0.51s
     git status -sb:
     ```
     ## main...origin/main
      M app/main.py
      M app/schemas.py
    + M evidence/test_runs.md
    + M evidence/test_runs_latest.md
      M evidence/updatedifflog.md
      M tests/conftest.py
    -?? app/api/routers/shopping.py
    -?? app/services/shopping_service.py
    -?? tests/test_recipes_search_anchors.py
    -?? tests/test_shopping_diff.py
    + M tests/test_shopping_diff.py
    +?? app/api/routers/mealplan.py
    +?? app/services/mealplan_service.py
    +?? tests/test_mealplan_generate.py
     ```
     git diff --stat:
     ```
    - app/main.py               |  3 ++-
    - app/schemas.py            | 53 +++++++++++++++++++++++++++++++++++++++
    - evidence/updatedifflog.md | 64 ++++++++++++++++++++---------------------------
    - tests/conftest.py         |  2 ++
    - 4 files changed, 84 insertions(+), 38 deletions(-)
    + app/main.py                  |   3 +-
    + app/schemas.py               |   7 +
    + evidence/test_runs.md        |  33 +++
    + evidence/test_runs_latest.md |  34 ++--
    + evidence/updatedifflog.md    | 472 +++----------------------------------------
    + tests/conftest.py            |   2 +
    + tests/test_shopping_diff.py  |  18 ++
    + 7 files changed, 108 insertions(+), 461 deletions(-)
     ```
     
    diff --git a/tests/conftest.py b/tests/conftest.py
    index c2e2f6a..b641115 100644
    --- a/tests/conftest.py
    +++ b/tests/conftest.py
    @@ -11,6 +11,7 @@ from app.services.inventory_service import get_inventory_service
     import app.api.routers.recipes as recipes_router
     from app.services.recipe_service import get_recipe_service, reset_recipe_service_cache
     from app.services.shopping_service import reset_shopping_service_cache
    +from app.services.mealplan_service import reset_mealplan_service_cache
     
     
     @pytest.fixture
    @@ -20,6 +21,7 @@ def app_instance():
         get_inventory_service.cache_clear()
         reset_recipe_service_cache()
         reset_shopping_service_cache()
    +    reset_mealplan_service_cache()
         chat_router._proposal_store.clear()
         chat_router._chat_service = ChatService(get_prefs_service(), get_inventory_service(), chat_router._proposal_store)
         recipes_router.reset_recipes_for_tests()
    diff --git a/tests/test_mealplan_generate.py b/tests/test_mealplan_generate.py
    new file mode 100644
    index 0000000..ba295de
    --- /dev/null
    +++ b/tests/test_mealplan_generate.py
    @@ -0,0 +1,30 @@
    +def test_mealplan_generate_requires_auth(client):
    +    resp = client.post("/mealplan/generate", json={"days": 1, "meals_per_day": 2})
    +    assert resp.status_code == 401
    +    body = resp.json()
    +    assert body["error"] == "unauthorized"
    +    assert "detail" not in body
    +
    +
    +def test_mealplan_generate_happy_path(authed_client):
    +    resp = authed_client.post("/mealplan/generate", json={"days": 2, "meals_per_day": 2})
    +    assert resp.status_code == 200
    +    plan = resp.json()
    +    assert plan["plan_id"]
    +    assert plan["created_at"]
    +    assert len(plan["days"]) == 2
    +    for day in plan["days"]:
    +        assert "day_index" in day
    +        assert len(day["meals"]) == 2
    +        for meal in day["meals"]:
    +            source = meal["source"]
    +            assert source["source_type"] == "built_in"
    +            assert source["built_in_recipe_id"]
    +            assert source["book_id"] is None
    +            assert source["file_id"] is None
    +            assert "excerpt" in source
    +            assert meal["ingredients"]
    +            for ing in meal["ingredients"]:
    +                assert ing["item_name"]
    +                assert ing["quantity"] >= 0
    +                assert ing["unit"] in ("g", "ml", "count")
    diff --git a/tests/test_shopping_diff.py b/tests/test_shopping_diff.py
    index 4380d28..73a434a 100644
    --- a/tests/test_shopping_diff.py
    +++ b/tests/test_shopping_diff.py
    @@ -80,3 +80,21 @@ def test_shopping_diff_computes_missing_only(authed_client):
         assert missing["eggs"]["unit"] == "count"
         assert missing["milk"]["quantity"] == 300
         assert missing["milk"]["unit"] == "ml"
    +
    +
    +def test_shopping_diff_works_with_generated_plan(authed_client):
    +    resp = authed_client.post("/mealplan/generate", json={"days": 1, "meals_per_day": 2})
    +    assert resp.status_code == 200
    +    plan = resp.json()
    +
    +    # Seed inventory with some items from built-in ingredients
    +    authed_client.post(
    +        "/inventory/events",
    +        json={"event_type": "add", "item_name": "tomato", "quantity": 1, "unit": "count", "note": "", "source": "ui"},
    +    )
    +
    +    resp = authed_client.post("/shopping/diff", json={"plan": plan})
    +    assert resp.status_code == 200
    +    missing = resp.json()["missing_items"]
    +    assert any(item["item_name"] == "tomato" for item in missing)  # still missing some tomatoes
    +    assert all("unit" in item for item in missing)

## Verification
- Static: `python -m compileall app` -> ok
- Static: `python -c "import app.main; print('import ok')"` -> import ok
- Runtime: `python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); print(c.get('/health').status_code, c.get('/health').json()); r=c.post('/mealplan/generate', json={'days':1,'meals_per_day':1}); print(r.status_code, r.json())"` -> 200 {'status': 'ok'}; 401 unauthorized (top-level ErrorResponse)
- Behavior: `pwsh -File .\\scripts\\run_tests.ps1` -> PASS (pytest 20 passed, 1 warning in 0.51s; logs updated)
- Contract: /mealplan/generate matches physics MealPlanGenerateRequest/Response; recipe sources set with built_in_recipe_id and no user_library anchors; shopping diff continues to accept MealPlanResponse and returns ShoppingDiffResponse; 401 responses use top-level ErrorResponse.

## Notes (optional)
- None.

## Next Steps
- Await Phase 7 directives (likely meal plan refinement/citations).

