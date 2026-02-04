# Little Chef — Builder Contract (v0.1)

This contract governs any automated builder (Copilot/Codex/Claude/etc.) touching this repo.

It exists to prevent:
- godfiles
- drift
- duplicated features
- unverifiable changes
- regressions from “helpful refactors”

---

## 1) Contract read gate (mandatory)

Before making changes, the builder must read (in this order):

1) `Contracts/blueprint.md`
2) `Contracts/manifesto.md`
3) `Contracts/physics.yaml`
4) `Contracts/directive.md` (when it exists)
5) `evidence/updatedifflog.md` (canonical)  
   - Legacy fallback may exist: `build_docs/evidence/updatedifflog.md`

If any file is missing or not found, STOP with: `EVIDENCE_MISSING`.

---

## 2) Evidence bundle (mandatory)

Every change request must include:

- repo tree (or confirm file paths exist)
- files to be edited (exact paths)
- current behavior + expected behavior
- logs/errors (if runtime issue)
- minimal diff plan
- verification steps + results

If evidence is insufficient, STOP with: `EVIDENCE_MISSING`.

---

## 3) Minimal-diff rule (default)

- Change as little as possible.
- No renames.
- No “cleanup”.
- No refactors unless explicitly requested.

If the builder’s proposed change touches unrelated files, STOP with: `CONTRACT_CONFLICT`.

---

## 4) File boundary enforcement (anti-godfile)

**Routers are HTTP-only.**
Routers may:
- parse request
- call service
- return response

Routers may NOT:
- contain SQL
- contain domain logic
- call OpenAI
- contain retrieval/vector logic

Services own orchestration + business logic.

Repos own DB reads/writes.

LLM wrapper owns OpenAI calls.

If any boundary is violated, STOP with: `CONTRACT_CONFLICT`.

---

## 5) Physics compliance

### 5.1 Physics-first gate (new/unallocated features)

If a requested change introduces a feature that does not have a dedicated place in `Contracts/physics.yaml` (new endpoint, new request/response field, new component capability), the builder MUST stop and ask for a contracts update first.

- STOP with: `EVIDENCE_MISSING`
- Report what is missing (which endpoint/schema/component needs to be added to physics)
- Propose a minimal contract diff (physics + any blueprint/manifesto touchpoints) before writing code

This prevents duplicated features and “AI amnesia” across sessions.

- `Contracts/physics.yaml` is canonical.
- Routes must match `physics.yaml` paths, methods, and response shapes.
- Pydantic models must align with `physics.yaml` schemas.

If code and physics diverge, STOP with: `CONTRACT_CONFLICT`.

---

## 6) Confirm-before-write rule (v0.1 default)

For changes to prefs/inventory (and any state mutation):
- Chat flow must propose structured action(s), then require confirmation, then execute write.
- Exactly one active proposal per thread; a new proposal supersedes the prior active proposal.
- Decline is non-destructive: declined proposals are not applied and remain recoverable/editable within the same thread; starting a new clean thread makes prior thread proposals inaccessible via UI (even if retained for audit).
- Thread identity (`thread_id`) scopes conversation + proposals; UI/clients should persist/pass it when continuing a thread. Do NOT add `/threads/*` endpoints unless physics is updated first.

If implementation mutates user data without confirmation, STOP with: `CONTRACT_CONFLICT`.

---

## 7) Anti-hallucination rule for recipes

If a recipe is sourced from user-uploaded books:
- response MUST include a citation/anchor (per `RecipeSearchResult` / `RecipeSource` fields in physics)
- if retrieval fails, assistant must not invent a recipe

If a plan includes “user library” recipe content without citation/anchor, STOP with: `CONTRACT_CONFLICT`.

### 7.1 Prefer proven components over custom builds

When a reliable, maintained component exists (auth, storage, ingestion, UI widgets, SDK helpers), prefer using it over building from scratch.

- New dependencies must be explicitly approved in the directive (include rationale + alternatives considered).
- Do not introduce heavyweight frameworks or sweeping architecture changes without explicit instruction.

### 7.2 Voice-first, text-native API (v0.1)
- Voice input is allowed but must be transcribed client-side; backend receives text via `/chat` only.
- Do NOT add audio upload/transcribe routes unless physics is updated first.
- Do NOT place OpenAI or other model keys in the browser; all model/tool calls remain server-side.

### 7.3 Background work (allowed, never silent writes)
- Background agents/jobs may parse stored messages and pre-fill flow state.
- Background work may produce proposals or read-only derived state; it must not apply writes without explicit confirmation.

### 7.4 OpenAI integration guidance (implementation-level)
- Use server-side OpenAI calls (e.g., Responses API) only; keep model selection configurable via env/config (chat vs transcription vs embeddings independently configurable).
- Never log or return secrets; keep keys in server env only.

---

## 8) Typed STOP reasons (use exactly one)

- `EVIDENCE_MISSING` — missing repo tree, missing file, missing logs, missing contract update, missing acceptance criteria
- `AMBIGUOUS_INTENT` — unclear expected behavior
- `CONTRACT_CONFLICT` — violates manifesto/blueprint/physics rules
- `RISK_EXCEEDS_SCOPE` — high risk, large refactor implied
- `NON_DETERMINISTIC_BEHAVIOR` — cannot reproduce or verify
- `ENVIRONMENT_LIMITATION` — blocked by runtime/tooling constraints

---

## 9) Verification hierarchy (must be reported in order)

1) Static correctness
   - type check / lint (if configured)
   - import sanity
2) Runtime sanity
   - app boots
   - core endpoints respond
3) Behavioral intent
   - target scenario is fixed
4) Contract compliance
   - physics matches
   - file boundaries preserved

### 9.1 Test Gate (mandatory)

- Create/maintain a `tests/` folder at repo root (pytest).
- At the end of each phase (or any “feature complete” checkpoint):
  1) Add or update unit tests covering the new behavior.
  2) Run tests as part of verification: **static → runtime → behavior (pytest) → contract**.
- Tests must be deterministic:
  - Do not depend on live OAuth/JWKS/OIDC network calls.
  - Use dependency overrides / fakes for auth verification in tests.
- A phase must not be marked COMPLETE until relevant tests pass.

### 9.2 Test Runner Script Gate (mandatory)

- Create/maintain a PowerShell test runner at: `scripts/run_tests.ps1`.
- The test runner must be updated whenever new tests are added or existing test layout changes.
- The test runner must run the full deterministic suite used for “bulk” verification.
- Each invocation of `scripts/run_tests.ps1` must append a timestamped entry to `evidence/test_runs.md` capturing start/end time (UTC), python path, branch/HEAD (or “git unavailable”), git status/diff stat, and exit codes/summaries for compileall, import sanity, and pytest. The log MUST append (never overwrite) even when a step fails.
- At the end of every implementation cycle marked COMPLETE, the builder MUST run `.\scripts\run_tests.ps1` and include results in verification.
- `scripts/run_tests.ps1` must also overwrite `evidence/test_runs_latest.md` on every run; the first line must be `Status: PASS|FAIL` and, if failing, include a brief failing-tests section (or note to see console output).

Minimum required behavior for `scripts/run_tests.ps1`:
- Run static sanity for the backend (compile/import)
- Run pytest (quiet) for the full suite
- Return a non-zero exit code if any step fails

The builder must:
- Add/update `scripts/run_tests.ps1` in the same cycle as adding tests (or STOP with `CONTRACT_CONFLICT` if tests were added without updating the runner).
- Include the exact commands + outputs in the diff log verification section.

### 9.3 Drift guardrails (UI/TS + evidence discipline)
- UI work must remain TypeScript-only (no new `.js` sources); mobile-first per `Contracts/ui_style.md`.
- Physics-first: no new routes without updating `Contracts/physics.yaml` first.
- Minimal diffs per cycle; no refactors unless the contract forces it.
- Every cycle overwrites `evidence/updatedifflog.md` with verification: static → runtime → behavior → contract.

---

## 10) Diff log gate (mandatory)

Canonical diff log path: `evidence/updatedifflog.md`  
Legacy fallback may exist: `build_docs/evidence/updatedifflog.md`

The builder must:

1) Read the canonical diff log at the start (if present) and summarize last change.
2) Overwrite the canonical diff log at the end with:
   - summary of this cycle
   - files changed
   - minimal diff hunks
   - verification evidence
   - next steps

If the repo has a PowerShell helper for diff logs, it must be used:
- `scripts/overwrite_diff_log.ps1`

Helper workflow: the script writes skeleton + git/diff metadata but leaves TODO placeholders. The builder must:
1) At START of a cycle: run the helper, then replace TODO placeholders with Status=IN_PROCESS, planned/current files, summary bullets, and notes/next steps (no TODOs left).
2) At END of a cycle: re-run the helper to refresh metadata, then replace all TODO placeholders with final Status=COMPLETE, real summary, verification (static → runtime → behavior → contract), and notes/next steps (explicit “None” if empty).
No cycle is COMPLETE if any “TODO:” placeholders remain in `evidence/updatedifflog.md`.

Mandatory per-cycle diff log sequence:
1) Read `evidence/updatedifflog.md` and summarize the previous cycle (1–5 bullets) before any overwrite/tool call.
2) Plan scope/files/tests.
3) Only after planning, run `scripts/overwrite_diff_log.ps1` to regenerate the scaffold.
4) Immediately replace placeholders with Status=IN_PROCESS, planned summary, planned files (mark as planned if unstaged), notes, and next steps (no TODOs left).
5) Do the work.
6) End-of-cycle: re-run the helper, then manually finalize Status=COMPLETE, Summary, Verification (static → runtime → behavior → contract), Notes, and Next Steps.
7) After manual edits, run `pwsh -File .\scripts\overwrite_diff_log.ps1 -Finalize`; if it reports TODO placeholders or missing log, treat as CONTRACT_CONFLICT and stop.

Non-negotiable rule:
- Overwriting before summarizing the prior cycle or leaving TODO placeholders is a CONTRACT_CONFLICT (work incomplete).

Rules:
- Do not write or re-introduce a root-level `updatedifflog.md`.
- If the helper script or canonical evidence path cannot be used, STOP with: `ENVIRONMENT_LIMITATION` (include exact error).

If diff log is not updated, work is incomplete.

--- End of Builder Contract ---
