# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-08T04:34:46+00:00
- Branch: main
- HEAD: 8d57eaf29e017045e7ea953268932cde3729250d
- BASE_HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
- Diff basis: unstaged (working tree)

## Cycle Status
- Status: COMPLETE

## Summary
- Inventory proposal lines now append USE BY: DD/MM when available
- Notes suppress backend measurement echoes and only surface use_by
- UI renderer test now freezes time and asserts cleaned output

## Files Changed (unstaged (working tree))
- evidence/test_runs.md
- evidence/test_runs_latest.md
- evidence/updatedifflog.md
- scripts/ui_proposal_renderer_test.mjs
- web/dist/proposalRenderer.js
- web/src/proposalRenderer.ts

## git status -sb
    ## main...origin/main [ahead 2]
     M evidence/test_runs.md
     M evidence/test_runs_latest.md
     M evidence/updatedifflog.md
     M scripts/ui_proposal_renderer_test.mjs
     M web/dist/proposalRenderer.js
     M web/src/proposalRenderer.ts

## Minimal Diff Hunks
    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    index 9f1b7d8..638739c 100644
    --- a/evidence/test_runs.md
    +++ b/evidence/test_runs.md
    @@ -12368,3 +12368,33 @@ MM evidence/updatedifflog.md
      6 files changed, 185 insertions(+), 42 deletions(-)
     ```
     
    +## Test Run 2026-02-08T04:34:06Z
    +- Status: PASS
    +- Start: 2026-02-08T04:34:06Z
    +- End: 2026-02-08T04:34:22Z
    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    +- Branch: main
    +- HEAD: 8d57eaf29e017045e7ea953268932cde3729250d
    +- compileall exit: 0
    +- import app.main exit: 0
    +- pytest exit: 0
    +- pytest summary: 73 passed in 3.51s
    +- playwright test:e2e exit: 0
    +- playwright summary:   1 passed (3.0s)
    +- git status -sb:
    +```
    +## main...origin/main [ahead 2]
    + M evidence/updatedifflog.md
    + M scripts/ui_proposal_renderer_test.mjs
    + M web/dist/proposalRenderer.js
    + M web/src/proposalRenderer.ts
    +```
    +- git diff --stat:
    +```
    + evidence/updatedifflog.md             | 366 ++--------------------------------
    + scripts/ui_proposal_renderer_test.mjs |  96 +++++++++
    + web/dist/proposalRenderer.js          |  74 ++++++-
    + web/src/proposalRenderer.ts           |  56 ++++--
    + 4 files changed, 223 insertions(+), 369 deletions(-)
    +```
    +
    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    index 619f3b1..e58446b 100644
    --- a/evidence/test_runs_latest.md
    +++ b/evidence/test_runs_latest.md
    @@ -1,35 +1,29 @@
     Status: PASS
    -Start: 2026-02-08T04:06:48Z
    -End: 2026-02-08T04:07:04Z
    +Start: 2026-02-08T04:34:06Z
    +End: 2026-02-08T04:34:22Z
     Branch: main
    -HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    +HEAD: 8d57eaf29e017045e7ea953268932cde3729250d
     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
     compileall exit: 0
     import app.main exit: 0
     pytest exit: 0
    -pytest summary: 73 passed in 2.78s
    +pytest summary: 73 passed in 3.51s
     playwright test:e2e exit: 0
    -playwright summary:   1 passed (3.1s)
    +playwright summary:   1 passed (3.0s)
     git status -sb:
     ```
    -## main...origin/main [ahead 1]
    -A  evidence/inventory_proposal_format_audit.md
    - M evidence/test_runs.md
    - M evidence/test_runs_latest.md
    -MM evidence/updatedifflog.md
    +## main...origin/main [ahead 2]
    + M evidence/updatedifflog.md
      M scripts/ui_proposal_renderer_test.mjs
      M web/dist/proposalRenderer.js
      M web/src/proposalRenderer.ts
    -?? web/test-results/
     ```
     git diff --stat:
     ```
    - evidence/test_runs.md                 | 29 ++++++++++++
    - evidence/test_runs_latest.md          | 31 ++++++-------
    - evidence/updatedifflog.md             | 84 ++++++++++++++++++++++++++++-------
    - scripts/ui_proposal_renderer_test.mjs |  8 +++-
    - web/dist/proposalRenderer.js          | 33 ++++++++++++--
    - web/src/proposalRenderer.ts           | 42 ++++++++++++++++--
    - 6 files changed, 185 insertions(+), 42 deletions(-)
    + evidence/updatedifflog.md             | 366 ++--------------------------------
    + scripts/ui_proposal_renderer_test.mjs |  96 +++++++++
    + web/dist/proposalRenderer.js          |  74 ++++++-
    + web/src/proposalRenderer.ts           |  56 ++++--
    + 4 files changed, 223 insertions(+), 369 deletions(-)
     ```
     
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 2cf0e29..e8e66a3 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,370 +1,40 @@
     # Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-08T04:07:42+00:00
    +- Timestamp: 2026-02-08T04:32:30+00:00
     - Branch: main
    -- HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    -- BASE_HEAD: 462d734ab1d4bbe73cc845700a0402b2efb18b46
    +- HEAD: 8d57eaf29e017045e7ea953268932cde3729250d
    +- BASE_HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
     - Diff basis: unstaged (working tree)
     
     ## Cycle Status
    -- Status: COMPLETE
    +- Status: IN_PROCESS
     
     ## Summary
    -- UI lines now join name+quantity with plain spaces and humanized kg/L units.
    -- Inventory summary ignores weight_g/volume_ml notes and the UI test expects the new space-delimited bullet.
    +- Plan use_by parsing for proposal lines
    +- Adjust UI tests to cover USE BY output
    +- Note verification steps for compile/build/tests
     
     ## Files Changed (unstaged (working tree))
    -- evidence/test_runs.md
    -- evidence/test_runs_latest.md
    -- evidence/updatedifflog.md
    -- scripts/ui_proposal_renderer_test.mjs
    -- web/src/proposalRenderer.ts
    +- (none detected)
     
     ## git status -sb
    -    ## main...origin/main [ahead 1]
    -    A  evidence/inventory_proposal_format_audit.md
    -     M evidence/test_runs.md
    -     M evidence/test_runs_latest.md
    -    MM evidence/updatedifflog.md
    -     M scripts/ui_proposal_renderer_test.mjs
    -     M web/src/proposalRenderer.ts
    +    ## main...origin/main [ahead 2]
     
     ## Minimal Diff Hunks
    -    diff --git a/evidence/test_runs.md b/evidence/test_runs.md
    -    index 7a24d01..9f1b7d8 100644
    -    --- a/evidence/test_runs.md
    -    +++ b/evidence/test_runs.md
    -    @@ -12303,3 +12303,68 @@ A  web/playwright.config.ts
    -      1 file changed, 154 insertions(+)
    -     ```
    -     
    -    +## Test Run 2026-02-08T04:06:08Z
    -    +- Status: PASS
    -    +- Start: 2026-02-08T04:06:08Z
    -    +- End: 2026-02-08T04:06:26Z
    -    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    -    +- Branch: main
    -    +- HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    -    +- compileall exit: 0
    -    +- import app.main exit: 0
    -    +- pytest exit: 0
    -    +- pytest summary: 73 passed in 3.46s
    -    +- playwright test:e2e exit: 0
    -    +- playwright summary:   1 passed (4.9s)
    -    +- git status -sb:
    -    +```
    -    +## main...origin/main [ahead 1]
    -    +A  evidence/inventory_proposal_format_audit.md
    -    +MM evidence/updatedifflog.md
    -    + M web/dist/proposalRenderer.js
    -    + M web/src/proposalRenderer.ts
    -    +```
    -    +- git diff --stat:
    -    +```
    -    + evidence/updatedifflog.md    | 84 ++++++++++++++++++++++++++++++++++++--------
    -    + web/dist/proposalRenderer.js | 33 ++++++++++++++---
    -    + web/src/proposalRenderer.ts  | 42 +++++++++++++++++++---
    -    + 3 files changed, 136 insertions(+), 23 deletions(-)
    -    +```
    -    +
    -    +## Test Run 2026-02-08T04:06:48Z
    -    +- Status: PASS
    -    +- Start: 2026-02-08T04:06:48Z
    -    +- End: 2026-02-08T04:07:04Z
    -    +- Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    -    +- Branch: main
    -    +- HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    -    +- compileall exit: 0
    -    +- import app.main exit: 0
    -    +- pytest exit: 0
    -    +- pytest summary: 73 passed in 2.78s
    -    +- playwright test:e2e exit: 0
    -    +- playwright summary:   1 passed (3.1s)
    -    +- git status -sb:
    -    +```
    -    +## main...origin/main [ahead 1]
    -    +A  evidence/inventory_proposal_format_audit.md
    -    + M evidence/test_runs.md
    -    + M evidence/test_runs_latest.md
    -    +MM evidence/updatedifflog.md
    -    + M scripts/ui_proposal_renderer_test.mjs
    -    + M web/dist/proposalRenderer.js
    -    + M web/src/proposalRenderer.ts
    -    +?? web/test-results/
    -    +```
    -    +- git diff --stat:
    -    +```
    -    + evidence/test_runs.md                 | 29 ++++++++++++
    -    + evidence/test_runs_latest.md          | 31 ++++++-------
    -    + evidence/updatedifflog.md             | 84 ++++++++++++++++++++++++++++-------
    -    + scripts/ui_proposal_renderer_test.mjs |  8 +++-
    -    + web/dist/proposalRenderer.js          | 33 ++++++++++++--
    -    + web/src/proposalRenderer.ts           | 42 ++++++++++++++++--
    -    + 6 files changed, 185 insertions(+), 42 deletions(-)
    -    +```
    -    +
    -    diff --git a/evidence/test_runs_latest.md b/evidence/test_runs_latest.md
    -    index 88fee17..619f3b1 100644
    -    --- a/evidence/test_runs_latest.md
    -    +++ b/evidence/test_runs_latest.md
    -    @@ -1,31 +1,35 @@
    -     Status: PASS
    -    -Start: 2026-02-08T03:09:34Z
    -    -End: 2026-02-08T03:09:50Z
    -    +Start: 2026-02-08T04:06:48Z
    -    +End: 2026-02-08T04:07:04Z
    -     Branch: main
    -    -HEAD: 92f2551d103c70a3ed48b9b78ebc38181519e1a8
    -    +HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    -     Python: Z:\LittleChef\.venv\\Scripts\\python.exe
    -     compileall exit: 0
    -     import app.main exit: 0
    -     pytest exit: 0
    -    -pytest summary: 73 passed in 3.57s
    -    +pytest summary: 73 passed in 2.78s
    -     playwright test:e2e exit: 0
    -    -playwright summary:   1 passed (3.0s)
    -    +playwright summary:   1 passed (3.1s)
    -     git status -sb:
    -     ```
    -    -## main...origin/main
    -    -M  evidence/test_runs.md
    -    -M  evidence/test_runs_latest.md
    -    -M  evidence/updatedifflog.md
    -    -M  scripts/run_tests.ps1
    -    -A  web/e2e/dev-panel.spec.ts
    -    -M  web/package-lock.json
    -    -M  web/package.json
    -    -A  web/playwright.config.ts
    -    - M web/src/main.ts
    -    +## main...origin/main [ahead 1]
    -    +A  evidence/inventory_proposal_format_audit.md
    -    + M evidence/test_runs.md
    -    + M evidence/test_runs_latest.md
    -    +MM evidence/updatedifflog.md
    -    + M scripts/ui_proposal_renderer_test.mjs
    -    + M web/dist/proposalRenderer.js
    -    + M web/src/proposalRenderer.ts
    -    +?? web/test-results/
    -     ```
    -     git diff --stat:
    -     ```
    -    - web/src/main.ts | 154 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    -    - 1 file changed, 154 insertions(+)
    -    + evidence/test_runs.md                 | 29 ++++++++++++
    -    + evidence/test_runs_latest.md          | 31 ++++++-------
    -    + evidence/updatedifflog.md             | 84 ++++++++++++++++++++++++++++-------
    -    + scripts/ui_proposal_renderer_test.mjs |  8 +++-
    -    + web/dist/proposalRenderer.js          | 33 ++++++++++++--
    -    + web/src/proposalRenderer.ts           | 42 ++++++++++++++++--
    -    + 6 files changed, 185 insertions(+), 42 deletions(-)
    -     ```
    -     
    -    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    -    index fae359b..cedf48b 100644
    -    --- a/evidence/updatedifflog.md
    -    +++ b/evidence/updatedifflog.md
    -    @@ -1,37 +1,91 @@
    -    -﻿# Diff Log (overwrite each cycle)
    -    +# Diff Log (overwrite each cycle)
    -     
    -     ## Cycle Metadata
    -    -- Timestamp: 2026-02-08T03:52:40+00:00
    -    +- Timestamp: 2026-02-08T04:05:45+00:00
    -     - Branch: main
    -     - HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    -     - BASE_HEAD: 462d734ab1d4bbe73cc845700a0402b2efb18b46
    -    -- Diff basis: staged
    -    +- Diff basis: unstaged (working tree)
    -     
    -     ## Cycle Status
    -    -- Status: COMPLETE
    -    +- Status: IN_PROCESS
    -     
    -     ## Summary
    -    -- Documented the /chat/inventory → inventory-agent normalization → Dev Panel rendering path and string sources.
    -    -- Captured measurement-note origins plus three minimal edit candidates (UI/back-end) for the proposal lines.
    -    +- Switch formatInventoryAction to space-separated name+quantity lines.
    -    +- Strip backend measurement echoes before the Dev Panel renders a single clean bullet line.
    -     
    -    -## Files Changed (staged)
    -    -- (none detected)
    -    +## Files Changed (unstaged (working tree))
    -    +- evidence/updatedifflog.md
    -     
    -     ## git status -sb
    -         ## main...origin/main [ahead 1]
    -    -     M evidence/updatedifflog.md
    -    -    ?? evidence/inventory_proposal_format_audit.md
    -    +    A  evidence/inventory_proposal_format_audit.md
    -    +    MM evidence/updatedifflog.md
    -     
    -     ## Minimal Diff Hunks
    -    -    (none)
    -    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    -    +    index fae359b..69f96db 100644
    -    +    --- a/evidence/updatedifflog.md
    -    +    +++ b/evidence/updatedifflog.md
    -    +    @@ -1,37 +1,37 @@
    -    +    -﻿# Diff Log (overwrite each cycle)
    -    +    +# Diff Log (overwrite each cycle)
    -    +     
    -    +     ## Cycle Metadata
    -    +    -- Timestamp: 2026-02-08T03:52:40+00:00
    -    +    +- Timestamp: 2026-02-08T04:05:39+00:00
    -    +     - Branch: main
    -    +     - HEAD: 0101586431fb65e71c3cf6a8dc350e0d727fcc9d
    -    +     - BASE_HEAD: 462d734ab1d4bbe73cc845700a0402b2efb18b46
    -    +    -- Diff basis: staged
    -    +    +- Diff basis: unstaged (working tree)
    -    +     
    -    +     ## Cycle Status
    -    +    -- Status: COMPLETE
    -    +    +- Status: IN_PROCESS
    -    +     
    -    +     ## Summary
    -    +    -- Documented the /chat/inventory → inventory-agent normalization → Dev Panel rendering path and string sources.
    -    +    -- Captured measurement-note origins plus three minimal edit candidates (UI/back-end) for the proposal lines.
    -    +    +- Switch formatInventoryAction to space-separated name+quantity lines.
    -    +    +- Strip backend measurement echoes before the Dev Panel renders a single clean bullet line.
    -    +     
    -    +    -## Files Changed (staged)
    -    +    +## Files Changed (unstaged (working tree))
    -    +     - (none detected)
    -    +     
    -    +     ## git status -sb
    -    +         ## main...origin/main [ahead 1]
    -    +    -     M evidence/updatedifflog.md
    -    +    -    ?? evidence/inventory_proposal_format_audit.md
    -    +    +    A  evidence/inventory_proposal_format_audit.md
    -    +    +    M  evidence/updatedifflog.md
    -    +     
    -    +     ## Minimal Diff Hunks
    -    +         (none)
    -    +     
    -    +     ## Verification
    -    +    -- static: not run (audit-only).
    -    +    -- Re-ran the required git grep/git ls-files commands to confirm anchors.
    -    +    +- static: not run (planning state).
    -    +     
    -    +     ## Notes (optional)
    -    +    -- Contracts/directive.md NOT PRESENT (allowed).
    -    +    +- Contracts/directive.md NOT PRESENT (allowed).
    -    +     
    -    +     ## Next Steps
    -    +    -- phase: minimal formatting tweak site = web/src/proposalRenderer.ts:60-83.
    -    +    +- Edit web/src/proposalRenderer.ts to replace formatInventoryAction as specified.
    -    +    +- Run npm --prefix web run build and scripts/run_tests.ps1 once formatting change is in place.
    -    +     
    -     
    -     ## Verification
    -    -- static: not run (audit-only).
    -    -- Re-ran the required git grep/git ls-files commands to confirm anchors.
    -    +- static: not run (planning state).
    -     
    -     ## Notes (optional)
    -    -- Contracts/directive.md NOT PRESENT (allowed).
    -    +- Contracts/directive.md NOT PRESENT (allowed).
    -     
    -     ## Next Steps
    -    -- phase: minimal formatting tweak site = web/src/proposalRenderer.ts:60-83.
    -    +- Edit web/src/proposalRenderer.ts to replace formatInventoryAction as specified.
    -    +- Run npm --prefix web run build and scripts/run_tests.ps1 once formatting change is in place.
    -     
    -    diff --git a/scripts/ui_proposal_renderer_test.mjs b/scripts/ui_proposal_renderer_test.mjs
    -    index 8d576a5..2f6e78c 100644
    -    --- a/scripts/ui_proposal_renderer_test.mjs
    -    +++ b/scripts/ui_proposal_renderer_test.mjs
    -    @@ -56,8 +56,12 @@ assert(
    -       "inventory summary should not mention preferences"
    -     );
    -     assert(
    -    -  inventorySummary.includes("• cheddar — 1 count — weight_g=300"),
    -    -  "inventory summary should describe the item name, quantity/unit, and note"
    -    +  inventorySummary.includes("• cheddar 1"),
    -    +  "inventory summary should describe the item name and quantity"
    -    +);
    -    +assert(
    -    +  !inventorySummary.includes("weight_g="),
    -    +  "inventory summary should not surface backend measurement notes"
    -     );
    -     const inventoryReply = "Proposed inventory update\n\ninventory update text";
    -     const inventoryCleaned = stripProposalPrefix(inventoryReply);
    -    diff --git a/web/src/proposalRenderer.ts b/web/src/proposalRenderer.ts
    -    index ff1d4d3..f0ab278 100644
    -    --- a/web/src/proposalRenderer.ts
    -    +++ b/web/src/proposalRenderer.ts
    -    @@ -62,21 +62,55 @@ const formatInventoryAction = (action: ChatAction): string => {
    -       if (!event) {
    -         return `• Proposal: ${action.action_type}`;
    -       }
    -    +
    -       const components: string[] = [event.item_name];
    -    -  const unitLabel = event.unit || "count";
    -    +
    -    +  // Quantity formatting (hide "count", humanize g/ml when sensible)
    -       if (event.quantity !== undefined && event.quantity !== null) {
    -    -    components.push(`${event.quantity} ${unitLabel}`);
    -    +    const unit = (event.unit || "").trim().toLowerCase();
    -    +
    -    +    let qtyText = "";
    -    +
    -    +    if (!unit || unit === "count") {
    -    +      qtyText = `${event.quantity}`;
    -    +    } else if (
    -    +      unit === "g" &&
    -    +      typeof event.quantity === "number" &&
    -    +      event.quantity >= 1000 &&
    -    +      event.quantity % 1000 === 0
    -    +    ) {
    -    +      qtyText = `${event.quantity / 1000} kg`;
    -    +    } else if (
    -    +      unit === "ml" &&
    -    +      typeof event.quantity === "number" &&
    -    +      event.quantity >= 1000 &&
    -    +      event.quantity % 1000 === 0
    -    +    ) {
    -    +      qtyText = `${event.quantity / 1000} L`;
    -    +    } else {
    -    +      qtyText = `${event.quantity} ${unit}`;
    -    +    }
    -    +
    -    +    components.push(qtyText);
    -       }
    -    +
    -    +  // Note formatting: drop internal measurement echoes like weight_g=500, volume_ml=500
    -       if (event.note) {
    -         const notePieces = event.note
    -           .split(";")
    -           .map((piece) => piece.trim())
    -    -      .filter(Boolean);
    -    +      .filter(Boolean)
    -    +      .filter((piece) => {
    -    +        const p = piece.toLowerCase();
    -    +        return !(p.startsWith("weight_g=") || p.startsWith("volume_ml="));
    -    +      });
    -    +
    -         if (notePieces.length) {
    -           components.push(notePieces.join("; "));
    -         }
    -       }
    -    -  return `• ${components.join(" — ")}`;
    -    +
    -    +  return `• ${components.join(" ")}`;
    -     };
    -     
    -     export function formatProposalSummary(response: ChatResponse | null): string | null {
    +    (none)
     
     ## Verification
    -- static: npm --prefix web run build
    -- runtime: pwsh -NoProfile -File .\scripts\run_tests.ps1 (compileall, import, pytest, UI renderer + Playwright e2e)
    -- behavior: pwsh -NoProfile -File .\scripts\run_tests.ps1 (ui proposal renderer test + dev-panel Playwright e2e pass)
    -- contract: only web/src/proposalRenderer.ts, scripts/ui_proposal_renderer_test.mjs, and evidence logs changed; no backend/schema edits (Contracts/directive.md NOT PRESENT).
    +- static: pending (compileall)
    +- runtime: pending (run_tests)
    +- behavior: pending (UI tests + e2e)
    +- contract: pending (UI-only change)
     
     ## Notes (optional)
    -- Contracts/directive.md NOT PRESENT (allowed).
     
     ## Next Steps
    -- None
    +- Update web/src/proposalRenderer.ts to format USE BY: DD/MM
    +- Update scripts/ui_proposal_renderer_test.mjs with use_by cases
    +- Run npm --prefix web run build and .\scripts\run_tests.ps1
     
    diff --git a/scripts/ui_proposal_renderer_test.mjs b/scripts/ui_proposal_renderer_test.mjs
    index 2f6e78c..704798d 100644
    --- a/scripts/ui_proposal_renderer_test.mjs
    +++ b/scripts/ui_proposal_renderer_test.mjs
    @@ -63,6 +63,102 @@ assert(
       !inventorySummary.includes("weight_g="),
       "inventory summary should not surface backend measurement notes"
     );
    +
    +const RealDate = Date;
    +const frozenDate = new RealDate("2026-02-08T00:00:00Z");
    +class FrozenDate extends RealDate {
    +  constructor(...args) {
    +    if (args.length === 0) {
    +      return new RealDate(frozenDate);
    +    }
    +    return new RealDate(...args);
    +  }
    +  static now() {
    +    return frozenDate.getTime();
    +  }
    +  static parse(...args) {
    +    return RealDate.parse(...args);
    +  }
    +  static UTC(...args) {
    +    return RealDate.UTC(...args);
    +  }
    +}
    +
    +globalThis.Date = FrozenDate;
    +try {
    +  const useByResponse = {
    +    confirmation_required: true,
    +    proposed_actions: [
    +      {
    +        action_type: "create_inventory_event",
    +        event: {
    +          event_type: "add",
    +          item_name: "olive oil",
    +          quantity: 500,
    +          unit: "ml",
    +          note: "weight_g=1200; use_by=9th",
    +          source: "chat",
    +        },
    +      },
    +    ],
    +  };
    +  const useBySummary = formatProposalSummary(useByResponse);
    +  assert(useBySummary, "use_by summary should exist");
    +  assert(
    +    useBySummary.includes("USE BY: 09/02"),
    +    "inventory summary should render USE BY with fixed month/day format"
    +  );
    +  assert(
    +    !useBySummary.includes("weight_g="),
    +    "measurements should remain hidden even when use_by is present"
    +  );
    +
    +  const useBySecondResponse = {
    +    confirmation_required: true,
    +    proposed_actions: [
    +      {
    +        action_type: "create_inventory_event",
    +        event: {
    +          event_type: "add",
    +          item_name: "tins chopped tomatoes",
    +          quantity: 4,
    +          unit: "count",
    +          note: "volume_ml=2000; use_by=11th",
    +          source: "chat",
    +        },
    +      },
    +    ],
    +  };
    +  const useBySecondSummary = formatProposalSummary(useBySecondResponse);
    +  assert(
    +    useBySecondSummary && useBySecondSummary.includes("USE BY: 11/02"),
    +    "second use_by entry should show updated day"
    +  );
    +
    +  const useByInvalidResponse = {
    +    confirmation_required: true,
    +    proposed_actions: [
    +      {
    +        action_type: "create_inventory_event",
    +        event: {
    +          event_type: "add",
    +          item_name: "frozen peas",
    +          quantity: 900,
    +          unit: "g",
    +          note: "use_by=??",
    +          source: "chat",
    +        },
    +      },
    +    ],
    +  };
    +  const useByInvalidSummary = formatProposalSummary(useByInvalidResponse);
    +  assert(
    +    useByInvalidSummary && !useByInvalidSummary.includes("USE BY:"),
    +    "invalid use_by tokens should not render"
    +  );
    +} finally {
    +  globalThis.Date = RealDate;
    +}
     const inventoryReply = "Proposed inventory update\n\ninventory update text";
     const inventoryCleaned = stripProposalPrefix(inventoryReply);
     assert(
    diff --git a/web/dist/proposalRenderer.js b/web/dist/proposalRenderer.js
    index 91221c7..6c81e58 100644
    --- a/web/dist/proposalRenderer.js
    +++ b/web/dist/proposalRenderer.js
    @@ -29,26 +29,82 @@ const describePrefs = (prefs) => {
         }
         return lines;
     };
    +const parseNoteKeyValues = (note) => {
    +    const fields = {};
    +    note.split(";").forEach((piece) => {
    +        const trimmed = piece.trim();
    +        if (!trimmed) {
    +            return;
    +        }
    +        const equalsIndex = trimmed.indexOf("=");
    +        if (equalsIndex < 0) {
    +            return;
    +        }
    +        const key = trimmed.slice(0, equalsIndex).trim().toLowerCase();
    +        const value = trimmed.slice(equalsIndex + 1).trim();
    +        if (!key || !value) {
    +            return;
    +        }
    +        fields[key] = value;
    +    });
    +    return fields;
    +};
    +const formatUseByToken = (value) => {
    +    if (!value) {
    +        return null;
    +    }
    +    const digits = value.replace(/\D/g, "");
    +    if (!digits) {
    +        return null;
    +    }
    +    const dayNum = parseInt(digits, 10);
    +    if (Number.isNaN(dayNum) || dayNum < 1 || dayNum > 31) {
    +        return null;
    +    }
    +    const now = new Date();
    +    const month = now.getMonth() + 1;
    +    const dayText = String(dayNum).padStart(2, "0");
    +    const monthText = String(month).padStart(2, "0");
    +    return `USE BY: ${dayText}/${monthText}`;
    +};
     const formatInventoryAction = (action) => {
         const event = action.event;
         if (!event) {
             return `• Proposal: ${action.action_type}`;
         }
         const components = [event.item_name];
    -    const unitLabel = event.unit || "count";
    +    // Quantity formatting (hide "count", humanize g/ml when sensible)
         if (event.quantity !== undefined && event.quantity !== null) {
    -        components.push(`${event.quantity} ${unitLabel}`);
    +        const unit = (event.unit || "").trim().toLowerCase();
    +        let qtyText = "";
    +        if (!unit || unit === "count") {
    +            qtyText = `${event.quantity}`;
    +        }
    +        else if (unit === "g" &&
    +            typeof event.quantity === "number" &&
    +            event.quantity >= 1000 &&
    +            event.quantity % 1000 === 0) {
    +            qtyText = `${event.quantity / 1000} kg`;
    +        }
    +        else if (unit === "ml" &&
    +            typeof event.quantity === "number" &&
    +            event.quantity >= 1000 &&
    +            event.quantity % 1000 === 0) {
    +            qtyText = `${event.quantity / 1000} L`;
    +        }
    +        else {
    +            qtyText = `${event.quantity} ${unit}`;
    +        }
    +        components.push(qtyText);
         }
         if (event.note) {
    -        const notePieces = event.note
    -            .split(";")
    -            .map((piece) => piece.trim())
    -            .filter(Boolean);
    -        if (notePieces.length) {
    -            components.push(notePieces.join("; "));
    +        const noteFields = parseNoteKeyValues(event.note);
    +        const useByToken = formatUseByToken(noteFields["use_by"]);
    +        if (useByToken) {
    +            components.push(useByToken);
             }
         }
    -    return `• ${components.join(" — ")}`;
    +    return `• ${components.join(" ")}`;
     };
     export function formatProposalSummary(response) {
         var _a;
    diff --git a/web/src/proposalRenderer.ts b/web/src/proposalRenderer.ts
    index f0ab278..f1aa4b0 100644
    --- a/web/src/proposalRenderer.ts
    +++ b/web/src/proposalRenderer.ts
    @@ -57,6 +57,46 @@ const describePrefs = (prefs: Prefs): string[] => {
       return lines;
     };
     
    +const parseNoteKeyValues = (note: string): Record<string, string> => {
    +  const fields: Record<string, string> = {};
    +  note.split(";").forEach((piece) => {
    +    const trimmed = piece.trim();
    +    if (!trimmed) {
    +      return;
    +    }
    +    const equalsIndex = trimmed.indexOf("=");
    +    if (equalsIndex < 0) {
    +      return;
    +    }
    +    const key = trimmed.slice(0, equalsIndex).trim().toLowerCase();
    +    const value = trimmed.slice(equalsIndex + 1).trim();
    +    if (!key || !value) {
    +      return;
    +    }
    +    fields[key] = value;
    +  });
    +  return fields;
    +};
    +
    +const formatUseByToken = (value?: string): string | null => {
    +  if (!value) {
    +    return null;
    +  }
    +  const digits = value.replace(/\D/g, "");
    +  if (!digits) {
    +    return null;
    +  }
    +  const dayNum = parseInt(digits, 10);
    +  if (Number.isNaN(dayNum) || dayNum < 1 || dayNum > 31) {
    +    return null;
    +  }
    +  const now = new Date();
    +  const month = now.getMonth() + 1;
    +  const dayText = String(dayNum).padStart(2, "0");
    +  const monthText = String(month).padStart(2, "0");
    +  return `USE BY: ${dayText}/${monthText}`;
    +};
    +
     const formatInventoryAction = (action: ChatAction): string => {
       const event = action.event;
       if (!event) {
    @@ -94,19 +134,11 @@ const formatInventoryAction = (action: ChatAction): string => {
         components.push(qtyText);
       }
     
    -  // Note formatting: drop internal measurement echoes like weight_g=500, volume_ml=500
       if (event.note) {
    -    const notePieces = event.note
    -      .split(";")
    -      .map((piece) => piece.trim())
    -      .filter(Boolean)
    -      .filter((piece) => {
    -        const p = piece.toLowerCase();
    -        return !(p.startsWith("weight_g=") || p.startsWith("volume_ml="));
    -      });
    -
    -    if (notePieces.length) {
    -      components.push(notePieces.join("; "));
    +    const noteFields = parseNoteKeyValues(event.note);
    +    const useByToken = formatUseByToken(noteFields["use_by"]);
    +    if (useByToken) {
    +      components.push(useByToken);
         }
       }
     

## Verification
- static: python -m compileall . (pass)
- runtime: pwsh -NoProfile -File .\\scripts\\run_tests.ps1 (includes compile/import/pytest/build/Playwright)
- behavior: run_tests covers node scripts/ui_proposal_renderer_test.mjs + npm --prefix web run test:e2e
- contract: UI-only formatting change (no backend/schema edits)

## Notes (optional)
- Contracts/directive.md NOT PRESENT (allowed).

## Next Steps
- None

