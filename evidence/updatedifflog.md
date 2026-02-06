# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-06T13:44:34+00:00
- Branch: main
- HEAD: c64a9f90fb98770b445a2c8f26f1d76eb059a7a5
- BASE_HEAD: 9460876626c05512a0ced9aec1466f25620918c7
- Diff basis: staged
- Contracts read: Contracts/builder_contract.md, Contracts/blueprint.md, Contracts/manifesto.md, Contracts/physics.yaml, Contracts/ui_style.md, Contracts/phases_7_plus.md; Contracts/directive.md NOT PRESENT (allowed)
- Allowed files: app/services/chat_service.py, tests/test_chat_prefs_propose_confirm.py, evidence/test_runs.md, evidence/test_runs_latest.md, evidence/updatedifflog.md

## Cycle Status
- Status: COMPLETE_AWAITING_AUTHORIZATION
- Classification: EVIDENCE + FIX

## Summary
- Parsed likes/dislikes/cuisine likes via clause-aware regex helpers so fill-mode text is broken into clean lists instead of relying on naive keyword splits.
- Added clause splitting, clause deduplication, and allergy normalization helpers that lower-case prefixes before trimming, which keeps items like "peanuts" and "shellfish" intact.
- Expanded the prefs regression test so the reported paragraph now verifies servings=2, the captured allergy list, dislikes covering mushrooms/olives/blue cheese/"really sweet sauces", and cuisine likes such as chicken/salmon/rice/pasta.

## Evidence
- POST `/chat` (mode: fill) with the paragraph "Okay, so for allergies: I'm allergic to peanuts..." produces `reply_text = "Proposed preferences: servings 2, meals/day 2. Reply CONFIRM to save or continue editing."`, `confirmation_required = true`, and `proposed_actions[0].prefs` containing `servings: 2`, `allergies: ["peanuts", "shellfish"]`, `dislikes` that include mushrooms/olives/blue cheese/"really sweet sauces", and `cuisine_likes` covering chicken/salmon/rice/pasta/potatoes/tomatoes/spinach/peppers/cheese/anything spicy`.

## Root Cause
- `_extract_allergy_items` + `_normalize_allergy_item` (app/services/chat_service.py:503-518) now lower-case prefixes before trimming so "allergies: I'm allergic to" doesn’t leave fragments like "ies:.".
- `_parse_prefs_from_message` (app/services/chat_service.py:520-537) now leverages clause helpers and deduplication to surface likes/dislikes/cuisine_likes lists reliably instead of splitting on the first keyword instance.

## Files Changed (staged)
- app/services/chat_service.py
- tests/test_chat_prefs_propose_confirm.py
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md

## git status -sb
    ## main...origin/main [ahead 14]
    MM app/services/chat_service.py
    MM evidence/test_runs.md
    MM evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
    M  tests/test_chat_prefs_propose_confirm.py

## Minimal Diff Hunks
```diff
@@
-        def extract_list(keyword: str) -> List[str]:
-            if keyword not in message:
-                return []
-            after = message.split(keyword, 1)[1]
-            parts = re.split(r"[,.]", after)
-            return [p.strip() for p in parts[0].split(" and ") if p.strip()]
-
-        allergies = extract_list("allerg")
-        dislikes = extract_list("dislike")
-        cuisine_likes = extract_list("cuisine")
+        allergies = self._extract_allergy_items(lowered_message)
+        dislikes = self._extract_clause_items(lowered_message, DISLIKE_CLAUSE_PATTERNS)
+        likes = self._extract_clause_items(lowered_message, LIKE_CLAUSE_PATTERNS)
+        cuisine_entries = self._extract_clause_items(lowered_message, CUISINE_CLAUSE_PATTERNS)
+        cuisine_likes = self._dedupe_items(likes + cuisine_entries)
@@
-        return UserPrefs(
-            allergies=allergies,
-            dislikes=dislikes,
-            cuisine_likes=cuisine_likes,
-            servings=servings or 0,
-            meals_per_day=meals_per_day or 0,
-            notes="",
-        )
+        return UserPrefs(
+            allergies=allergies,
+            dislikes=dislikes,
+            cuisine_likes=cuisine_likes,
+            servings=servings or 0,
+            meals_per_day=meals_per_day or 0,
+            notes="",
+        )
```
```diff
@@
-    assert action["prefs"]["servings"] == 2
+    assert action["prefs"]["servings"] == 2
+    prefs = action["prefs"]
+    assert set(prefs["allergies"]) == {"peanuts", "shellfish"}
+    assert set(prefs["dislikes"]) >= {"mushrooms", "olives", "blue cheese", "really sweet sauces"}
+    assert set(prefs["cuisine_likes"]) >= {"chicken", "salmon", "rice", "pasta", "potatoes", "tomatoes", "spinach", "peppers", "cheese", "anything spicy"}
```

## Verification
- `python -m compileall app`: PASS
- `python -c "import app.main; print('import ok')"`: PASS
- `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`: PASS (54 passed, 1 warning recorded in `evidence/test_runs.md`/`evidence/test_runs_latest.md`)
- Contract: `Contracts/physics.yaml` unchanged and was not modified this cycle.

## Notes (optional)
- `Contracts/directive.md` NOT PRESENT (allowed).

## Next Steps
- Await `AUTHORIZED` before committing.
