# Phase 8: Inventory Agent Split (Fill-only, Isolation Enforcement)

## Status
- **State:** Planned (spec locked; ready to execute)
- **Primary goal:** Prevent flow bleed by isolating Inventory `/fill` behavior into a dedicated inventory-only pipeline (“Inventory Agent”).
- **Non-goal:** Adding new inventory features. Most parsing/normalization/confirm-write behavior already exists; this phase is about **hard routing boundaries** + **action allowlisting**.

---

## 1) Purpose

Phase 8 exists to stop “flow bleed” where inventory STT messages can trigger preference proposals because a shared chat pipeline is being used across flows.

This phase introduces a strict separation:
- Inventory updates (free-flow cupboard/fridge scan) are handled by an **Inventory Agent**.
- The Inventory Agent can **only** propose inventory actions and can **never** propose preferences or meal plan actions.

---

## 2) Scope Boundaries

### 2.1 Included in Phase 8
1. **Inventory mode is `/fill` only**
   - In inventory mode, user messages are treated as inventory updates (create/edit/delete within a proposal).
   - No inventory Q&A (“Do I have pasta?”) in Phase 8.

2. **Proposal → Confirm/Edit/Deny**
   - Inventory updates produce a proposal list.
   - User can Confirm, Edit, or Deny.
   - Confirm writes to DB; Edit changes pending proposal; Deny clears proposal.

3. **Thread-scoped proposals**
   - Inventory proposals are scoped to `thread_id`.
   - If user starts a new thread or closes/changes threads, a pending proposal may be lost. (This is acceptable for now and mirrors prefs behavior.)

4. **Confirm-before-write**
   - No database writes occur until the user confirms.
   - On confirm, the system writes inventory events to `inventory_events` (one event per item).

5. **Hard action allowlist**
   - Inventory flow must emit **only inventory actions**.
   - For Phase 8, the only allowed action type is:
     - `create_inventory_event`
   - Inventory Agent must never emit:
     - `upsert_prefs`
     - any preferences action
     - any meal plan action
     - any non-inventory action type

6. **Canonical entrypoint = long-press navigation**
   - Long-press menu is the primary navigation entry point for flows.
   - Inventory flow is entered via long-press (once unlocked by onboarding rules).

7. **Dedicated backend entrypoint**
   - Inventory flow is enforced via a dedicated endpoint:
     - `POST /chat/inventory`
   - This endpoint is used to hard-separate inventory routing from prefs routing.

---

### 2.2 Explicitly Excluded (Not Phase 8)
1. Inventory Q&A / `/ask` behavior (e.g., “what’s low stock?” / “do I have pasta?”).
2. Meal plan agent creation or meal plan flow isolation.
3. Location semantics (e.g., cupboard vs fridge as storage metadata).
4. New inventory schema fields unless strictly required to implement the agent boundary.
5. Direct DB editing of existing inventory outside the proposal lifecycle (future phase).
6. UI polish beyond what is strictly required for routing or proposal usage.

---

## 3) Canonical UX Contract (Inventory Fill)

### 3.1 Inventory `/fill` behavior is strict
When the user is in Inventory flow with `/fill` active:
- **Every message is treated as inventory update input**, not general conversation.
- The output must include:
  1. A structured proposal (normalized list of items)
  2. Clear instructions: Confirm / Edit / Deny
  3. Any warnings/ambiguities appended at the bottom

### 3.2 Edit semantics (pending proposal)
While an inventory proposal is pending:
- Any follow-up message is treated as an **edit instruction** applied to the pending proposal.
- Edits may include:
  - Rename items
  - Adjust quantity/unit
  - Adjust expiry date
  - Adjust notes
  - Delete items

### 3.3 Deny semantics
- Deny clears the pending inventory proposal.
- No DB write occurs.

### 3.4 Confirm semantics
- Confirm persists proposed inventory changes:
  - One DB event per item in `inventory_events`
- Confirm clears pending proposal afterward.

### 3.5 Ambiguity behavior
If parsing is ambiguous or missing detail:
- Still propose a best-effort normalized list.
- Append short “queries/warnings” at the bottom (examples):
  - “Pasta weight missing; assumed 500g.”
  - “Expiry date unclear; left blank.”
  - “Unit assumed grams.”

---

## 4) Architecture Decision: Isolation Strategy

### 4.1 Reason for split
The current shared pipeline can emit preference proposals inside inventory UI contexts. This is unacceptable for correctness and user trust.

### 4.2 Backend-first enforcement (required)
The backend is authoritative. Frontend-only routing is not sufficient to prevent bleed.

### 4.3 Dedicated endpoint (locked)
Phase 8 introduces:
- `POST /chat/inventory`

This endpoint is the inventory `/fill` entrypoint and guarantees:
- Inventory-only parsing/proposals/actions
- No prefs proposals possible through this path

This also establishes a pattern for later:
- `POST /chat/mealplan`

---

## 5) Inventory Agent Contract

### 5.1 Inventory Agent responsibilities
The Inventory Agent owns:
- Draft extraction (new draft)
- Edit operation extraction (edit instructions)
- Normalization of items
- Proposal creation and storage (thread-scoped)
- Rendering human-readable proposal reply text
- Producing proposed actions **only** of type `create_inventory_event`
- Confirm/Deny lifecycle tied to pending proposal

### 5.2 Inventory Agent forbidden behavior
The Inventory Agent must not:
- Propose preferences (no servings/days/likes/dislikes)
- Write or upsert prefs
- Emit non-inventory actions
- Emit meal plan actions
- Perform inventory Q&A in Phase 8

### 5.3 Proposal storage rule
- Proposals are keyed by `thread_id`.
- Proposal is ephemeral until confirmed.

---

## 6) Data + DB Contract

### 6.1 Persistence model
- Inventory updates are event-based.
- Table:
  - `inventory_events`

### 6.2 Write rule
- No writes until Confirm.
- Confirm creates:
  - One event per proposed item

### 6.3 Schema changes
- No schema changes required for Phase 8 unless a hard requirement is discovered during implementation.

---

## 7) Testing + Proof Contract (Acceptance Criteria)

Phase 8 is complete only when all of the following are true:

1. **Isolation proof**
   - Calling `/chat/inventory` never emits prefs proposals.
   - `/chat/inventory` never returns `upsert_prefs`.

2. **Action allowlist proof**
   - `/chat/inventory` responses contain only `create_inventory_event` in proposed actions.

3. **Confirm-before-write proof**
   - Proposal step does not write to DB.
   - Confirm writes inventory events.
   - Deny writes nothing.

4. **Thread-scoped proposal proof**
   - Pending proposal is tied to `thread_id`.
   - Confirm applies only the pending proposal for that thread.

5. **Regression safety**
   - Existing `/chat` prefs/onboarding behavior remains unchanged.

6. **Evidence + verification logs**
   - All verification outputs are recorded under evidence logs per governance.

---

## 8) Deferred Questions (Explicitly Not Solved Here)

These are intentionally postponed to avoid scope creep:
- Whether `location` should represent user context vs storage location
- Inventory `/ask` Q&A behavior and retrieval
- Editing existing inventory rows outside proposal cycle
- UI formatting changes for long inventory lists beyond what is required to function
- Meal plan flow isolation and MealPlan Agent

---

## 9) Implementation Notes (Non-prescriptive)
This Phase 8 plan is intentionally strict about outcomes, not implementation style. Implementation must preserve:
- Minimal diffs
- Backend-first enforcement
- Deterministic tests
- Confirm-before-write semantics
- Inventory-only action allowlist

---
