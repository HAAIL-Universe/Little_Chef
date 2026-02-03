# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-03T14:17:30+00:00
- Branch: main
- HEAD: 445a321446a20eaa259c20e1fda361341dc3b081
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added citations lists to PlannedMeal and ShoppingListItem responses to satisfy updated physics (min length 1, RecipeSource).
- Ensured shopping reasons are non-empty and deterministic.
- Updated schemas, services, and tests; test runner executed and logs updated.

## Files Changed (staged)
- app/schemas.py
- app/services/mealplan_service.py
- app/services/shopping_service.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- tests/test_mealplan_generate.py
- tests/test_shopping_diff.py

## git status -sb
    ## main...origin/main
    M  app/schemas.py
    M  app/services/mealplan_service.py
    M  app/services/shopping_service.py
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
    M  tests/test_mealplan_generate.py
    M  tests/test_shopping_diff.py

## Minimal Diff Hunks
    app/schemas.py:
      + citations: conlist(RecipeSource, min_length=1) on PlannedMeal
      + ShoppingListItem.reason now Field(..., min_length=1, default non-empty); added citations conlist min_length=1
    app/services/mealplan_service.py:
      + Construct RecipeSource per meal and set citations=[src]
    app/services/shopping_service.py:
      + Track ingredient citations and emit reason \"missing for meal plan\" with citations on every missing item
    tests/test_mealplan_generate.py:
      + Assert citations exist and include built_in recipe id
    tests/test_shopping_diff.py:
      + Plan fixtures include citations; missing items assert reason non-empty and citations present

## Verification
- Static: `python -m compileall app` -> ok
- Static: `python -c "import app.main; print('import ok')"` -> import ok
- Runtime: `python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); r=c.post('/mealplan/generate', json={'days':1,'meals_per_day':1}); print(r.status_code, r.json())"` -> 401 {'error': 'unauthorized', 'message': 'Missing Authorization header', 'details': None}
- Behavior: `pwsh -File .\\scripts\\run_tests.ps1` -> PASS (pytest 20 passed, 1 warning in 0.67s; logs updated)
- Contract: PlannedMeal and ShoppingListItem now include citations (>=1) and ShoppingListItem.reason non-empty; no endpoints changed.

## Notes (optional)
- None.

## Next Steps
- Update client/runtime as needed to supply citations when constructing shopping diffs from meal plans.
     
    diff --git a/tests/test_mealplan_generate.py b/tests/test_mealplan_generate.py
    index ba295de..a1b5cd9 100644
    --- a/tests/test_mealplan_generate.py
    +++ b/tests/test_mealplan_generate.py
    @@ -23,6 +23,12 @@ def test_mealplan_generate_happy_path(authed_client):
                 assert source["book_id"] is None
                 assert source["file_id"] is None
                 assert "excerpt" in source
    +            citations = meal.get("citations", [])
    +            assert isinstance(citations, list)
    +            assert len(citations) >= 1
    +            first = citations[0]
    +            assert first["source_type"] == "built_in"
    +            assert first["built_in_recipe_id"]
                 assert meal["ingredients"]
                 for ing in meal["ingredients"]:
                     assert ing["item_name"]
    diff --git a/tests/test_shopping_diff.py b/tests/test_shopping_diff.py
    index 73a434a..43163b5 100644
    --- a/tests/test_shopping_diff.py
    +++ b/tests/test_shopping_diff.py
    @@ -22,6 +22,15 @@ def _make_plan(ingredients):
                                 "book_id": None,
                                 "excerpt": None,
                             },
    +                        "citations": [
    +                            {
    +                                "source_type": "built_in",
    +                                "built_in_recipe_id": "builtin_1",
    +                                "file_id": None,
    +                                "book_id": None,
    +                                "excerpt": None,
    +                            }
    +                        ],
                         }
                     ],
                 }
    @@ -80,6 +89,9 @@ def test_shopping_diff_computes_missing_only(authed_client):
         assert missing["eggs"]["unit"] == "count"
         assert missing["milk"]["quantity"] == 300
         assert missing["milk"]["unit"] == "ml"
    +    for item in missing.values():
    +        assert item["reason"]
    +        assert item["citations"] and len(item["citations"]) >= 1
     
     
     def test_shopping_diff_works_with_generated_plan(authed_client):
    @@ -98,3 +110,6 @@ def test_shopping_diff_works_with_generated_plan(authed_client):
         missing = resp.json()["missing_items"]
         assert any(item["item_name"] == "tomato" for item in missing)  # still missing some tomatoes
         assert all("unit" in item for item in missing)
    +    for item in missing:
    +        assert item["reason"]
    +        assert item["citations"] and len(item["citations"]) >= 1

## Verification
- TODO: verification evidence (static -> runtime -> behavior -> contract).

## Notes (optional)
- TODO: blockers, risks, constraints.

## Next Steps
- TODO: next actions (small, specific).

