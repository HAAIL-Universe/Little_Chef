# CLAUDE_FIND — Pre-existing Failure Analysis

## Summary

- **TS2339 L1199** — (A) real product bug. Frontend `InventorySummaryItem` type is missing `location` field that the backend schema declares and returns. Deterministic.
- **history-badge.spec.ts** — (B) test fragility. Test asserts "👍" in `#duet-user-bubble .bubble-text`, but "👍" is rendered in a separate `#duet-sent-indicator` button. Test also lacks `/chat` API mock, so sends fail with network error. Deterministic.
- **inventory-overlay.spec.ts** — (B) test fragility. Test expects `button[data-onboard-item=mealplan]` in the onboard menu, but `?skipauth=1` never sets `state.token`, so `renderOnboardMenuButtons()` gates at the token check and only renders a Login button. Deterministic.

---

## Failure 1: TS2339 — `Property 'location' does not exist on type 'InventorySummaryItem'`

### 1) Evidence Anchors

**Compiler error:**
```
src/main.ts:1199:26 - error TS2339: Property 'location' does not exist on type 'InventorySummaryItem'.
1199         const loc = item.location || "pantry";
                              ~~~~~~~~
```

**Frontend type definition** (`web/src/main.ts` L110):
```ts
type InventorySummaryItem = { item_name: string; quantity: number; unit: string; approx?: boolean };
```

**Usage site** (`web/src/main.ts` L1196–1210):
```ts
      const groups: Record<string, InventorySummaryItem[]> = {};
      summary.forEach(item => {
        const loc = item.location || "pantry";     // ← TS2339 here
        (groups[loc] ??= []).push(item);
      });
      for (const loc of ["pantry", "fridge", "freezer"]) {
        if (!groups[loc]?.length) continue;
        const hdr = document.createElement("li");
        hdr.className = "inv-loc-header";
        hdr.textContent = loc.charAt(0).toUpperCase() + loc.slice(1);
        summaryList.appendChild(hdr);
        groups[loc].forEach(item => {
          const li = document.createElement("li");
          li.textContent = `${item.item_name} - ${formatQuantity(item.quantity, item.unit, item.approx)}`;
          summaryList.appendChild(li);
        });
      }
```

**Backend schema** (`app/schemas.py` L54, L91–97):
```python
Location = Literal["pantry", "fridge", "freezer"]   # L54

class InventorySummaryItem(BaseModel):               # L91
    item_name: str
    quantity: float
    unit: Unit
    location: Location = "pantry"                    # ← field exists in backend
    approx: bool = False
```

### 2) Root Cause

The frontend runtime code correctly accesses `item.location` — this property IS returned by the API (default `"pantry"`). The **TypeScript type alias** at L110 was never updated when `location` was added to the backend schema. This is a type-definition-only gap; the runtime behavior is correct and working.

**Classification: (A) real product bug** (type definition incomplete — causes tsc failure).
**Deterministic: Yes** — pure compile-time, 100% reproducible.

### 3) Fix Options

**Option 1 (preferred): Add `location` to the frontend type**
- File: `web/src/main.ts` L110
- Change:
  ```ts
  // Before
  type InventorySummaryItem = { item_name: string; quantity: number; unit: string; approx?: boolean };
  // After
  type InventorySummaryItem = { item_name: string; quantity: number; unit: string; location?: "pantry" | "fridge" | "freezer"; approx?: boolean };
  ```
- Why: Matches backend `Location = Literal["pantry", "fridge", "freezer"]` with default `"pantry"`. Optional (`?`) because the fallback `|| "pantry"` at L1199 already handles it.
- Risk: None. Purely additive type change.

**Option 2: Use type assertion at usage site**
- File: `web/src/main.ts` L1199
- Change: `const loc = (item as any).location || "pantry";`
- Why: Suppresses the error without touching the shared type.
- Risk: Hides future type errors on that property. Not recommended.

### 4) Verification

```powershell
cd web && npx tsc --noEmit
```
Expected: 0 errors (was 1 error).

---

## Failure 2: history-badge.spec.ts — bubble text never shows "👍"

### 1) Evidence Anchors

**Test file:** `web/e2e/history-badge.spec.ts`
**Full test name:** `History badge and bubble › sent bubble and badge track normal chat activity`

**Failing assertion** (L19):
```ts
await expect(bubbleText).toHaveText("👍", { timeout: 5000 });
```
where `bubbleText = page.locator("#duet-user-bubble .bubble-text")`.

**Error output:**
```
Error: expect(locator).toHaveText(expected) failed
Locator:  locator('#duet-user-bubble .bubble-text')
Expected: "👍"
Received: "Long-press this chat bubble to log in."
Timeout:  5000ms
```

**DOM selectors involved:**
- `#duet-user-bubble .bubble-text` — the user bubble's text div (resolved to `<div class="bubble-text" id="duet-user-text">`)
- `#duet-sent-indicator` — separate button rendered by `ensureDuetShellControls()` at L1080–1088

**Where "👍" is actually rendered** (`web/src/main.ts` L164, L1086):
```ts
const USER_BUBBLE_SENT_TEXT = "👍";
// ...
sentIndicatorBtn.textContent = USER_BUBBLE_SENT_TEXT; // L1086 — on #duet-sent-indicator
```

**Where `.bubble-text` content is set** (`web/src/main.ts` L845–862, `updateDuetBubbles()`):
```ts
const fallbackText = isNormalChatFlow() ? userSystemHint : lastUser?.text ?? userSystemHint;
setBubbleText(user, fallbackText);
```

Since `?skipauth=1` never sets `state.token`, `refreshSystemHints()` (L183) sets:
```ts
if (!s.is_logged_in) {
    userSystemHint = "Long-press this chat bubble to log in.";
```

**No API mocks:** The test has zero `page.route()` calls. Sends to `/chat` fail with network error. Even if they succeeded, `updateDuetBubbles()` sets bubble text to `userSystemHint`, never "👍".

### 2) Root Cause

Two independent issues:
1. **Wrong selector**: The "👍" text is displayed in `#duet-sent-indicator` (a separate button in the shell), not in `#duet-user-bubble .bubble-text`. The test asserts on the wrong element.
2. **No API mock**: Without mocking `/chat`, the `send()` path hits a network error. The assistant text becomes "Network error. Try again." but the user bubble text remains the system hint regardless — it's always set via `updateDuetBubbles()` to `userSystemHint`.

The DOM snapshot from `error-context.md` confirms: the sent indicator button shows `"👍"` at `button "Message sent"` while `.bubble-text` shows the login hint.

**Classification: (B) test fragility** — test locator doesn't match the actual UI structure.
**Deterministic: Yes** — structurally never passes.

### 3) Fix Options

**Option 1 (preferred): Fix the locator + add API mock**
- File: `web/e2e/history-badge.spec.ts`
- Changes:
  1. Add `page.route("**/chat", ...)` mock returning `{ reply_text: "ok", thread_id: "t1" }` before the loop.
  2. Change `bubbleText` locator from `#duet-user-bubble .bubble-text` to `#duet-sent-indicator`.
  3. Adjust visible/text assertions accordingly. The sent-indicator gets class `visible` after send + reply, and its text is always "👍".
- Why: Aligns test with actual UI. The mock ensures the send completes and triggers the sent-indicator visibility.
- Risk: Low. Purely test-side change.

**Option 2: Mock /chat AND set a fake token via skipauth**
- Files: `web/e2e/history-badge.spec.ts` + potentially `web/src/main.ts`
- If `?skipauth=1` also set `state.token = "test"`, then `userSystemHint` would change, and `updateDuetBubbles()` would show different text. But the bubble text still wouldn't become "👍" — that's structurally on a separate element.
- Risk: Requires product code change for test purposes. Not recommended standalone.

**Option 3: Skip the bubble-text assertion entirely, test only the badge counter**
- File: `web/e2e/history-badge.spec.ts`
- Remove the `await expect(bubbleText).toHaveText("👍", ...)` lines, keep only badge counter assertions.
- Why: The badge counter is the stated purpose of the test. The bubble assertion is an unrelated concern.
- Risk: Loses coverage of send-indicator visibility. Acceptable if covered elsewhere.

### 4) Verification

```powershell
cd web && npx playwright test e2e/history-badge.spec.ts --reporter=list
```
Expected: 1 passed (was 1 failed).

---

## Failure 3: inventory-overlay.spec.ts — mealplan button not found

### 1) Evidence Anchors

**Test file:** `web/e2e/inventory-overlay.spec.ts`
**Full test name:** `inventory overlay appears after confirming inventory proposal`

**Failing assertion** (L139):
```ts
const mealPlanBtn = onboardMenu.locator("button[data-onboard-item=mealplan]");
await expect(mealPlanBtn).toHaveCount(1);
```

**Error output:**
```
Error: expect(locator).toHaveCount(expected) failed
Locator:  locator('#onboard-menu').locator('button[data-onboard-item=mealplan]')
Expected: 1
Received: 0
Timeout:  5000ms
```

**DOM selectors involved:**
- `#onboard-menu` — the onboard context menu (visible after long-press)
- `button[data-onboard-item=mealplan]` — button created via `planBtn.dataset.onboardItem = "mealplan"` at L2958

**`renderOnboardMenuButtons()`** (`web/src/main.ts` L2911–2968):
```ts
function renderOnboardMenuButtons() {
  if (!onboardMenu) return;
  onboardMenu.innerHTML = "";

  // Before login: show only Login button
  if (!state.token?.trim()) {     // ← GATE: no token means early return
    const loginBtn = document.createElement("button");
    // ... loginBtn.dataset.onboardItem = "login"
    onboardMenu.appendChild(loginBtn);
    return;                        // ← returns here, never reaches mealplan
  }

  // ... Preferences button (always after login) ...
  if (state.onboarded) {
    // ... Inventory button ...
  }
  if (state.inventoryOnboarded) {  // ← mealplan button created here
    const planBtn = document.createElement("button");
    planBtn.dataset.onboardItem = "mealplan";
    // ...
  }
}
```

**`?skipauth=1` behavior** (`web/src/main.ts` L2203–2205):
```ts
if (!isSkipAuth()) {
    openLoginModal();
}
```
It only skips the login modal. It does NOT set `state.token`. So `!state.token?.trim()` is truthy, and `renderOnboardMenuButtons()` returns early with only a Login button.

**DOM snapshot confirms:** The `error-context.md` shows `button "Login"` inside the menu — no Preferences, Inventory, or Meal Plan buttons.

### 2) Root Cause

The test successfully confirms the inventory proposal (setting `state.inventoryOnboarded = true`), then long-presses the bubble to open the onboard menu. But `renderOnboardMenuButtons()` checks `!state.token?.trim()` first and returns early, rendering only the Login button. The `inventoryOnboarded` check on L2955 is never reached.

The test was likely written assuming `?skipauth=1` would also set a fake token, or was written before the token gate was added to `renderOnboardMenuButtons()`.

**Classification: (B) test fragility** — test setup doesn't match the state required by the UI gate.
**Deterministic: Yes** — token is structurally never set.

### 3) Fix Options

**Option 1 (preferred): Set a fake token in the test setup via page.evaluate + expose state**
- File: `web/e2e/inventory-overlay.spec.ts`
- The challenge is that `state` is module-scoped. The cleanest approach is to make `?skipauth=1` also set `state.token = "skip"` in the product code.
- File: `web/src/main.ts` — in the startup path where `isSkipAuth()` is checked, add:
  ```ts
  if (isSkipAuth()) {
    state.token = "skip";
  }
  ```
- Why: Makes `?skipauth=1` behave fully as-if-logged-in, which matches the intent of all e2e tests that use it.
- Risk: Medium. Changes `skipauth` semantics globally. Any test relying on skipauth being token-less would break. Verify all tests using `?skipauth=1` still pass.

**Option 2: Expose state for testing via a window global**
- File: `web/src/main.ts`
- Add: `if (isSkipAuth()) { (window as any).__littlechef_state = state; }`
- Then in test before long-press:
  ```ts
  await page.evaluate(() => { (window as any).__littlechef_state.token = "fake"; });
  ```
  And trigger re-render: `await page.evaluate(() => { renderOnboardMenuButtons(); });`
- Why: Allows test-only state manipulation without changing skipauth behavior for other code paths.
- Risk: Exposes internals. Should be gated behind debug/test flag.

**Option 3: Remove the mealplan assertion from this test**
- File: `web/e2e/inventory-overlay.spec.ts`
- Remove L126–141 (the long-press and onboard-menu assertions).
- Why: The test's primary purpose is "inventory overlay appears after confirming inventory proposal" — the mealplan button assertion is an unrelated concern tacked on.
- Risk: Loses coverage of mealplan onboard-menu entry. Acceptable if tested elsewhere.

### 4) Verification

```powershell
cd web && npx playwright test e2e/inventory-overlay.spec.ts --reporter=list
```
Expected: 1 passed (was 1 failed).

---

## Cross-cutting Notes

| # | File | Classification | Deterministic | Recent Changes Exposed It? |
|---|------|---------------|--------------|--------------------------|
| 1 | `web/src/main.ts` L110 | (A) real product bug | Yes | No — introduced when inventory location grouping was added |
| 2 | `web/e2e/history-badge.spec.ts` | (B) test fragility | Yes | No — structural mismatch since sent-indicator was split from bubble |
| 3 | `web/e2e/inventory-overlay.spec.ts` | (B) test fragility | Yes | No — structural mismatch since token gate was added to onboard menu |

None of these failures were introduced or worsened by the recent compose-next-hint changes. All three are long-standing structural mismatches between tests/types and the current product code.
