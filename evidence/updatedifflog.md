# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-03T13:08:06+00:00
- Branch: main
- HEAD: bbaa331a7a7e90e6b3f20d9017a47ac776b92b20
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Hotfixed recipes 404 responses to return top-level ErrorResponse (no detail wrapper).
- Added NotFoundError handler and registered globally.
- Updated recipes router to raise NotFoundError and extended tests to assert 404 shape.
- Test runner executed; logs appended/overwritten; all tests pass.

## Files Changed
- app/errors.py
- app/main.py
- app/api/routers/recipes.py
- tests/test_recipes_crud_and_search.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md

## git status -sb
    ## main...origin/main [ahead 10]
     M app/api/routers/recipes.py
     M app/errors.py
     M app/main.py
     M evidence/test_runs.md
     M evidence/test_runs_latest.md
     M evidence/updatedifflog.md
     M tests/test_recipes_crud_and_search.py

## Minimal Diff Hunks
    app/errors.py:
      + NotFoundError + not_found_handler -> ErrorResponse(error="not_found", message=...)
    app/main.py:
      + app.add_exception_handler(NotFoundError, not_found_handler)
    app/api/routers/recipes.py:
      + import NotFoundError; raise NotFoundError("book not found") instead of HTTPException detail wrapper
    tests/test_recipes_crud_and_search.py:
      + Assert 404 body has error/message (no detail) and add missing-id 404 test

## Verification
- python -m compileall app -> ok
- python -c "import app.main; print('import ok')" -> import ok
- python -c "from fastapi.testclient import TestClient; from app.main import app; c=TestClient(app); r=c.get('/health'); print(r.status_code, r.json())" -> 200 {'status': 'ok'}
- pwsh -File .\\scripts\\run_tests.ps1 -> PASS (pytest summary: 13 passed, 1 warning in 0.33s; test run logs updated)
- Contract: recipes 404 now uses top-level ErrorResponse (no detail); verified via updated tests.

## Notes (optional)
- None.

## Next Steps
- Proceed to Phase 5 directive.

