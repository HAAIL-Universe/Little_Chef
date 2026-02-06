# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-06T22:22:23+00:00
- Branch: main
- HEAD: 2044d7c767663cbee44df8bda1e49b877af446b7
- BASE_HEAD: 03240184d9da421f40b383d8bd60515211260a87
- Diff basis: staged

## Cycle Status
- Status: COMPLETE
- Classification: EVIDENCE_ONLY — Phase 8 inventory agent preflight questionnaire

## Summary
- Collected the UI/backend inventory evidence requested in this Phase 8 preflight and proposed a split plan so Julius can decide the agent boundary.

## Phase 8 Preflight Questionnaire
1. **Q1 — Inventory Flow Selector:** `flowOptions` lists the literal flow key inventory in `web/src/main.ts:19-25`, and `currentFlowKey` (`web/src/main.ts:44-57`) is toggled by `selectFlow` (`web/src/main.ts:1345-1358`). The `/chat` POST (`web/src/main.ts:1019-1027`) only carries `mode`, `message`, `include_user_library`, and `thread_id`, so the backend learns about the flow through `ChatRequest`’s optional `location` field (`app/schemas.py:213-218`). `ChatService.handle_chat` (`app/services/chat_service.py:192-214`) therefore routes to inventory only when `request.location` is truthy; without it the prefs branch runs even if the UI displays the inventory menu.
2. **Q2 — Inventory UI Panel:** `refreshInventoryOverlay` (`web/src/main.ts:661-679`) fetches `/inventory/summary` and `/inventory/low-stock`, feeds the bullets via `renderInventoryLists`, and flips `state.inventoryOnboarded` via `markInventoryOnboarded` (`web/src/main.ts:616-622`). `updateInventoryOverlayVisibility` (`web/src/main.ts:691-704`) toggles the `.inventory-ghost` overlay only when `currentFlowKey === "inventory"` and `state.inventoryOnboarded` is true, and `setupInventoryGhostOverlay` (`web/src/main.ts:706-785`) builds the absolute positioned container with a pointer-events-none wrapper and an inner panel that re-enables interactions. The prefs overlay mirrors that pattern: `refreshPrefsOverlay` hits `/prefs` (`web/src/main.ts:857-874`), `updatePrefsOverlayVisibility` gates on `currentFlowKey === "prefs" && !!state.onboarded` (`web/src/main.ts:884-891`), and `setupPrefsOverlay`/`renderPrefsOverlay` (`web/src/main.ts:894-955` and `793-838`) reuse the same glass-card layout.
3. **Q3 — Inventory API Endpoints:** `app/api/routers/inventory.py:12-44` exposes `/inventory/events`, `/inventory/summary`, and `/inventory/low-stock`, all forwarded to `InventoryService.summary`/`low_stock` (`app/services/inventory_service.py:21-74`). The chat surface is provided by `app/api/routers/chat.py:20-43`, which instantiates `ChatService` and routes `/chat` and `/chat/confirm` to it.
4. **Q4 — Parsing/Extraction:** `extract_new_draft` and `extract_edit_ops` (`app/services/inventory_parse_service.py:10-46`) call `LlmClient.generate_structured_reply` with JSON schemas that return `name_raw`, `quantity_raw`, `unit_raw`, `expires_raw`, and `notes_raw`. `normalize_items` (`app/services/inventory_normalizer.py:7-99`) turns raw drafts into normalized dictionaries, converting kg->g, l->ml, defaulting units to g while emitting `UNIT_ASSUMED_G`, parsing GB dates, building `item_key`, and appending warnings such as `LOCATION_SUSPICIOUS` for pantry eggs. These helpers rely on `LlmClient.generate_structured_reply` (`app/services/llm_client.py:35-117`), which only runs when `LLM_ENABLED` is truthy, the `OPENAI_MODEL` is a valid `gpt-5*-mini`/`gpt-5*-nano`, and it returns JSON-schema compliant data.
5. **Q5 — Proposal/Confirm/Edit/Deny:** `ChatService.handle_chat` (`app/services/chat_service.py:192-214`) dispatches inventory when `request.location` exists; `_handle_inventory_flow` (`app/services/chat_service.py:262-315`) implements two states (draft creation via `extract_new_draft` and edit via `extract_edit_ops`), normalizes items, stores proposals via `ProposalStore` (`app/services/proposal_store.py:1-32`), and keeps the unconfirmed draft in `pending_raw`. `_apply_ops`, `_to_actions`, and `_render_proposal` build the structured inventory action bundle. `confirm` (`app/services/chat_service.py:379-451`) only writes to the repository when `confirm=True`, popping the stored proposal, calling `InventoryService.create_event`, appending `applied_event_ids`, and clearing `pending_raw`, guaranteeing confirm-before-write semantics.
6. **Q6 — DB Persistence:** `DbInventoryRepository.create_event` (`app/repos/inventory_repo.py:53-133`) `INSERT`s into `inventory_events` (with `ensure_user` and `payload` JSON) and `SELECT`s rows for reads; when `DATABASE_URL` is set `get_inventory_repository()` (`app/repos/inventory_repo.py:135-138`) returns this implementation. The schema in `db/migrations/0001_init.sql:13-32` defines `inventory_events` with `event_id`, `user_id`, `occurred_at`, `event_type`, `payload`, and an index on `(user_id, occurred_at)`.
7. **Q7 — Tests:** `tests/test_chat_inventory_fill_propose_confirm.py` demonstrates `/chat` proposals returning a `create_inventory_event` action and that `/chat/confirm` applies it; `tests/test_chat_inventory_ask_low_stock.py` ensures `ask` mode surfaces low-stock text; `tests/test_inventory_summary_derived.py`, `tests/test_inventory_low_stock_defaults.py`, and `tests/test_inventory_events_create_and_list.py` exercise the summary, low-stock, and event endpoints directly; `tests/test_inventory_proposals.py` guards pending edits, denial, and confirm-only writes. A gap remains: there is no test ensuring the backend only emits inventory actions when the UI explicitly signals the inventory flow.
8. **Q8 — Known Bleed:** The UI’s `/chat` POST body never includes `location` or a flow key—only `mode`, `message`, `include_user_library`, and `thread_id` are sent (`web/src/main.ts:1019-1027`). Meanwhile, the backend routing branch depends on `request.location` (`app/services/chat_service.py:192-215`) so every `fill` request without location enters the prefs flow, letting prefs proposals leak through even inside Inventory UI; the only backend-level clue that distinguishes inventory is the optional `location` in `ChatRequest` (`app/schemas.py:213-218`).
9. **Q9 — Phase 8 Split Plan:** Option A (backend-first agent split) is the most suitable path because the core inventory state machine already exists in `ChatService`. Minimal plan: (a) update `web/src/main.ts` to send a `location` value whenever `selectFlow(inventory)` is active (and optionally send a `flow_key` so the backend gets an explicit signal); (b) factor the inventory pipeline (`extract_new_draft`, `_handle_inventory_flow`, `_apply_ops`, `_render_proposal`, `_to-actions`, `pending_raw`) into a dedicated `app/services/inventory_agent.py` that only returns `create_inventory_event` actions and reuses `inventory_parse_service`/`normalize_items`; (c) adjust `app/services/chat_service.py` and `app/api/routers/chat.py` to inject the new agent and delegate inventory flows to it while keeping prefs handling isolated; (d) add regression tests (e.g., extend `tests/test_chat_inventory_fill_propose_confirm.py` or add `tests/test_inventory_agent.py`) that assert inventory-agent responses never include `upsert_prefs` and that prefs proposals remain when location is absent. This preserves the confirm-before-write gate while empowering a future meal-plan agent to reuse the same pattern.

## Files Changed (staged)
- evidence/updatedifflog.md

## git status -sb
    ## main...origin/main
    M evidence/updatedifflog.md

## Minimal Diff Hunks
    - Replaced the entire diff log with the Phase 8 preflight questionnaire text and added the new classification line.

## Verification
- N/A (evidence-only; no code changes)

## Notes (optional)
- All required anchors have been gathered; no blockers remain for this evidence-only step.

## Next Steps
- Wait for Julius to review the questionnaire, authorize the Phase 8 plan, and direct the subsequent inventory-agent implementation.
