# Blueprint + Manifesto Audit (Phase 6 closure sanity)

Snapshot
- Branch/HEAD: main @ eb4561aaeb1c42531e1935d49538e2737461557c (clean)
- Contracts read: builder_contract.md, blueprint.md, manifesto.md, ui_style.md, Contracts/physics.yaml, phases_0-6.md, phases_6a_6c_extension.md
- Last cycle (per updatedifflog): hardened smoke.ps1, added token-leak guard test, prod smoke (no token) 200/200/200/401.

Blueprint acceptance checklist (v0.1)
- OAuth login (bearer JWT), onboarding, prefs reflected in UI → PARTIAL (auth + prefs wired; UI auth strip/prefs panel present; full onboarding flow not evidenced) — app/api/routers/auth.py:9-65; app/api/routers/prefs.py:8-41; web/src/main.ts.
- Add inventory via chat and see totals → PARTIAL (chat + inventory endpoints exist; needs E2E proof) — app/api/routers/chat.py:18-58; app/api/routers/inventory.py:15-70.
- Log consumption types (cooked/used separately/thrown away) → PARTIAL (event types covered in inventory router/service; no recent E2E evidence) — app/api/routers/inventory.py:33-70.
- Low-stock sensible results → UNKNOWN (endpoint present; no evidence of correctness) — app/api/routers/inventory.py:62-70.
- Generate 7-day plan + structured plan output + shopping diff (missing only) → PARTIAL (endpoints implemented; UI renders minimal plan/diff) — app/api/routers/mealplan.py:7-17; app/api/routers/shopping.py:7-17; web/src/main.ts.
- Recipe library upload works end-to-end for a PDF and retrieval is used → UNKNOWN (upload/search endpoints exist; no recent upload/retrieval evidence) — app/api/routers/recipes.py:15-95.
- No “user library” recipe without citation → UNKNOWN (physics enforces citations; enforcement not recently evidenced) — Contracts/physics.yaml mealplan/shopping schemas; mealplan/shopping services implied.
- Routers remain thin (no domain logic/SQL/LLM) → PASS — routers delegate to services/repos; see app/api/routers/*.py vs services/repos.

Manifesto non-negotiables
- Chat-first control (edits via chat) → PASS (chat router/service primary; UI chat surface: web/src/main.ts; chat endpoints: app/api/routers/chat.py).
- Contract/physics-first truth → PASS (physics.yaml defines all routes; no extra routes observed; app/main.py includes only physics-defined routers).
- Boundary hygiene (routers thin, no SQL/LLM in routers) → PASS (routers only parse/call services; e.g., app/api/routers/inventory.py, auth.py).
- Confirm-before-write behavior → PARTIAL (chat propose/confirm endpoints implemented; UX minimal) — app/api/routers/chat.py:18-58; web/src/main.ts confirmation handling.
- Anti-hallucination/citations → UNKNOWN (schemas require citations; runtime enforcement not evidenced) — Contracts/physics.yaml (PlannedMeal.citations, ShoppingListItem.citations).

Physics vs routes sanity
- All physics paths served: `/`, `/static/{path}`, `/health`, `/auth/me`, `/chat`, `/chat/confirm`, `/prefs`, `/inventory/events`, `/inventory/summary`, `/inventory/low-stock`, `/recipes/books`, `/recipes/books/{book_id}`, `/recipes/search`, `/mealplan/generate`, `/shopping/diff`, `/docs`, `/openapi.json` — anchors: app/main.py:16-50; app/api/routers/*.py as listed above.
- No extra public API routes beyond physics observed. → PASS.

Closure statement
- Are Blueprint + Manifesto effectively satisfied besides UI polish? → NO.
- Reasons/gaps:
  1) Onboarding/prefs and chat confirm UX need user-facing proof/polish (UI_POLISH_ONLY/NEEDS_MANUAL_VERIFICATION).
  2) Inventory add/consumption/low-stock behaviors lack recent end-to-end evidence (NEEDS_MANUAL_VERIFICATION).
  3) Recipe upload + retrieval with citations not recently evidenced (NEEDS_MANUAL_VERIFICATION).
  4) Citations anti-hallucination enforcement not proven (NEEDS_MANUAL_VERIFICATION).

Recommended next milestone
- Run focused E2E validation: upload a recipe PDF, generate meal plan/shopping diff citing user library, and exercise chat propose/confirm + inventory add/consume + low-stock, capturing outputs/screenshots to close remaining PASS/UNKNOWN items; then polish chat confirm UI (Phase 6A). 
