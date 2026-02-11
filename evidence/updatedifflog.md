# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T18:45:00+00:00
- Branch: claude/romantic-jones
- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
- Diff basis: unstaged

## Cycle Status
- Status: COMPLETE

## Summary
- Replaced composer UX with centered "ghost narrator" input overlay.
- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
- Textarea auto-expands vertically as user types (up to max-height).
- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
- No borders/box/chrome on the centered input — ghost narrator styling.
- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.

## Files Changed (unstaged)
- web/index.html — `<input>` → `<textarea>` in composer
- web/src/main.ts — compose overlay logic, type updates, auto-expand, VisualViewport handler
- web/src/style.css — textarea styles, compose overlay CSS, narrator styling
- web/dist/index.html — `<input>` → `<textarea>` (built)
- web/dist/main.js — compiled output
- web/dist/style.css — compiled CSS
- evidence/updatedifflog.md — this file

## git status -sb
    ## claude/romantic-jones
     M .claude/settings.local.json
     M web/dist/index.html
     M web/dist/main.js
     M web/dist/style.css
     M web/index.html
     M web/src/main.ts
     M web/src/style.css

## Minimal Diff Hunks (source files only)

### web/index.html
- `<input id="duet-input" type="text" .../>` → `<textarea id="duet-input" rows="1" ...></textarea>`

### web/src/style.css
- `.duet-composer input` → `.duet-composer textarea`
- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
- New `.compose-overlay.active` (visible)
- New `.compose-overlay-backdrop` (translucent + blur)
- New `.compose-narrator` (centered flex column, 520px max width)
- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")

### web/src/main.ts
- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
- 6× `HTMLInputElement` → `HTMLTextAreaElement` for `#duet-input`
- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
- `showFloatingComposer()`: redirects to `showComposeOverlay()`
- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap

## Verification
- Static: `tsc --noEmit` — 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
- Static: `tsc -p tsconfig.json --noCheck` — build emits successfully
- Runtime: pytest 183 passed, 1 warning in 114.43s
- Runtime: node ui_onboarding_hints_test.mjs — 17/17 PASS
- Runtime: node ui_proposal_renderer_test.mjs — 3/3 PASS
- Contract: physics.yaml unchanged; minimal diff; no refactors

## Behavioral Design Notes
- Triple-tap on `.duet-stage` → `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` → sends, clears, hides overlay
- Double-tap uses `pointerdown` on backdrop only — cannot fire during text selection inside input
- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
- Shell (`#duet-shell`) is never repositioned — only the narrator overlay adjusts
- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur

## Next Steps
- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
- Phase 6C: Render deployment + smoke tests
- Future cycle: mic button / STT live transcription

