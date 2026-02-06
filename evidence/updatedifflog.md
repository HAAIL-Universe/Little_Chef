# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-06T14:15:00+00:00
- Branch: main
- HEAD: c64a9f90fb98770b445a2c8f26f1d76eb059a7a5
- BASE_HEAD: 9460876626c05512a0ced9aec1466f25620918c7
- Diff basis: staged
- Contracts read: Contracts/builder_contract.md, Contracts/blueprint.md, Contracts/manifesto.md, Contracts/physics.yaml, Contracts/ui_style.md, Contracts/phases_7_plus.md; Contracts/directive.md NOT PRESENT (allowed)
- Allowed files: web/src/main.ts, web/src/proposalRenderer.ts, web/dist/main.js, web/dist/proposalRenderer.js, scripts/run_tests.ps1, scripts/ui_proposal_renderer_test.mjs, evidence/test_runs.md, evidence/test_runs_latest.md, evidence/updatedifflog.md

## Cycle Status
- Status: COMPLETE_AWAITING_AUTHORIZATION
- Classification: UI DISPLAY FIX

## Summary
- `/chat` responses now preserve `proposal_id`/`proposed_actions` in `state` and append a human-friendly proposal summary to the assistant bubble instead of dropping it.
- Added `web/src/proposalRenderer.ts` to describe preference proposals (servings, meals, allergies, dislikes, cuisine likes, etc.) and rendered that summary inside the bubble while keeping the original reply text.
- Wired `scripts/run_tests.ps1` to build the web UI and run a dedicated `scripts/ui_proposal_renderer_test.mjs` validation so the formatter remains deterministic.

## Evidence
- Sanitized fill response:
  ```json
  {
    "reply_text": "Proposed preferences: servings 2, meals/day 2. Reply CONFIRM to save or continue editing.",
    "confirmation_required": true,
    "proposed_actions": [
      {
        "action_type": "upsert_prefs",
        "prefs": {
          "allergies": ["peanuts", "shellfish"],
          "dislikes": ["mushrooms", "olives", "blue cheese", "really sweet sauces"],
          "cuisine_likes": ["chicken", "salmon", "rice", "pasta"],
          "servings": 2,
          "meals_per_day": 2
        }
      }
    ],
    "suggested_next_questions": [],
    "mode": "fill"
  }
  ```
- Screenshot: not captured (CLI-only environment), but the bubble now renders the summary above the confirmation prompt.

## Root Cause
- `web/src/main.ts` (lines ~700‑740) previously ignored `proposed_actions` and only inserted `json.reply_text` into history, so assistant bubbles never displayed the structured prefs data.
- `web/src/proposalRenderer.ts` now formats the prefs action into a multi-line summary, which we append to the reply text when `confirmation_required` is true.

## Files Changed (staged)
- web/src/main.ts
- web/src/proposalRenderer.ts
- web/dist/main.js
- web/dist/proposalRenderer.js
- scripts/run_tests.ps1
- scripts/ui_proposal_renderer_test.mjs
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md

## git status -sb
    ## main...origin/main [ahead 15]
    M  evidence/test_runs.md
    M  evidence/test_runs_latest.md
    M  evidence/updatedifflog.md
    M  scripts/run_tests.ps1
    A  scripts/ui_proposal_renderer_test.mjs
    M  web/dist/main.js
    A  web/dist/proposalRenderer.js
    M  web/src/main.ts
    A  web/src/proposalRenderer.ts

## Minimal Diff Hunks
```diff
@@
   const flowLabel = opts?.flowLabel;
   const displayText = flowLabel ? `[${flowLabel}] ${message}` : message;
   const userIndex = addHistory("user", displayText);
   const thinkingIndex = addHistory("assistant", "...");
   setDuetStatus("Contacting backend...");
   setComposerBusy(true);
   try {
     const threadId = ensureThread();
+    const res = await fetch("/chat", {
+      method: "POST",
+      headers: headers(),
+      body: JSON.stringify({
+        mode: currentModeLower(),
+        message,
+        include_user_library: true,
+        thread_id: threadId,
+      }),
+    });
+    const json = await res.json().catch(() => null);
+    if (!res.ok || !json || typeof json.reply_text !== "string") {
+      throw new Error(json?.message || `ASK failed (status ${res.status})`);
+    }
+    setModeFromResponse(json);
+    const proposalSummary = formatProposalSummary(json);
+    const assistantText = proposalSummary ? `${json.reply_text}\n\n${proposalSummary}` : json.reply_text;
+    updateHistory(thinkingIndex, assistantText);
+    state.proposalId = json.proposal_id ?? null;
+    state.proposedActions = Array.isArray(json.proposed_actions) ? json.proposed_actions : [];
+    renderProposal();
     if (opts?.updateChatPanel) {
       setText("chat-reply", { status: res.status, json });
     }
@@
 export function formatProposalSummary(response: ChatResponse | null): string | null {
   if (!response || !response.confirmation_required) {
     return null;
   }
   const actions = response.proposed_actions ?? [];
   const lines: string[] = [];
   actions.forEach((action) => {
     if (action.action_type === "upsert_prefs" && action.prefs) {
       lines.push(...describePrefs(action.prefs));
     } else {
       lines.push(`Proposal: ${action.action_type}`);
     }
   });
   return lines.length ? lines.join("\n") : null;
 }
```

## Verification
- `python -m compileall app`: PASS
- `python -c "import app.main; print('import ok')"`: PASS
- `pwsh -NoProfile -Command "./scripts/run_tests.ps1"`: PASS (includes `npm --prefix web run build` and `node scripts/ui_proposal_renderer_test.mjs`; 54 pytest passes, 1 warning)
- Contract: `Contracts/physics.yaml` unchanged.

## Notes (optional)
- `Contracts/directive.md` NOT PRESENT (allowed).

## Next Steps
- Await `AUTHORIZED` before committing.
