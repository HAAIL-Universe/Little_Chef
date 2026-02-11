# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T19:59:41+00:00
- Branch: claude/romantic-jones
- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Added `margin: 0` to `.compose-close-btn` in CSS to override the inherited global `button { margin-top: 6px }` rule.
- Root cause: `getBoundingClientRect()` returns the trigger's border-box position, but CSS `top` on `.compose-close-btn` positions the margin-box edge. The inherited 6px margin-top pushed the close button 6px lower than the trigger.
- No blur, layering, or JS changes. CSS-only fix (1 property added in src + dist).

## Files Changed (staged)
- evidence/updatedifflog.md
- web/dist/main.js
- web/dist/style.css
- web/src/main.ts
- web/src/style.css

## git status -sb
    ## claude/romantic-jones
     M .claude/settings.local.json
    M  evidence/updatedifflog.md
    M  web/dist/main.js
    M  web/dist/style.css
    M  web/src/main.ts
    M  web/src/style.css

## Minimal Diff Hunks
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 81ccc1e..bbaaa7d 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,87 +1,707 @@
     ´╗┐# Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-11T18:45:00+00:00
    +- Timestamp: 2026-02-11T19:49:41+00:00
     - Branch: claude/romantic-jones
    -- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -- Diff basis: unstaged
    +- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    +- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    +- Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- Replaced composer UX with centered "ghost narrator" input overlay.
    -- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
    -- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
    -- Textarea auto-expands vertically as user types (up to max-height).
    -- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
    -- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
    -- No borders/box/chrome on the centered input ÔÇö ghost narrator styling.
    -- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
    -- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.
    +- Restored subtle `backdrop-filter: blur(2px)` to `.compose-overlay-backdrop` (was removed entirely in cycle 3). Soft-focus effect, background remains readable.
    +- Fixed compose X button position to match original `.flow-menu-toggle` location: `showComposeOverlay()` now reads the flow-menu-trigger's `getBoundingClientRect()` and applies those coordinates as inline `top`/`right` on `.compose-close-btn`.
    +- `hideComposeOverlay()` clears inline positioning on the close button.
    +- No layout changes; X appears at exact same viewport position as the original gear/close button.
    +- CSS `.compose-close-btn` top/right kept as fallback for edge cases.
     
    -## Files Changed (unstaged)
    -- web/index.html ÔÇö `<input>` ÔåÆ `<textarea>` in composer
    -- web/src/main.ts ÔÇö compose overlay logic, type updates, auto-expand, VisualViewport handler
    -- web/src/style.css ÔÇö textarea styles, compose overlay CSS, narrator styling
    -- web/dist/index.html ÔÇö `<input>` ÔåÆ `<textarea>` (built)
    -- web/dist/main.js ÔÇö compiled output
    -- web/dist/style.css ÔÇö compiled CSS
    -- evidence/updatedifflog.md ÔÇö this file
    +## Files Changed (staged)
    +- evidence/updatedifflog.md
    +- web/dist/main.js
    +- web/dist/style.css
    +- web/src/main.ts
    +- web/src/style.css
     
     ## git status -sb
         ## claude/romantic-jones
          M .claude/settings.local.json
    -     M web/dist/index.html
    -     M web/dist/main.js
    -     M web/dist/style.css
    -     M web/index.html
    -     M web/src/main.ts
    -     M web/src/style.css
    +    M  evidence/updatedifflog.md
    +    M  web/dist/main.js
    +    M  web/dist/style.css
    +    M  web/src/main.ts
    +    M  web/src/style.css
     
    -## Minimal Diff Hunks (source files only)
    -
    -### web/index.html
    -- `<input id="duet-input" type="text" .../>` ÔåÆ `<textarea id="duet-input" rows="1" ...></textarea>`
    -
    -### web/src/style.css
    -- `.duet-composer input` ÔåÆ `.duet-composer textarea`
    -- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
    -- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
    -- New `.compose-overlay.active` (visible)
    -- New `.compose-overlay-backdrop` (translucent + blur)
    -- New `.compose-narrator` (centered flex column, 520px max width)
    -- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
    -- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")
    -
    -### web/src/main.ts
    -- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
    -- 6├ù `HTMLInputElement` ÔåÆ `HTMLTextAreaElement` for `#duet-input`
    -- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
    -- `showFloatingComposer()`: redirects to `showComposeOverlay()`
    -- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
    -- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
    -- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap
    +## Minimal Diff Hunks
    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    +    index 81ccc1e..cb58614 100644
    +    --- a/evidence/updatedifflog.md
    +    +++ b/evidence/updatedifflog.md
    +    @@ -1,87 +1,343 @@
    +     ┬┤ÔòùÔöÉ# Diff Log (overwrite each cycle)
    +     
    +     ## Cycle Metadata
    +    -- Timestamp: 2026-02-11T18:45:00+00:00
    +    +- Timestamp: 2026-02-11T19:40:53+00:00
    +     - Branch: claude/romantic-jones
    +    -- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    +    -- Diff basis: unstaged
    +    +- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    +    +- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    +    +- Diff basis: staged
    +     
    +     ## Cycle Status
    +     - Status: COMPLETE
    +     
    +     ## Summary
    +    -- Replaced composer UX with centered "ghost narrator" input overlay.
    +    -- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
    +    -- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
    +    -- Textarea auto-expands vertically as user types (up to max-height).
    +    -- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
    +    -- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
    +    -- No borders/box/chrome on the centered input ├ö├ç├Â ghost narrator styling.
    +    -- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
    +    -- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.
    +    +- Removed compose overlay backdrop blur entirely (was 2px) and reduced dim from 0.30 ├ö├Ñ├å 0.18; background messages now clearly readable.
    +    +- Fixed X close button not clickable: root cause was `.duet-shell` `backdrop-filter: blur(10px)` creating a CSS stacking context that traps all children below the compose overlay on `document.body`.
    +    +- Solution: added dedicated `.compose-close-btn` (├ö┬ú├▓) inside `.compose-overlay` itself, wired to `hideComposeOverlay()`. Sidesteps stacking context entirely.
    +    +- Removed non-functional `.flow-menu.compose-elevated` CSS rule and class toggle from JS.
    +    +- Flow-menu trigger now hidden during compose mode instead of showing close-mode styling.
    +     
    +    -## Files Changed (unstaged)
    +    -- web/index.html ├ö├ç├Â `<input>` ├ö├Ñ├å `<textarea>` in composer
    +    -- web/src/main.ts ├ö├ç├Â compose overlay logic, type updates, auto-expand, VisualViewport handler
    +    -- web/src/style.css ├ö├ç├Â textarea styles, compose overlay CSS, narrator styling
    +    -- web/dist/index.html ├ö├ç├Â `<input>` ├ö├Ñ├å `<textarea>` (built)
    +    -- web/dist/main.js ├ö├ç├Â compiled output
    +    -- web/dist/style.css ├ö├ç├Â compiled CSS
    +    -- evidence/updatedifflog.md ├ö├ç├Â this file
    +    +## Files Changed (staged)
    +    +- evidence/updatedifflog.md
    +    +- web/dist/main.js
    +    +- web/dist/style.css
    +    +- web/src/main.ts
    +    +- web/src/style.css
    +     
    +     ## git status -sb
    +         ## claude/romantic-jones
    +          M .claude/settings.local.json
    +    -     M web/dist/index.html
    +    -     M web/dist/main.js
    +    -     M web/dist/style.css
    +    -     M web/index.html
    +    -     M web/src/main.ts
    +    -     M web/src/style.css
    +    +    M  evidence/updatedifflog.md
    +    +    M  web/dist/main.js
    +    +    M  web/dist/style.css
    +    +    M  web/src/main.ts
    +    +    M  web/src/style.css
    +     
    +    -## Minimal Diff Hunks (source files only)
    +    -
    +    -### web/index.html
    +    -- `<input id="duet-input" type="text" .../>` ├ö├Ñ├å `<textarea id="duet-input" rows="1" ...></textarea>`
    +    -
    +    -### web/src/style.css
    +    -- `.duet-composer input` ├ö├Ñ├å `.duet-composer textarea`
    +    -- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
    +    -- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
    +    -- New `.compose-overlay.active` (visible)
    +    -- New `.compose-overlay-backdrop` (translucent + blur)
    +    -- New `.compose-narrator` (centered flex column, 520px max width)
    +    -- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
    +    -- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")
    +    -
    +    -### web/src/main.ts
    +    -- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
    +    -- 6Ôö£├╣ `HTMLInputElement` ├ö├Ñ├å `HTMLTextAreaElement` for `#duet-input`
    +    -- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
    +    -- `showFloatingComposer()`: redirects to `showComposeOverlay()`
    +    -- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
    +    -- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
    +    -- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap
    +    +## Minimal Diff Hunks
    +    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    +    +    index 81ccc1e..f4a8382 100644
    +    +    --- a/evidence/updatedifflog.md
    +    +    +++ b/evidence/updatedifflog.md
    +    +    @@ -1,87 +1,39 @@
    +    +     Ôö¼Ôöñ├ö├▓├╣├ö├Â├ë# Diff Log (overwrite each cycle)
    +    +     
    +    +     ## Cycle Metadata
    +    +    -- Timestamp: 2026-02-11T18:45:00+00:00
    +    +    +- Timestamp: 2026-02-11T19:40:46+00:00
    +    +     - Branch: claude/romantic-jones
    +    +    -- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    +    +    -- Diff basis: unstaged
    +    +    +- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    +    +    +- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    +    +    +- Diff basis: staged
    +    +     
    +    +     ## Cycle Status
    +    +    -- Status: COMPLETE
    +    +    +- Status: IN_PROCESS
    +    +     
    +    +     ## Summary
    +    +    -- Replaced composer UX with centered "ghost narrator" input overlay.
    +    +    -- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
    +    +    -- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
    +    +    -- Textarea auto-expands vertically as user types (up to max-height).
    +    +    -- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
    +    +    -- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
    +    +    -- No borders/box/chrome on the centered input Ôö£├ÂÔö£├ºÔö£├é ghost narrator styling.
    +    +    -- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
    +    +    -- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.
    +    +    +- TODO: 1-5 bullets (what changed, why, scope).
    +    +     
    +    +    -## Files Changed (unstaged)
    +    +    -- web/index.html Ôö£├ÂÔö£├ºÔö£├é `<input>` Ôö£├ÂÔö£├æÔö£├Ñ `<textarea>` in composer
    +    +    -- web/src/main.ts Ôö£├ÂÔö£├ºÔö£├é compose overlay logic, type updates, auto-expand, VisualViewport handler
    +    +    -- web/src/style.css Ôö£├ÂÔö£├ºÔö£├é textarea styles, compose overlay CSS, narrator styling
    +    +    -- web/dist/index.html Ôö£├ÂÔö£├ºÔö£├é `<input>` Ôö£├ÂÔö£├æÔö£├Ñ `<textarea>` (built)
    +    +    -- web/dist/main.js Ôö£├ÂÔö£├ºÔö£├é compiled output
    +    +    -- web/dist/style.css Ôö£├ÂÔö£├ºÔö£├é compiled CSS
    +    +    -- evidence/updatedifflog.md Ôö£├ÂÔö£├ºÔö£├é this file
    +    +    +## Files Changed (staged)
    +    +    +- (none detected)
    +    +     
    +    +     ## git status -sb
    +    +         ## claude/romantic-jones
    +    +          M .claude/settings.local.json
    +    +    -     M web/dist/index.html
    +    +    +     M evidence/updatedifflog.md
    +    +          M web/dist/main.js
    +    +          M web/dist/style.css
    +    +    -     M web/index.html
    +    +          M web/src/main.ts
    +    +          M web/src/style.css
    +    +     
    +    +    -## Minimal Diff Hunks (source files only)
    +    +    -
    +    +    -### web/index.html
    +    +    -- `<input id="duet-input" type="text" .../>` Ôö£├ÂÔö£├æÔö£├Ñ `<textarea id="duet-input" rows="1" ...></textarea>`
    +    +    -
    +    +    -### web/src/style.css
    +    +    -- `.duet-composer input` Ôö£├ÂÔö£├æÔö£├Ñ `.duet-composer textarea`
    +    +    -- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
    +    +    -- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
    +    +    -- New `.compose-overlay.active` (visible)
    +    +    -- New `.compose-overlay-backdrop` (translucent + blur)
    +    +    -- New `.compose-narrator` (centered flex column, 520px max width)
    +    +    -- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
    +    +    -- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")
    +    +    -
    +    +    -### web/src/main.ts
    +    +    -- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
    +    +    -- 6├ö├Â┬úÔö£Ôòú `HTMLInputElement` Ôö£├ÂÔö£├æÔö£├Ñ `HTMLTextAreaElement` for `#duet-input`
    +    +    -- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
    +    +    -- `showFloatingComposer()`: redirects to `showComposeOverlay()`
    +    +    -- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
    +    +    -- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
    +    +    -- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap
    +    +    +## Minimal Diff Hunks
    +    +    +    (none)
    +    +     
    +    +     ## Verification
    +    +    -- Static: `tsc --noEmit` Ôö£├ÂÔö£├ºÔö£├é 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
    +    +    -- Static: `tsc -p tsconfig.json --noCheck` Ôö£├ÂÔö£├ºÔö£├é build emits successfully
    +    +    -- Runtime: pytest 183 passed, 1 warning in 114.43s
    +    +    -- Runtime: node ui_onboarding_hints_test.mjs Ôö£├ÂÔö£├ºÔö£├é 17/17 PASS
    +    +    -- Runtime: node ui_proposal_renderer_test.mjs Ôö£├ÂÔö£├ºÔö£├é 3/3 PASS
    +    +    -- Contract: physics.yaml unchanged; minimal diff; no refactors
    +    +    +- TODO: verification evidence (static -> runtime -> behavior -> contract).
    +    +     
    +    +    -## Behavioral Design Notes
    +    +    -- Triple-tap on `.duet-stage` Ôö£├ÂÔö£├æÔö£├Ñ `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
    +    +    -- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
    +    +    -- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` Ôö£├ÂÔö£├æÔö£├Ñ sends, clears, hides overlay
    +    +    -- Double-tap uses `pointerdown` on backdrop only Ôö£├ÂÔö£├ºÔö£├é cannot fire during text selection inside input
    +    +    -- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
    +    +    -- Shell (`#duet-shell`) is never repositioned Ôö£├ÂÔö£├ºÔö£├é only the narrator overlay adjusts
    +    +    -- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur
    +    +    +## Notes (optional)
    +    +    +- TODO: blockers, risks, constraints.
    +    +     
    +    +     ## Next Steps
    +    +    -- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
    +    +    -- Phase 6C: Render deployment + smoke tests
    +    +    -- Future cycle: mic button / STT live transcription
    +    +    +- TODO: next actions (small, specific).
    +    +     
    +    +    diff --git a/web/dist/main.js b/web/dist/main.js
    +    +    index 18ca797..92f9e81 100644
    +    +    --- a/web/dist/main.js
    +    +    +++ b/web/dist/main.js
    +    +    @@ -2112,6 +2112,14 @@ function ensureComposeOverlay() {
    +    +         const backdrop = document.createElement("div");
    +    +         backdrop.className = "compose-overlay-backdrop";
    +    +         overlay.appendChild(backdrop);
    +    +    +    // Close button inside overlay (above backdrop, always clickable)
    +    +    +    const closeBtn = document.createElement("button");
    +    +    +    closeBtn.type = "button";
    +    +    +    closeBtn.className = "compose-close-btn";
    +    +    +    closeBtn.textContent = "\u2715";
    +    +    +    closeBtn.setAttribute("aria-label", "Close composer");
    +    +    +    closeBtn.addEventListener("click", () => hideComposeOverlay());
    +    +    +    overlay.appendChild(closeBtn);
    +    +         const narrator = document.createElement("div");
    +    +         narrator.className = "compose-narrator";
    +    +         overlay.appendChild(narrator);
    +    +    @@ -2290,20 +2298,16 @@ function syncFlowMenuVisibility() {
    +    +             return;
    +    +         const trigger = document.getElementById("flow-menu-trigger");
    +    +         if (composerVisible) {
    +    +    -        // Show trigger as a red Ôö£├ÂÔö¼├║Ôö£Ôûô close button instead of hiding it
    +    +    -        flowMenuContainer.classList.remove("hidden");
    +    +    -        if (trigger) {
    +    +    -            trigger.classList.add("close-mode");
    +    +    -            trigger.textContent = "Ôö£├ÂÔö¼├║Ôö£Ôûô";
    +    +    -            trigger.setAttribute("aria-label", "Close composer");
    +    +    -        }
    +    +    -        // Hide the dropdown while in close mode
    +    +    +        // Hide the flow-menu trigger (compose overlay has its own close button)
    +    +    +        flowMenuContainer.classList.add("hidden");
    +    +    +        // Hide the dropdown while in compose mode
    +    +             if (flowMenuDropdown) {
    +    +                 flowMenuDropdown.style.display = "none";
    +    +                 flowMenuDropdown.classList.remove("open");
    +    +             }
    +    +         }
    +    +         else {
    +    +    +        flowMenuContainer.classList.remove("hidden");
    +    +             if (trigger) {
    +    +                 trigger.classList.remove("close-mode");
    +    +                 trigger.textContent = "Ôö£├ÂÔö£┬úÔö£├╗";
    +    +    diff --git a/web/dist/style.css b/web/dist/style.css
    +    +    index a94e659..0ff97ac 100644
    +    +    --- a/web/dist/style.css
    +    +    +++ b/web/dist/style.css
    +    +    @@ -275,6 +275,32 @@ pre {
    +    +       transform: translateY(-1px);
    +    +     }
    +    +     
    +    +    +/* Close button inside compose overlay */
    +    +    +.compose-close-btn {
    +    +    +  position: absolute;
    +    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +    +    +  right: 22px;
    +    +    +  z-index: 2;
    +    +    +  width: 46px;
    +    +    +  height: 46px;
    +    +    +  border-radius: 12px;
    +    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    +    +    +  background: rgba(220, 38, 38, 0.85);
    +    +    +  color: #fff;
    +    +    +  font-size: 18px;
    +    +    +  font-weight: 700;
    +    +    +  display: inline-flex;
    +    +    +  align-items: center;
    +    +    +  justify-content: center;
    +    +    +  cursor: pointer;
    +    +    +  box-shadow: var(--shadow);
    +    +    +  transition: background 120ms ease;
    +    +    +}
    +    +    +
    +    +    +.compose-close-btn:hover {
    +    +    +  background: rgba(239, 68, 68, 1);
    +    +    +}
    +    +    +
    +    +     .flow-menu-dropdown {
    +    +       position: absolute;
    +    +       top: calc(100% + 6px);
    +    +    @@ -802,9 +828,7 @@ pre {
    +    +     .compose-overlay-backdrop {
    +    +       position: absolute;
    +    +       inset: 0;
    +    +    -  background: rgba(5, 12, 20, 0.45);
    +    +    -  backdrop-filter: blur(6px);
    +    +    -  -webkit-backdrop-filter: blur(6px);
    +    +    +  background: rgba(5, 12, 20, 0.18);
    +    +     }
    +    +     
    +    +     .compose-narrator {
    +    +    diff --git a/web/src/main.ts b/web/src/main.ts
    +    +    index dc4ec82..756b656 100644
    +    +    --- a/web/src/main.ts
    +    +    +++ b/web/src/main.ts
    +    +    @@ -2218,6 +2218,15 @@ function ensureComposeOverlay(): HTMLDivElement {
    +    +       backdrop.className = "compose-overlay-backdrop";
    +    +       overlay.appendChild(backdrop);
    +    +     
    +    +    +  // Close button inside overlay (above backdrop, always clickable)
    +    +    +  const closeBtn = document.createElement("button");
    +    +    +  closeBtn.type = "button";
    +    +    +  closeBtn.className = "compose-close-btn";
    +    +    +  closeBtn.textContent = "\u2715";
    +    +    +  closeBtn.setAttribute("aria-label", "Close composer");
    +    +    +  closeBtn.addEventListener("click", () => hideComposeOverlay());
    +    +    +  overlay.appendChild(closeBtn);
    +    +    +
    +    +       const narrator = document.createElement("div");
    +    +       narrator.className = "compose-narrator";
    +    +       overlay.appendChild(narrator);
    +    +    @@ -2397,19 +2406,15 @@ function syncFlowMenuVisibility() {
    +    +       if (!flowMenuContainer) return;
    +    +       const trigger = document.getElementById("flow-menu-trigger");
    +    +       if (composerVisible) {
    +    +    -    // Show trigger as a red Ôö£├ÂÔö¼├║Ôö£Ôûô close button instead of hiding it
    +    +    -    flowMenuContainer.classList.remove("hidden");
    +    +    -    if (trigger) {
    +    +    -      trigger.classList.add("close-mode");
    +    +    -      trigger.textContent = "Ôö£├ÂÔö¼├║Ôö£Ôûô";
    +    +    -      trigger.setAttribute("aria-label", "Close composer");
    +    +    -    }
    +    +    -    // Hide the dropdown while in close mode
    +    +    +    // Hide the flow-menu trigger (compose overlay has its own close button)
    +    +    +    flowMenuContainer.classList.add("hidden");
    +    +    +    // Hide the dropdown while in compose mode
    +    +         if (flowMenuDropdown) {
    +    +           flowMenuDropdown.style.display = "none";
    +    +           flowMenuDropdown.classList.remove("open");
    +    +         }
    +    +       } else {
    +    +    +    flowMenuContainer.classList.remove("hidden");
    +    +         if (trigger) {
    +    +           trigger.classList.remove("close-mode");
    +    +           trigger.textContent = "Ôö£├ÂÔö£┬úÔö£├╗";
    +    +    diff --git a/web/src/style.css b/web/src/style.css
    +    +    index a94e659..0ff97ac 100644
    +    +    --- a/web/src/style.css
    +    +    +++ b/web/src/style.css
    +    +    @@ -275,6 +275,32 @@ pre {
    +    +       transform: translateY(-1px);
    +    +     }
    +    +     
    +    +    +/* Close button inside compose overlay */
    +    +    +.compose-close-btn {
    +    +    +  position: absolute;
    +    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +    +    +  right: 22px;
    +    +    +  z-index: 2;
    +    +    +  width: 46px;
    +    +    +  height: 46px;
    +    +    +  border-radius: 12px;
    +    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    +    +    +  background: rgba(220, 38, 38, 0.85);
    +    +    +  color: #fff;
    +    +    +  font-size: 18px;
    +    +    +  font-weight: 700;
    +    +    +  display: inline-flex;
    +    +    +  align-items: center;
    +    +    +  justify-content: center;
    +    +    +  cursor: pointer;
    +    +    +  box-shadow: var(--shadow);
    +    +    +  transition: background 120ms ease;
    +    +    +}
    +    +    +
    +    +    +.compose-close-btn:hover {
    +    +    +  background: rgba(239, 68, 68, 1);
    +    +    +}
    +    +    +
    +    +     .flow-menu-dropdown {
    +    +       position: absolute;
    +    +       top: calc(100% + 6px);
    +    +    @@ -802,9 +828,7 @@ pre {
    +    +     .compose-overlay-backdrop {
    +    +       position: absolute;
    +    +       inset: 0;
    +    +    -  background: rgba(5, 12, 20, 0.45);
    +    +    -  backdrop-filter: blur(6px);
    +    +    -  -webkit-backdrop-filter: blur(6px);
    +    +    +  background: rgba(5, 12, 20, 0.18);
    +    +     }
    +    +     
    +    +     .compose-narrator {
    +     
    +     ## Verification
    +    -- Static: `tsc --noEmit` ├ö├ç├Â 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
    +    +- Static: `tsc --noEmit` ├ö├ç├Â 1 pre-existing TS2339 (line 1174 `item.location`), no new errors
    +     - Static: `tsc -p tsconfig.json --noCheck` ├ö├ç├Â build emits successfully
    +    -- Runtime: pytest 183 passed, 1 warning in 114.43s
    +    +- Runtime: pytest 183 passed, 1 warning in 114.30s
    +     - Runtime: node ui_onboarding_hints_test.mjs ├ö├ç├Â 17/17 PASS
    +     - Runtime: node ui_proposal_renderer_test.mjs ├ö├ç├Â 3/3 PASS
    +     - Contract: physics.yaml unchanged; minimal diff; no refactors
    +     
    +    -## Behavioral Design Notes
    +    -- Triple-tap on `.duet-stage` ├ö├Ñ├å `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
    +    -- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
    +    -- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` ├ö├Ñ├å sends, clears, hides overlay
    +    -- Double-tap uses `pointerdown` on backdrop only ├ö├ç├Â cannot fire during text selection inside input
    +    -- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
    +    -- Shell (`#duet-shell`) is never repositioned ├ö├ç├Â only the narrator overlay adjusts
    +    -- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur
    +    +## Notes
    +    +- Root cause: `.duet-shell` has `backdrop-filter: blur(10px)` (style.css L65) which creates a stacking context. Even `position: fixed; z-index: 110` on a child cannot escape it. Compose overlay at z-index 100 on body always wins.
    +     
    +     ## Next Steps
    +    -- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
    +    +- Physical iPhone Safari testing: confirm ├ö┬ú├▓ clickable, blur readable, double-tap send works
    +     - Phase 6C: Render deployment + smoke tests
    +    -- Future cycle: mic button / STT live transcription
    +     
    +    diff --git a/web/dist/main.js b/web/dist/main.js
    +    index 18ca797..4cde744 100644
    +    --- a/web/dist/main.js
    +    +++ b/web/dist/main.js
    +    @@ -2112,6 +2112,14 @@ function ensureComposeOverlay() {
    +         const backdrop = document.createElement("div");
    +         backdrop.className = "compose-overlay-backdrop";
    +         overlay.appendChild(backdrop);
    +    +    // Close button inside overlay (above backdrop, always clickable)
    +    +    const closeBtn = document.createElement("button");
    +    +    closeBtn.type = "button";
    +    +    closeBtn.className = "compose-close-btn";
    +    +    closeBtn.textContent = "\u2715";
    +    +    closeBtn.setAttribute("aria-label", "Close composer");
    +    +    closeBtn.addEventListener("click", () => hideComposeOverlay());
    +    +    overlay.appendChild(closeBtn);
    +         const narrator = document.createElement("div");
    +         narrator.className = "compose-narrator";
    +         overlay.appendChild(narrator);
    +    @@ -2173,6 +2181,14 @@ function showComposeOverlay() {
    +         // Move input into narrator container
    +         const narrator = overlay.querySelector(".compose-narrator");
    +         narrator.insertBefore(input, narrator.firstChild);
    +    +    // Position close button to match original flow-menu-trigger location
    +    +    const fmTrigger = document.getElementById("flow-menu-trigger");
    +    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    +    +    if (fmTrigger && closeBtn) {
    +    +        const rect = fmTrigger.getBoundingClientRect();
    +    +        closeBtn.style.top = rect.top + "px";
    +    +        closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    +    }
    +         overlay.classList.add("active");
    +         composeActive = true;
    +         composerVisible = true;
    +    @@ -2208,6 +2224,12 @@ function hideComposeOverlay() {
    +                 composer.appendChild(input);
    +             }
    +         }
    +    +    // Clear inline positioning from compose-close-btn
    +    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    +    +    if (closeBtn) {
    +    +        closeBtn.style.top = "";
    +    +        closeBtn.style.right = "";
    +    +    }
    +         overlay.classList.remove("active");
    +         composeActive = false;
    +         composerVisible = false;
    +    @@ -2290,20 +2312,16 @@ function syncFlowMenuVisibility() {
    +             return;
    +         const trigger = document.getElementById("flow-menu-trigger");
    +         if (composerVisible) {
    +    -        // Show trigger as a red ├ö┬ú├▓ close button instead of hiding it
    +    -        flowMenuContainer.classList.remove("hidden");
    +    -        if (trigger) {
    +    -            trigger.classList.add("close-mode");
    +    -            trigger.textContent = "├ö┬ú├▓";
    +    -            trigger.setAttribute("aria-label", "Close composer");
    +    -        }
    +    -        // Hide the dropdown while in close mode
    +    +        // Hide the flow-menu trigger (compose overlay has its own close button)
    +    +        flowMenuContainer.classList.add("hidden");
    +    +        // Hide the dropdown while in compose mode
    +             if (flowMenuDropdown) {
    +                 flowMenuDropdown.style.display = "none";
    +                 flowMenuDropdown.classList.remove("open");
    +             }
    +         }
    +         else {
    +    +        flowMenuContainer.classList.remove("hidden");
    +             if (trigger) {
    +                 trigger.classList.remove("close-mode");
    +                 trigger.textContent = "├ö├£├û";
    +    diff --git a/web/dist/style.css b/web/dist/style.css
    +    index a94e659..9f2258c 100644
    +    --- a/web/dist/style.css
    +    +++ b/web/dist/style.css
    +    @@ -275,6 +275,32 @@ pre {
    +       transform: translateY(-1px);
    +     }
    +     
    +    +/* Close button inside compose overlay */
    +    +.compose-close-btn {
    +    +  position: absolute;
    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +    +  right: 22px;
    +    +  z-index: 2;
    +    +  width: 46px;
    +    +  height: 46px;
    +    +  border-radius: 12px;
    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    +    +  background: rgba(220, 38, 38, 0.85);
    +    +  color: #fff;
    +    +  font-size: 18px;
    +    +  font-weight: 700;
    +    +  display: inline-flex;
    +    +  align-items: center;
    +    +  justify-content: center;
    +    +  cursor: pointer;
    +    +  box-shadow: var(--shadow);
    +    +  transition: background 120ms ease;
    +    +}
    +    +
    +    +.compose-close-btn:hover {
    +    +  background: rgba(239, 68, 68, 1);
    +    +}
    +    +
    +     .flow-menu-dropdown {
    +       position: absolute;
    +       top: calc(100% + 6px);
    +    @@ -802,9 +828,9 @@ pre {
    +     .compose-overlay-backdrop {
    +       position: absolute;
    +       inset: 0;
    +    -  background: rgba(5, 12, 20, 0.45);
    +    -  backdrop-filter: blur(6px);
    +    -  -webkit-backdrop-filter: blur(6px);
    +    +  background: rgba(5, 12, 20, 0.18);
    +    +  backdrop-filter: blur(2px);
    +    +  -webkit-backdrop-filter: blur(2px);
    +     }
    +     
    +     .compose-narrator {
    +    diff --git a/web/src/main.ts b/web/src/main.ts
    +    index dc4ec82..4e8a831 100644
    +    --- a/web/src/main.ts
    +    +++ b/web/src/main.ts
    +    @@ -2218,6 +2218,15 @@ function ensureComposeOverlay(): HTMLDivElement {
    +       backdrop.className = "compose-overlay-backdrop";
    +       overlay.appendChild(backdrop);
    +     
    +    +  // Close button inside overlay (above backdrop, always clickable)
    +    +  const closeBtn = document.createElement("button");
    +    +  closeBtn.type = "button";
    +    +  closeBtn.className = "compose-close-btn";
    +    +  closeBtn.textContent = "\u2715";
    +    +  closeBtn.setAttribute("aria-label", "Close composer");
    +    +  closeBtn.addEventListener("click", () => hideComposeOverlay());
    +    +  overlay.appendChild(closeBtn);
    +    +
    +       const narrator = document.createElement("div");
    +       narrator.className = "compose-narrator";
    +       overlay.appendChild(narrator);
    +    @@ -2283,6 +2292,15 @@ function showComposeOverlay() {
    +       const narrator = overlay.querySelector(".compose-narrator") as HTMLElement;
    +       narrator.insertBefore(input, narrator.firstChild);
    +     
    +    +  // Position close button to match original flow-menu-trigger location
    +    +  const fmTrigger = document.getElementById("flow-menu-trigger");
    +    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    +    +  if (fmTrigger && closeBtn) {
    +    +    const rect = fmTrigger.getBoundingClientRect();
    +    +    closeBtn.style.top = rect.top + "px";
    +    +    closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    +  }
    +    +
    +       overlay.classList.add("active");
    +       composeActive = true;
    +       composerVisible = true;
    +    @@ -2320,6 +2338,13 @@ function hideComposeOverlay() {
    +         }
    +       }
    +     
    +    +  // Clear inline positioning from compose-close-btn
    +    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    +    +  if (closeBtn) {
    +    +    closeBtn.style.top = "";
    +    +    closeBtn.style.right = "";
    +    +  }
    +    +
    +       overlay.classList.remove("active");
    +       composeActive = false;
    +       composerVisible = false;
    +    @@ -2397,19 +2422,15 @@ function syncFlowMenuVisibility() {
    +       if (!flowMenuContainer) return;
    +       const trigger = document.getElementById("flow-menu-trigger");
    +       if (composerVisible) {
    +    -    // Show trigger as a red ├ö┬ú├▓ close button instead of hiding it
    +    -    flowMenuContainer.classList.remove("hidden");
    +    -    if (trigger) {
    +    -      trigger.classList.add("close-mode");
    +    -      trigger.textContent = "├ö┬ú├▓";
    +    -      trigger.setAttribute("aria-label", "Close composer");
    +    -    }
    +    -    // Hide the dropdown while in close mode
    +    +    // Hide the flow-menu trigger (compose overlay has its own close button)
    +    +    flowMenuContainer.classList.add("hidden");
    +    +    // Hide the dropdown while in compose mode
    +         if (flowMenuDropdown) {
    +           flowMenuDropdown.style.display = "none";
    +           flowMenuDropdown.classList.remove("open");
    +         }
    +       } else {
    +    +    flowMenuContainer.classList.remove("hidden");
    +         if (trigger) {
    +           trigger.classList.remove("close-mode");
    +           trigger.textContent = "├ö├£├û";
    +    diff --git a/web/src/style.css b/web/src/style.css
    +    index a94e659..9f2258c 100644
    +    --- a/web/src/style.css
    +    +++ b/web/src/style.css
    +    @@ -275,6 +275,32 @@ pre {
    +       transform: translateY(-1px);
    +     }
    +     
    +    +/* Close button inside compose overlay */
    +    +.compose-close-btn {
    +    +  position: absolute;
    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +    +  right: 22px;
    +    +  z-index: 2;
    +    +  width: 46px;
    +    +  height: 46px;
    +    +  border-radius: 12px;
    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    +    +  background: rgba(220, 38, 38, 0.85);
    +    +  color: #fff;
    +    +  font-size: 18px;
    +    +  font-weight: 700;
    +    +  display: inline-flex;
    +    +  align-items: center;
    +    +  justify-content: center;
    +    +  cursor: pointer;
    +    +  box-shadow: var(--shadow);
    +    +  transition: background 120ms ease;
    +    +}
    +    +
    +    +.compose-close-btn:hover {
    +    +  background: rgba(239, 68, 68, 1);
    +    +}
    +    +
    +     .flow-menu-dropdown {
    +       position: absolute;
    +       top: calc(100% + 6px);
    +    @@ -802,9 +828,9 @@ pre {
    +     .compose-overlay-backdrop {
    +       position: absolute;
    +       inset: 0;
    +    -  background: rgba(5, 12, 20, 0.45);
    +    -  backdrop-filter: blur(6px);
    +    -  -webkit-backdrop-filter: blur(6px);
    +    +  background: rgba(5, 12, 20, 0.18);
    +    +  backdrop-filter: blur(2px);
    +    +  -webkit-backdrop-filter: blur(2px);
    +     }
    +     
    +     .compose-narrator {
     
     ## Verification
    -- Static: `tsc --noEmit` ÔÇö 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
    +- Static: `tsc --noEmit` ÔÇö 1 pre-existing TS2339 (line 1174 `item.location`), no new errors
     - Static: `tsc -p tsconfig.json --noCheck` ÔÇö build emits successfully
    -- Runtime: pytest 183 passed, 1 warning in 114.43s
    +- Runtime: pytest 183 passed, 1 warning in 114.58s
     - Runtime: node ui_onboarding_hints_test.mjs ÔÇö 17/17 PASS
     - Runtime: node ui_proposal_renderer_test.mjs ÔÇö 3/3 PASS
     - Contract: physics.yaml unchanged; minimal diff; no refactors
     
    -## Behavioral Design Notes
    -- Triple-tap on `.duet-stage` ÔåÆ `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
    -- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
    -- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` ÔåÆ sends, clears, hides overlay
    -- Double-tap uses `pointerdown` on backdrop only ÔÇö cannot fire during text selection inside input
    -- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
    -- Shell (`#duet-shell`) is never repositioned ÔÇö only the narrator overlay adjusts
    -- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur
    +## Notes
    +- Original X: `.flow-menu` at `position: absolute; top: 90px; right: 22px` inside `.duet-shell` (relative). New `.compose-close-btn` is inside `.compose-overlay` (fixed inset:0 on body). Using `getBoundingClientRect()` maps the original's viewport position onto the overlay's coordinate space exactly.
     
     ## Next Steps
    -- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
    +- Physical iPhone Safari testing: confirm blur subtle, X position matches original, double-tap send works
     - Phase 6C: Render deployment + smoke tests
    -- Future cycle: mic button / STT live transcription
     
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 18ca797..4cde744 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -2112,6 +2112,14 @@ function ensureComposeOverlay() {
         const backdrop = document.createElement("div");
         backdrop.className = "compose-overlay-backdrop";
         overlay.appendChild(backdrop);
    +    // Close button inside overlay (above backdrop, always clickable)
    +    const closeBtn = document.createElement("button");
    +    closeBtn.type = "button";
    +    closeBtn.className = "compose-close-btn";
    +    closeBtn.textContent = "\u2715";
    +    closeBtn.setAttribute("aria-label", "Close composer");
    +    closeBtn.addEventListener("click", () => hideComposeOverlay());
    +    overlay.appendChild(closeBtn);
         const narrator = document.createElement("div");
         narrator.className = "compose-narrator";
         overlay.appendChild(narrator);
    @@ -2173,6 +2181,14 @@ function showComposeOverlay() {
         // Move input into narrator container
         const narrator = overlay.querySelector(".compose-narrator");
         narrator.insertBefore(input, narrator.firstChild);
    +    // Position close button to match original flow-menu-trigger location
    +    const fmTrigger = document.getElementById("flow-menu-trigger");
    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    +    if (fmTrigger && closeBtn) {
    +        const rect = fmTrigger.getBoundingClientRect();
    +        closeBtn.style.top = rect.top + "px";
    +        closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    }
         overlay.classList.add("active");
         composeActive = true;
         composerVisible = true;
    @@ -2208,6 +2224,12 @@ function hideComposeOverlay() {
                 composer.appendChild(input);
             }
         }
    +    // Clear inline positioning from compose-close-btn
    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    +    if (closeBtn) {
    +        closeBtn.style.top = "";
    +        closeBtn.style.right = "";
    +    }
         overlay.classList.remove("active");
         composeActive = false;
         composerVisible = false;
    @@ -2290,20 +2312,16 @@ function syncFlowMenuVisibility() {
             return;
         const trigger = document.getElementById("flow-menu-trigger");
         if (composerVisible) {
    -        // Show trigger as a red Ô£ò close button instead of hiding it
    -        flowMenuContainer.classList.remove("hidden");
    -        if (trigger) {
    -            trigger.classList.add("close-mode");
    -            trigger.textContent = "Ô£ò";
    -            trigger.setAttribute("aria-label", "Close composer");
    -        }
    -        // Hide the dropdown while in close mode
    +        // Hide the flow-menu trigger (compose overlay has its own close button)
    +        flowMenuContainer.classList.add("hidden");
    +        // Hide the dropdown while in compose mode
             if (flowMenuDropdown) {
                 flowMenuDropdown.style.display = "none";
                 flowMenuDropdown.classList.remove("open");
             }
         }
         else {
    +        flowMenuContainer.classList.remove("hidden");
             if (trigger) {
                 trigger.classList.remove("close-mode");
                 trigger.textContent = "ÔÜÖ";
    diff --git a/web/dist/style.css b/web/dist/style.css
    index a94e659..08e5f8c 100644
    --- a/web/dist/style.css
    +++ b/web/dist/style.css
    @@ -275,6 +275,33 @@ pre {
       transform: translateY(-1px);
     }
     
    +/* Close button inside compose overlay */
    +.compose-close-btn {
    +  position: absolute;
    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +  right: 22px;
    +  z-index: 2;
    +  margin: 0;
    +  width: 46px;
    +  height: 46px;
    +  border-radius: 12px;
    +  border: 1px solid rgba(248, 113, 113, 0.5);
    +  background: rgba(220, 38, 38, 0.85);
    +  color: #fff;
    +  font-size: 18px;
    +  font-weight: 700;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  cursor: pointer;
    +  box-shadow: var(--shadow);
    +  transition: background 120ms ease;
    +}
    +
    +.compose-close-btn:hover {
    +  background: rgba(239, 68, 68, 1);
    +}
    +
     .flow-menu-dropdown {
       position: absolute;
       top: calc(100% + 6px);
    @@ -802,9 +829,9 @@ pre {
     .compose-overlay-backdrop {
       position: absolute;
       inset: 0;
    -  background: rgba(5, 12, 20, 0.45);
    -  backdrop-filter: blur(6px);
    -  -webkit-backdrop-filter: blur(6px);
    +  background: rgba(5, 12, 20, 0.18);
    +  backdrop-filter: blur(2px);
    +  -webkit-backdrop-filter: blur(2px);
     }
     
     .compose-narrator {
    diff --git a/web/src/main.ts b/web/src/main.ts
    index dc4ec82..4e8a831 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -2218,6 +2218,15 @@ function ensureComposeOverlay(): HTMLDivElement {
       backdrop.className = "compose-overlay-backdrop";
       overlay.appendChild(backdrop);
     
    +  // Close button inside overlay (above backdrop, always clickable)
    +  const closeBtn = document.createElement("button");
    +  closeBtn.type = "button";
    +  closeBtn.className = "compose-close-btn";
    +  closeBtn.textContent = "\u2715";
    +  closeBtn.setAttribute("aria-label", "Close composer");
    +  closeBtn.addEventListener("click", () => hideComposeOverlay());
    +  overlay.appendChild(closeBtn);
    +
       const narrator = document.createElement("div");
       narrator.className = "compose-narrator";
       overlay.appendChild(narrator);
    @@ -2283,6 +2292,15 @@ function showComposeOverlay() {
       const narrator = overlay.querySelector(".compose-narrator") as HTMLElement;
       narrator.insertBefore(input, narrator.firstChild);
     
    +  // Position close button to match original flow-menu-trigger location
    +  const fmTrigger = document.getElementById("flow-menu-trigger");
    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    +  if (fmTrigger && closeBtn) {
    +    const rect = fmTrigger.getBoundingClientRect();
    +    closeBtn.style.top = rect.top + "px";
    +    closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +  }
    +
       overlay.classList.add("active");
       composeActive = true;
       composerVisible = true;
    @@ -2320,6 +2338,13 @@ function hideComposeOverlay() {
         }
       }
     
    +  // Clear inline positioning from compose-close-btn
    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    +  if (closeBtn) {
    +    closeBtn.style.top = "";
    +    closeBtn.style.right = "";
    +  }
    +
       overlay.classList.remove("active");
       composeActive = false;
       composerVisible = false;
    @@ -2397,19 +2422,15 @@ function syncFlowMenuVisibility() {
       if (!flowMenuContainer) return;
       const trigger = document.getElementById("flow-menu-trigger");
       if (composerVisible) {
    -    // Show trigger as a red Ô£ò close button instead of hiding it
    -    flowMenuContainer.classList.remove("hidden");
    -    if (trigger) {
    -      trigger.classList.add("close-mode");
    -      trigger.textContent = "Ô£ò";
    -      trigger.setAttribute("aria-label", "Close composer");
    -    }
    -    // Hide the dropdown while in close mode
    +    // Hide the flow-menu trigger (compose overlay has its own close button)
    +    flowMenuContainer.classList.add("hidden");
    +    // Hide the dropdown while in compose mode
         if (flowMenuDropdown) {
           flowMenuDropdown.style.display = "none";
           flowMenuDropdown.classList.remove("open");
         }
       } else {
    +    flowMenuContainer.classList.remove("hidden");
         if (trigger) {
           trigger.classList.remove("close-mode");
           trigger.textContent = "ÔÜÖ";
    diff --git a/web/src/style.css b/web/src/style.css
    index a94e659..08e5f8c 100644
    --- a/web/src/style.css
    +++ b/web/src/style.css
    @@ -275,6 +275,33 @@ pre {
       transform: translateY(-1px);
     }
     
    +/* Close button inside compose overlay */
    +.compose-close-btn {
    +  position: absolute;
    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +  right: 22px;
    +  z-index: 2;
    +  margin: 0;
    +  width: 46px;
    +  height: 46px;
    +  border-radius: 12px;
    +  border: 1px solid rgba(248, 113, 113, 0.5);
    +  background: rgba(220, 38, 38, 0.85);
    +  color: #fff;
    +  font-size: 18px;
    +  font-weight: 700;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  cursor: pointer;
    +  box-shadow: var(--shadow);
    +  transition: background 120ms ease;
    +}
    +
    +.compose-close-btn:hover {
    +  background: rgba(239, 68, 68, 1);
    +}
    +
     .flow-menu-dropdown {
       position: absolute;
       top: calc(100% + 6px);
    @@ -802,9 +829,9 @@ pre {
     .compose-overlay-backdrop {
       position: absolute;
       inset: 0;
    -  background: rgba(5, 12, 20, 0.45);
    -  backdrop-filter: blur(6px);
    -  -webkit-backdrop-filter: blur(6px);
    +  background: rgba(5, 12, 20, 0.18);
    +  backdrop-filter: blur(2px);
    +  -webkit-backdrop-filter: blur(2px);
     }
     
     .compose-narrator {

## Verification
- Static: `tsc --noEmit` — 1 pre-existing TS2339 (line 1174), no new errors
- Runtime: pytest 183 passed, 1 warning in 114.07s
- Runtime: node ui_onboarding_hints_test.mjs — 17/17 PASS
- Runtime: node ui_proposal_renderer_test.mjs — 3/3 PASS
- Contract: physics.yaml unchanged; 1 CSS property added; no refactors

## Notes
- Global rule `button { margin-top: 6px }` at style.css L180 affects all `<button>` elements. `.flow-menu-toggle` also inherits this margin but `getBoundingClientRect()` captures its actual rendered position (post-margin), so the rect is accurate. The fix ensures `.compose-close-btn`'s margin-box matches its border-box.

## Next Steps
- Physical iPhone Safari testing: confirm close button pixel-aligned with gear button
- Phase 6C: Render deployment + smoke tests

