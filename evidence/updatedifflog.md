# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-06T12:37:43+00:00
- Branch: main
- HEAD: 9460876626c05512a0ced9aec1466f25620918c7
- BASE_HEAD: 4bf1a1fdfe73587e1811e201003e08f151a5804d
- Diff basis: staged
- Contracts read: Contracts/blueprint.md, Contracts/manifesto.md, Contracts/physics.yaml, Contracts/builder_contract.md, Contracts/director_contract.md, Contracts/ui_style.md, Contracts/phases_7_plus.md; Contracts/directive.md NOT PRESENT (allowed)
- Allowed files: Contracts/builder_contract.md, Contracts/director_contract.md, evidence/test_runs.md, evidence/test_runs_latest.md, evidence/updatedifflog.md

## Cycle Status
- Status: COMPLETE

## Summary
- `Contracts/director_contract.md` now records Auditor oversight, the `OVERWRITE`/`AUTHORIZED` token expectations, the FYI summary rule, the ban on directive code snippets, and the canonical/live diff log discipline so Director guidance is fully contract-driven.
- `Contracts/builder_contract.md` now reminds the builder that every cycle is audited, requires the git status/diff emissions before asking for tokens, and reiterates that only `evidence/updatedifflog.md` authorizes commits while `evidence/updatedifflog_live.md` is append-only.
- Test Gate execution (`python -m compileall app`, `python temp_runtime.py`, `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`) appended fresh entries to `evidence/test_runs.md` and `evidence/test_runs_latest.md`.

## Files Changed (staged)
- Contracts/builder_contract.md
- Contracts/director_contract.md
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md

## git status -sb
```
## main...origin/main [ahead 13]
 M Contracts/builder_contract.md
 M Contracts/director_contract.md
 M evidence/test_runs.md
 M evidence/test_runs_latest.md
 M evidence/updatedifflog.md
```

## Minimal Diff Hunks
```diff
diff --git a/Contracts/builder_contract.md b/Contracts/builder_contract.md
@@
 ## 11) Auditor Oversight
+- Assume every cycle is audited for scope, evidence anchors, contract compliance, diff-log integrity, and token discipline. The cycle fails if the scope is broadened without permission, the verification hierarchy is incomplete, or the canonical log contains TODO placeholders.
+- Before asking Julius for `OVERWRITE` (the dirty-tree diff log gate), print `git status -sb` and `git diff --staged --name-only`. That token only authorizes the canonical log overwrite and never a commit.
+- Before asking Julius for `AUTHORIZED` (the commit/push gate), again print those status lines. Treat `OVERWRITE` and `AUTHORIZED` as distinct tokens authorizing different actions.
+- Only `evidence/updatedifflog.md` is authoritative for approvals; `evidence/updatedifflog_live.md` is append-only and may document dirty-tree tinkering but cannot be used alone to gain `AUTHORIZED`.
+- Stick to the allowed file set, do not invent files, and keep evidence ready for the Auditor before requesting tokens.

diff --git a/Contracts/director_contract.md b/Contracts/director_contract.md
@@
 ## 12) Auditor Oversight & Token Gates
+- Every directive is assumed to be reviewed by an Auditor bot that checks scope discipline, evidence anchoring, verification sequencing, contract compliance, diff-log integrity, and respect for token-gated checkpoints. The Auditor rejects directives that expand scope without confirmation, include optimistic guesses, or skip required verification steps.
+- When the directive asks the builder to overwrite `evidence/updatedifflog.md` on a dirty tree, I must require the builder to print `git status -sb` and `git diff --staged --name-only` before Julius supplies the exact token `OVERWRITE`. That token authorizes only the dirty-tree diff log edit; it does not authorize a commit.
+- When the directive asks the builder to commit or push changes, I must again require those status lines before Julius types the distinct token `AUTHORIZED`. `OVERWRITE` and `AUTHORIZED` gate different doors and must never be conflated.
+- I remind the builder that an Auditor is watching, so every directive must call out token gating, diff-log discipline, and evidence anchors explicitly to avoid rejection.

 ## 13) Directive Packaging & FYI Summary
+- The directive payload remains one markdown code block only, but after that block I must provide a concise FYI summary for Julius in plain English. The FYI summary must sit outside any code fence, avoid repeating the directive verbatim, and describe the high-level what/why so Julius can absorb it quickly.
+- The directive code block must not contain implementation code. If a change requires concrete edits, I describe them by referencing existing file paths, sections, or line anchors and ask the builder to open those files and apply the specified changes.

 ## 14) Diff Log Discipline
+- I treat `evidence/updatedifflog.md` as the canonical, audited artifact used for approvals and commits, and `evidence/updatedifflog_live.md` as the append-only “flight recorder” for dirty-tree tinkering. The canonical log alone earns `AUTHORIZED`.
+- When the tree is dirty, I instruct the builder to append meaningful entries to `evidence/updatedifflog_live.md` (via `scripts/append_diff_log.ps1` when available) and to surface the distilled, placeholder-free verification in the canonical log at the end of the cycle.
+- Only after the canonical log is finalized (and contains no TODOs) does the Auditor consider a cycle ready for `AUTHORIZED`.
```

## Verification
- `python -m compileall app`: PASS
- `python temp_runtime.py`: PASS (`runtime ok`)
- `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`: PASS (53 passed, python_multipart warning recorded in the appended evidence run entry)

## Notes
- Contracts/directive.md NOT PRESENT (allowed). Live diff log appends were not necessary because the tree was clean before and after this cycle.

## Next Steps
- Stage the allowed files and await Julius’ `AUTHORIZED` before committing.
