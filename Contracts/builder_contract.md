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
5) `build_docs/evidence/updatedifflog.md` or `updatedifflog.md` (if present)

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

For changes to prefs/inventory:
- Chat flow must propose structured action(s), then require confirmation, then execute write.

If implementation mutates user data without confirmation, STOP with: `CONTRACT_CONFLICT`.

---

## 7) Anti-hallucination rule for recipes

If a recipe is sourced from user-uploaded books:
- response MUST include a citation (`RecipeCitation`)
- if retrieval fails, assistant must not invent a recipe

If a plan includes “user library” recipe content without citation, STOP with: `CONTRACT_CONFLICT`.

### 7.1 Prefer proven components over custom builds

When a reliable, maintained component exists (auth, storage, ingestion, UI widgets, SDK helpers), prefer using it over building from scratch.

- New dependencies must be explicitly approved in the directive (include rationale + alternatives considered).
- Do not introduce heavyweight frameworks or sweeping architecture changes without explicit instruction.

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

---

## 10) Diff log gate (mandatory if diff log exists)

If `updatedifflog.md` exists (or `build_docs/evidence/updatedifflog.md`), the builder must:

1) Read it at the start and summarize last change
2) Overwrite it at the end with:
   - summary of this cycle
   - files changed
   - minimal diff hunks
   - verification evidence
   - next steps

If the repo has a PowerShell helper for diff logs, it must be used.

If diff log is not updated, work is incomplete.

--- End of Builder Contract ---
