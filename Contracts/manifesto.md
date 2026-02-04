# Little Chef — Manifesto (v0.1)

This document defines the non-negotiable principles for building Little Chef.
If implementation conflicts with this manifesto, implementation is wrong.

---

## 1) Product principle: chat-first, data-backed

Little Chef is a chat-first assistant that controls structured data.

- Chat is the primary control surface.
- Dashboards/forms are display surfaces of the current truth.
- Users can view data in UI, but edits happen via chat (by default in v0.1).

---

## 2) Contract-first, schema-first

Little Chef is built from contracts, not vibes.

- `physics.yaml` is the API “physics law” (OpenAPI format) and is canonical.
- Pydantic schemas mirror the physics spec.
- If it’s not in `physics.yaml`, it isn’t real.

---

## 3) No godfiles, no blurred boundaries

Everything has a lane.

- **Routers are HTTP-only** (parse → call service → return).
- **Services own domain rules** (inventory math, planning logic, diffs).
- **Repos own persistence** (SQL only).
- **LLM wrapper owns model/tool calls** (one integration point).
- No layer is allowed to do another layer’s job.

Violations are bugs, even if the feature works.

---

## 4) Auditability over cleverness

We value “debuggable and correct” over “magic and fast.”

- Inventory is event-based and explainable.
- All writes require correlation IDs and idempotency keys.
- A senior dev should be able to answer: “Why did this number change?”

---

## 5) Reliability over hallucination

The system must be honest about sources.

- Built-in recipes are deterministic and versioned.
- User-uploaded recipes are retrieved via vector search and MUST have citations.
- Little Chef must not claim a recipe comes from uploads without a retrieval anchor.

When retrieval yields nothing:
- ask a clarifying question, or
- fall back to built-ins (clearly labeled)

Voice-first, text-native API:
- Clients may capture audio but must send text to /chat (client-side transcription in v0.1).
- No audio upload routes in v0.1; no client-side model calls; server owns model/tool calls.

Background work is allowed (parsing, normalization, pre-fill), but it must only produce proposals or read-only derived state—never commit writes without confirmation.

Message storage:
- Raw user/assistant messages may be stored for thread context, auditability, and background parsing.
- Any derived updates must still flow through proposal → confirm/decline.

---

## 6) Confirm-before-write (v0.1 default)

Little Chef should not mutate user data based on ambiguous chat.

Default flow for writes:
1) propose a structured change (exactly one active proposal per thread; a new proposal supersedes the previous active one)
2) user confirms or declines
3) execute write only when confirmed

Decline is non-destructive: declined proposals are not applied and remain recoverable/editable within the same thread. Starting a new clean thread makes prior thread proposals inaccessible via UI (even if retained for audit).
Thread identity (thread_id) scopes chat + proposals; UI should persist it and treat a new thread as a hard boundary.

Destructive operations always require explicit confirmation.

---

## 7) Minimal diffs, traceable change

Changes must be small, scoped, and reviewable.

- No refactors unless explicitly requested.
- Touch the minimum files necessary.
- Every change updates the diff log (if present) and includes verification evidence.

---

## 8) Ship tight MVP loops

We ship the core loops before expanding scope:

1) onboarding prefs
2) inventory intake + consumption
3) meal plan generation
4) shopping list diff
5) recipe uploads + retrieval

Anything else is Phase 2+.

--- End of Manifesto ---
