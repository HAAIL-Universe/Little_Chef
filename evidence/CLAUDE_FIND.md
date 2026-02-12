# CLAUDE_FIND — Debug: MATCH/CHECK in Meal Plan Flow + Allergies Re-prompt

## Bug Report

**Symptom:** User has saved preferences (including allergies) and inventory. When they switch to the Meal Plan flow and ask "what can I make", the app responds with "Please tell me your allergies (or say 'none')" — the prefs wizard, not recipe suggestions.

## A) Evidence Bundle

### 1) Trigger Map: MATCH / CHECK / CONSUME

| Pattern | Regex | File:Line | Handler | Endpoint | Condition |
|---------|-------|-----------|---------|----------|-----------|
| MATCH | `_MATCH_RE` | `app/services/chef_agent.py:24` | `ChefAgent.handle_match()` | `POST /chat` (ask mode) | "what can I make/cook", "suggest meals", etc. |
| CHECK | `_CHECK_RE` | `app/services/chef_agent.py:30` | `ChefAgent.handle_check()` | `POST /chat` (ask mode) | "can I cook X?" |
| CONSUME | `_CONSUME_RE` | `app/services/chef_agent.py:39` | `ChefAgent.handle_consume()` | `POST /chat` (ask mode) | "I cooked X" |

**Router path:** `app/services/chat_service.py:1078-1093` — `_handle_ask()` checks CONSUME → CHECK → MATCH in order. Only reachable when `effective_mode == "ask"`.

**Meal plan endpoint:** `app/api/routers/chat.py:69-78` — `POST /chat/mealplan` calls `ChefAgent.handle_fill()` directly (generates meal plans, no MATCH/CHECK routing).

### 2) Repro Transcript

**Scenario:** User has prefs saved. Switches from Prefs flow → Mealplan flow. Types "what can I make".

1. Frontend `selectFlow("prefs")` sets `lastServerMode = "FILL"` (`web/src/main.ts:2874`)
2. Frontend `selectFlow("mealplan")` does **NOT** reset `lastServerMode` (`web/src/main.ts:2878`)
3. `sendAsk()` sends to `/chat` with `mode: currentModeLower()` = `"fill"` (`web/src/main.ts:1615`)
4. Server `handle_chat()`: `effective_mode == "fill"` → falls into `_handle_prefs_flow_threaded()` (`app/services/chat_service.py:283`)
5. Prefs wizard creates empty draft `UserPrefs(allergies=[], ...)` → `_next_wizard_question(set(), draft)` returns `"allergies"` → **asks "Please tell me your allergies"** (`app/services/chat_service.py:962-963`)

### 3) Prefs Read Path Proof

- **Write:** `PrefsService.upsert_prefs()` — stores `UserPrefs` by `user_id`
- **Read:** `PrefsService.get_prefs(user_id)` — same function used by `ChefAgent.handle_match()`, `handle_check()`, and `handle_fill()`
- **Schema:** `UserPrefs.allergies: List[str]` (`app/schemas.py:27`) — no mismatch, no aliasing
- **NOT the problem:** Prefs are stored and read correctly. The prefs wizard never calls `get_prefs()` — it creates a **brand new empty draft** because it thinks it's starting a fresh prefs conversation.

### 4) The Exact Prompt Logic

`app/services/chat_service.py:104`:
```python
WIZARD_QUESTIONS = {
    "allergies": "Please tell me your allergies (or say 'none').",
    ...
}
```

`app/services/chat_service.py:811-814`: `_next_wizard_question()` returns `"allergies"` when `answered` set is empty.

### 5) Identity / Session Alignment

- Same `user_id` in both flows (from JWT `sub`)
- Same `thread_id` (not reset on flow switch)
- **Identity is correct.** The bug is not an identity mismatch — it's a **mode leak** causing the wrong handler to be invoked.

## B) Root Cause Summary

1. **Frontend mode leak:** `selectFlow("prefs")` sets `lastServerMode = "FILL"` but no other flow resets it. When switching to mealplan, the stale "fill" mode is sent to `/chat`.
2. **Server fill-mode blind spot:** `handle_chat()` with `effective_mode == "fill"` unconditionally routed to `_handle_prefs_flow_threaded()`, ignoring MATCH/CHECK/CONSUME patterns.
3. **Result:** The prefs wizard starts fresh (no draft for the new thread key), creates empty `UserPrefs(allergies=[])`, and asks for allergies — even though prefs exist in storage.

## C) Minimal-Diff Fix Plan (Implemented)

| File | Change |
|------|--------|
| `web/src/main.ts:2874` | Reset `lastServerMode = "ASK"` when switching to any non-prefs flow |
| `app/services/chat_service.py:283` | In fill-mode branch, intercept MATCH/CHECK/CONSUME patterns before the prefs wizard |
| `tests/test_fill_mode_match_check.py` | 6 regression tests: MATCH/CHECK/CONSUME in fill mode + prefs wizard still works |

## D) Diff Hunks

### `web/src/main.ts` — Reset stale mode on flow switch

```diff
   if (currentFlowKey === "prefs") {
     lastServerMode = "FILL";
     updateThreadLabel();
     refreshPrefsOverlay(true);
-  }
+  } else {
+    // Reset mode when leaving prefs flow so stale FILL doesn't leak
+    if (lastServerMode === "FILL") {
+      lastServerMode = "ASK";
+      updateThreadLabel();
+    }
+  }
   if (currentFlowKey === "mealplan") {
```

### `app/services/chat_service.py` — Intercept MATCH/CHECK/CONSUME in fill mode

```diff
         if effective_mode == "fill":
-            response = self._handle_prefs_flow_threaded(user, request, effective_mode)
-            self._append_messages(request.thread_id, user.user_id, request.message, response.reply_text)
-            return response
+            # Intercept MATCH/CHECK/CONSUME even in fill mode so the prefs
+            # wizard doesn't hijack queries that are clearly recipe-related.
+            from app.services.chef_agent import _MATCH_RE, _CHECK_RE, _CONSUME_RE
+            if _CONSUME_RE.search(message):
+                user_obj = UserMe(user_id=user_id)
+                req_obj = ChatRequest(mode="ask", message=message, thread_id=request.thread_id)
+                resp = self.chef_agent.handle_consume(user_obj, req_obj)
+                self._append_messages(request.thread_id, user.user_id, request.message, resp.reply_text)
+                return resp
+            if _CHECK_RE.search(message):
+                user_obj = UserMe(user_id=user_id)
+                req_obj = ChatRequest(mode="ask", message=message)
+                resp = self.chef_agent.handle_check(user_obj, req_obj)
+                self._append_messages(request.thread_id, user.user_id, request.message, resp.reply_text)
+                return resp
+            if _MATCH_RE.search(message):
+                user_obj = UserMe(user_id=user_id)
+                req_obj = ChatRequest(mode="ask", message=message)
+                resp = self.chef_agent.handle_match(user_obj, req_obj)
+                self._append_messages(request.thread_id, user.user_id, request.message, resp.reply_text)
+                return resp
+            response = self._handle_prefs_flow_threaded(user, request, effective_mode)
+            self._append_messages(request.thread_id, user.user_id, request.message, response.reply_text)
+            return response
```

## E) Verification

| Check | Result |
|-------|--------|
| TypeScript build | `npx tsc -p tsconfig.json` — clean, no errors |
| Regression test | `test_fill_mode_match_check.py` — 6/6 pass |
| Full suite | 410 collected, 409 pass, 1 pre-existing flake (`test_auth_schema_missing`) |
| General flow MATCH | Unaffected (routed via ask mode as before) |
| General flow CHECK | Unaffected |
| Prefs wizard | Still works in fill mode for genuine prefs input |
| No new endpoints | No contract changes |

