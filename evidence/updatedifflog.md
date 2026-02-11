# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T21:00:08+00:00
- Branch: claude/romantic-jones
- HEAD: 33cf566b25aef9043ec7d5bdecc32e00d4d9cc89
- BASE_HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Swapped compose overlay button positions: Mic now occupies the X (close) button's old position (aligned to `#flow-menu-trigger`), X now occupies the history toggle's position (aligned to `#duet-history-toggle`).
- JS: `showComposeOverlay()` reads `getBoundingClientRect()` from `#duet-history-toggle` for close btn, and from `#flow-menu-trigger` for mic btn.
- CSS fallback tops updated: `.compose-close-btn` top → `max(32px, ...)`, `.compose-mic-btn` top → `max(90px, ...)`.
- No behavior changes — dictation, send, close, blur all unchanged.

## Files Changed (staged)
- evidence/updatedifflog.md
- web/dist/main.js
- web/dist/style.css
- web/src/main.ts
- web/src/style.css

## git status -sb
    ## claude/romantic-jones...origin/claude/romantic-jones
     M .claude/settings.local.json
    M  evidence/updatedifflog.md
    M  web/dist/main.js
    M  web/dist/style.css
    M  web/src/main.ts
    M  web/src/style.css

## Minimal Diff Hunks
    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    index 0686aef..9990433 100644
    --- a/evidence/updatedifflog.md
    +++ b/evidence/updatedifflog.md
    @@ -1,1070 +1,552 @@
     ´╗┐# Diff Log (overwrite each cycle)
     
     ## Cycle Metadata
    -- Timestamp: 2026-02-11T19:59:41+00:00
    +- Timestamp: 2026-02-11T20:14:32+00:00
     - Branch: claude/romantic-jones
    -- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    -- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    +- HEAD: 33cf566b25aef9043ec7d5bdecc32e00d4d9cc89
    +- BASE_HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
     - Diff basis: staged
     
     ## Cycle Status
     - Status: COMPLETE
     
     ## Summary
    -- Added `margin: 0` to `.compose-close-btn` in CSS to override the inherited global `button { margin-top: 6px }` rule.
    -- Root cause: `getBoundingClientRect()` returns the trigger's border-box position, but CSS `top` on `.compose-close-btn` positions the margin-box edge. The inherited 6px margin-top pushed the close button 6px lower than the trigger.
    -- No blur, layering, or JS changes. CSS-only fix (1 property added in src + dist).
    +- Enhanced compose mode auto-focus: `showComposeOverlay()` now calls `input.setSelectionRange()` after focus to place caret at end and trigger keyboard on iOS.
    +- Added `.compose-mic-btn` (­ƒÄñ) inside compose overlay, positioned just below the close button, same coordinate scheme via `getBoundingClientRect()`.
    +- Implemented Web Speech API dictation (SpeechRecognition/webkitSpeechRecognition): tap mic to start, interim results update the centered textarea live, tap mic again or single-tap backdrop to stop.
    +- Dictation automatically stops on: X close, double-tap send, or backdrop single-tap.
    +- Graceful fallback: if SpeechRecognition unavailable, shows status message and disables mic.
    +- Recording state indicated by red pulsing `.recording` class on mic button.
    +- No blur, layering, or X positioning changes.
     
     ## Files Changed (staged)
    -- evidence/updatedifflog.md
     - web/dist/main.js
     - web/dist/style.css
     - web/src/main.ts
     - web/src/style.css
     
     ## git status -sb
    -    ## claude/romantic-jones
    +    ## claude/romantic-jones...origin/claude/romantic-jones
          M .claude/settings.local.json
    -    M  evidence/updatedifflog.md
         M  web/dist/main.js
         M  web/dist/style.css
         M  web/src/main.ts
         M  web/src/style.css
     
     ## Minimal Diff Hunks
    -    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    -    index 81ccc1e..bbaaa7d 100644
    -    --- a/evidence/updatedifflog.md
    -    +++ b/evidence/updatedifflog.md
    -    @@ -1,87 +1,707 @@
    -     ┬┤ÔòùÔöÉ# Diff Log (overwrite each cycle)
    -     
    -     ## Cycle Metadata
    -    -- Timestamp: 2026-02-11T18:45:00+00:00
    -    +- Timestamp: 2026-02-11T19:49:41+00:00
    -     - Branch: claude/romantic-jones
    -    -- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -    -- Diff basis: unstaged
    -    +- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    -    +- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -    +- Diff basis: staged
    -     
    -     ## Cycle Status
    -     - Status: COMPLETE
    -     
    -     ## Summary
    -    -- Replaced composer UX with centered "ghost narrator" input overlay.
    -    -- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
    -    -- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
    -    -- Textarea auto-expands vertically as user types (up to max-height).
    -    -- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
    -    -- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
    -    -- No borders/box/chrome on the centered input ├ö├ç├Â ghost narrator styling.
    -    -- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
    -    -- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.
    -    +- Restored subtle `backdrop-filter: blur(2px)` to `.compose-overlay-backdrop` (was removed entirely in cycle 3). Soft-focus effect, background remains readable.
    -    +- Fixed compose X button position to match original `.flow-menu-toggle` location: `showComposeOverlay()` now reads the flow-menu-trigger's `getBoundingClientRect()` and applies those coordinates as inline `top`/`right` on `.compose-close-btn`.
    -    +- `hideComposeOverlay()` clears inline positioning on the close button.
    -    +- No layout changes; X appears at exact same viewport position as the original gear/close button.
    -    +- CSS `.compose-close-btn` top/right kept as fallback for edge cases.
    -     
    -    -## Files Changed (unstaged)
    -    -- web/index.html ├ö├ç├Â `<input>` ├ö├Ñ├å `<textarea>` in composer
    -    -- web/src/main.ts ├ö├ç├Â compose overlay logic, type updates, auto-expand, VisualViewport handler
    -    -- web/src/style.css ├ö├ç├Â textarea styles, compose overlay CSS, narrator styling
    -    -- web/dist/index.html ├ö├ç├Â `<input>` ├ö├Ñ├å `<textarea>` (built)
    -    -- web/dist/main.js ├ö├ç├Â compiled output
    -    -- web/dist/style.css ├ö├ç├Â compiled CSS
    -    -- evidence/updatedifflog.md ├ö├ç├Â this file
    -    +## Files Changed (staged)
    -    +- evidence/updatedifflog.md
    -    +- web/dist/main.js
    -    +- web/dist/style.css
    -    +- web/src/main.ts
    -    +- web/src/style.css
    -     
    -     ## git status -sb
    -         ## claude/romantic-jones
    -          M .claude/settings.local.json
    -    -     M web/dist/index.html
    -    -     M web/dist/main.js
    -    -     M web/dist/style.css
    -    -     M web/index.html
    -    -     M web/src/main.ts
    -    -     M web/src/style.css
    -    +    M  evidence/updatedifflog.md
    -    +    M  web/dist/main.js
    -    +    M  web/dist/style.css
    -    +    M  web/src/main.ts
    -    +    M  web/src/style.css
    -     
    -    -## Minimal Diff Hunks (source files only)
    -    -
    -    -### web/index.html
    -    -- `<input id="duet-input" type="text" .../>` ├ö├Ñ├å `<textarea id="duet-input" rows="1" ...></textarea>`
    -    -
    -    -### web/src/style.css
    -    -- `.duet-composer input` ├ö├Ñ├å `.duet-composer textarea`
    -    -- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
    -    -- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
    -    -- New `.compose-overlay.active` (visible)
    -    -- New `.compose-overlay-backdrop` (translucent + blur)
    -    -- New `.compose-narrator` (centered flex column, 520px max width)
    -    -- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
    -    -- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")
    -    -
    -    -### web/src/main.ts
    -    -- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
    -    -- 6Ôö£├╣ `HTMLInputElement` ├ö├Ñ├å `HTMLTextAreaElement` for `#duet-input`
    -    -- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
    -    -- `showFloatingComposer()`: redirects to `showComposeOverlay()`
    -    -- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
    -    -- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
    -    -- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap
    -    +## Minimal Diff Hunks
    -    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    -    +    index 81ccc1e..cb58614 100644
    -    +    --- a/evidence/updatedifflog.md
    -    +    +++ b/evidence/updatedifflog.md
    -    +    @@ -1,87 +1,343 @@
    -    +     Ôö¼Ôöñ├ö├▓├╣├ö├Â├ë# Diff Log (overwrite each cycle)
    -    +     
    -    +     ## Cycle Metadata
    -    +    -- Timestamp: 2026-02-11T18:45:00+00:00
    -    +    +- Timestamp: 2026-02-11T19:40:53+00:00
    -    +     - Branch: claude/romantic-jones
    -    +    -- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -    +    -- Diff basis: unstaged
    -    +    +- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    -    +    +- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -    +    +- Diff basis: staged
    -    +     
    -    +     ## Cycle Status
    -    +     - Status: COMPLETE
    -    +     
    -    +     ## Summary
    -    +    -- Replaced composer UX with centered "ghost narrator" input overlay.
    -    +    -- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
    -    +    -- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
    -    +    -- Textarea auto-expands vertically as user types (up to max-height).
    -    +    -- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
    -    +    -- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
    -    +    -- No borders/box/chrome on the centered input Ôö£├ÂÔö£├ºÔö£├é ghost narrator styling.
    -    +    -- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
    -    +    -- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.
    -    +    +- Removed compose overlay backdrop blur entirely (was 2px) and reduced dim from 0.30 Ôö£├ÂÔö£├æÔö£├Ñ 0.18; background messages now clearly readable.
    -    +    +- Fixed X close button not clickable: root cause was `.duet-shell` `backdrop-filter: blur(10px)` creating a CSS stacking context that traps all children below the compose overlay on `document.body`.
    -    +    +- Solution: added dedicated `.compose-close-btn` (Ôö£├ÂÔö¼├║Ôö£Ôûô) inside `.compose-overlay` itself, wired to `hideComposeOverlay()`. Sidesteps stacking context entirely.
    -    +    +- Removed non-functional `.flow-menu.compose-elevated` CSS rule and class toggle from JS.
    -    +    +- Flow-menu trigger now hidden during compose mode instead of showing close-mode styling.
    -    +     
    -    +    -## Files Changed (unstaged)
    -    +    -- web/index.html Ôö£├ÂÔö£├ºÔö£├é `<input>` Ôö£├ÂÔö£├æÔö£├Ñ `<textarea>` in composer
    -    +    -- web/src/main.ts Ôö£├ÂÔö£├ºÔö£├é compose overlay logic, type updates, auto-expand, VisualViewport handler
    -    +    -- web/src/style.css Ôö£├ÂÔö£├ºÔö£├é textarea styles, compose overlay CSS, narrator styling
    -    +    -- web/dist/index.html Ôö£├ÂÔö£├ºÔö£├é `<input>` Ôö£├ÂÔö£├æÔö£├Ñ `<textarea>` (built)
    -    +    -- web/dist/main.js Ôö£├ÂÔö£├ºÔö£├é compiled output
    -    +    -- web/dist/style.css Ôö£├ÂÔö£├ºÔö£├é compiled CSS
    -    +    -- evidence/updatedifflog.md Ôö£├ÂÔö£├ºÔö£├é this file
    -    +    +## Files Changed (staged)
    -    +    +- evidence/updatedifflog.md
    -    +    +- web/dist/main.js
    -    +    +- web/dist/style.css
    -    +    +- web/src/main.ts
    -    +    +- web/src/style.css
    -    +     
    -    +     ## git status -sb
    -    +         ## claude/romantic-jones
    -    +          M .claude/settings.local.json
    -    +    -     M web/dist/index.html
    -    +    -     M web/dist/main.js
    -    +    -     M web/dist/style.css
    -    +    -     M web/index.html
    -    +    -     M web/src/main.ts
    -    +    -     M web/src/style.css
    -    +    +    M  evidence/updatedifflog.md
    -    +    +    M  web/dist/main.js
    -    +    +    M  web/dist/style.css
    -    +    +    M  web/src/main.ts
    -    +    +    M  web/src/style.css
    -    +     
    -    +    -## Minimal Diff Hunks (source files only)
    -    +    -
    -    +    -### web/index.html
    -    +    -- `<input id="duet-input" type="text" .../>` Ôö£├ÂÔö£├æÔö£├Ñ `<textarea id="duet-input" rows="1" ...></textarea>`
    -    +    -
    -    +    -### web/src/style.css
    -    +    -- `.duet-composer input` Ôö£├ÂÔö£├æÔö£├Ñ `.duet-composer textarea`
    -    +    -- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
    -    +    -- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
    -    +    -- New `.compose-overlay.active` (visible)
    -    +    -- New `.compose-overlay-backdrop` (translucent + blur)
    -    +    -- New `.compose-narrator` (centered flex column, 520px max width)
    -    +    -- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
    -    +    -- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")
    -    +    -
    -    +    -### web/src/main.ts
    -    +    -- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
    -    +    -- 6├ö├Â┬úÔö£Ôòú `HTMLInputElement` Ôö£├ÂÔö£├æÔö£├Ñ `HTMLTextAreaElement` for `#duet-input`
    -    +    -- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
    -    +    -- `showFloatingComposer()`: redirects to `showComposeOverlay()`
    -    +    -- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
    -    +    -- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
    -    +    -- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap
    -    +    +## Minimal Diff Hunks
    -    +    +    diff --git a/evidence/updatedifflog.md b/evidence/updatedifflog.md
    -    +    +    index 81ccc1e..f4a8382 100644
    -    +    +    --- a/evidence/updatedifflog.md
    -    +    +    +++ b/evidence/updatedifflog.md
    -    +    +    @@ -1,87 +1,39 @@
    -    +    +     ├ö├Â┬╝├ö├Â├▒Ôö£├ÂÔö£ÔûôÔö£ÔòúÔö£├ÂÔö£├éÔö£├½# Diff Log (overwrite each cycle)
    -    +    +     
    -    +    +     ## Cycle Metadata
    -    +    +    -- Timestamp: 2026-02-11T18:45:00+00:00
    -    +    +    +- Timestamp: 2026-02-11T19:40:46+00:00
    -    +    +     - Branch: claude/romantic-jones
    -    +    +    -- HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -    +    +    -- Diff basis: unstaged
    -    +    +    +- HEAD: 3e099b736bce93f1da3b7b5db044be5eed38d86d
    -    +    +    +- BASE_HEAD: fec47d63bf18224e8f5622bb7e080119ef7c9dcb
    -    +    +    +- Diff basis: staged
    -    +    +     
    -    +    +     ## Cycle Status
    -    +    +    -- Status: COMPLETE
    -    +    +    +- Status: IN_PROCESS
    -    +    +     
    -    +    +     ## Summary
    -    +    +    -- Replaced composer UX with centered "ghost narrator" input overlay.
    -    +    +    -- Changed `#duet-input` from `<input type="text">` to `<textarea rows="1">` for multi-line wrapping and native iOS long-press editing.
    -    +    +    -- Added compose overlay (`#compose-overlay`) with backdrop blur: triple-tap opens centered input, double-tap outside sends.
    -    +    +    -- Textarea auto-expands vertically as user types (up to max-height).
    -    +    +    -- Added VisualViewport handler to keep narrator centered above iOS keyboard without pushing the shell.
    -    +    +    -- Composer bar (`#duet-composer`) kept intact but hidden while compose overlay is active (rollback safety).
    -    +    +    -- No borders/box/chrome on the centered input ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® ghost narrator styling.
    -    +    +    -- `showFloatingComposer()` now redirects to `showComposeOverlay()`.
    -    +    +    -- All `HTMLInputElement` casts for `#duet-input` updated to `HTMLTextAreaElement`.
    -    +    +    +- TODO: 1-5 bullets (what changed, why, scope).
    -    +    +     
    -    +    +    -## Files Changed (unstaged)
    -    +    +    -- web/index.html ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® `<input>` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ `<textarea>` in composer
    -    +    +    -- web/src/main.ts ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® compose overlay logic, type updates, auto-expand, VisualViewport handler
    -    +    +    -- web/src/style.css ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® textarea styles, compose overlay CSS, narrator styling
    -    +    +    -- web/dist/index.html ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® `<input>` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ `<textarea>` (built)
    -    +    +    -- web/dist/main.js ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® compiled output
    -    +    +    -- web/dist/style.css ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® compiled CSS
    -    +    +    -- evidence/updatedifflog.md ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® this file
    -    +    +    +## Files Changed (staged)
    -    +    +    +- (none detected)
    -    +    +     
    -    +    +     ## git status -sb
    -    +    +         ## claude/romantic-jones
    -    +    +          M .claude/settings.local.json
    -    +    +    -     M web/dist/index.html
    -    +    +    +     M evidence/updatedifflog.md
    -    +    +          M web/dist/main.js
    -    +    +          M web/dist/style.css
    -    +    +    -     M web/index.html
    -    +    +          M web/src/main.ts
    -    +    +          M web/src/style.css
    -    +    +     
    -    +    +    -## Minimal Diff Hunks (source files only)
    -    +    +    -
    -    +    +    -### web/index.html
    -    +    +    -- `<input id="duet-input" type="text" .../>` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ `<textarea id="duet-input" rows="1" ...></textarea>`
    -    +    +    -
    -    +    +    -### web/src/style.css
    -    +    +    -- `.duet-composer input` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ `.duet-composer textarea`
    -    +    +    -- `#duet-input` gains: `resize: none; overflow-y: auto; max-height: 120px; min-height: 36px; line-height: 1.4; field-sizing: content; font-family: inherit; color: inherit; padding: 8px 10px; border-radius: 10px`
    -    +    +    -- New `.compose-overlay` (fixed inset, z-index 100, opacity transition)
    -    +    +    -- New `.compose-overlay.active` (visible)
    -    +    +    -- New `.compose-overlay-backdrop` (translucent + blur)
    -    +    +    -- New `.compose-narrator` (centered flex column, 520px max width)
    -    +    +    -- New `.compose-narrator #duet-input` (transparent bg, no border, 20px centered text, max-height 40vh)
    -    +    +    -- New `.compose-narrator .compose-hint` (subtle label "Double-tap outside to send")
    -    +    +    -
    -    +    +    -### web/src/main.ts
    -    +    +    -- Added state: `composeOverlay`, `composeActive`, `composeDblTapTimer/Count`, `COMPOSE_DBL_TAP_WINDOW_MS`
    -    +    +    -- 6Ôö£├ÂÔö£├éÔö¼├║├ö├Â┬ú├ö├▓├║ `HTMLInputElement` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ `HTMLTextAreaElement` for `#duet-input`
    -    +    +    -- `wireDuetComposer()`: textarea auto-expand on input, `wireComposeOverlayKeyboard()` call
    -    +    +    -- `showFloatingComposer()`: redirects to `showComposeOverlay()`
    -    +    +    -- `hideFloatingComposer()`: routes through `hideComposeOverlay()` when active
    -    +    +    -- New functions: `ensureComposeOverlay()`, `handleComposeBackdropTap()`, `composeOverlaySend()`, `showComposeOverlay()`, `hideComposeOverlay()`, `autoExpandTextarea()`, `wireComposeOverlayKeyboard()`
    -    +    +    -- `wireFloatingComposerTrigger()`: now calls `showComposeOverlay()` on triple-tap
    -    +    +    +## Minimal Diff Hunks
    -    +    +    +    (none)
    -    +    +     
    -    +    +     ## Verification
    -    +    +    -- Static: `tsc --noEmit` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
    -    +    +    -- Static: `tsc -p tsconfig.json --noCheck` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® build emits successfully
    -    +    +    -- Runtime: pytest 183 passed, 1 warning in 114.43s
    -    +    +    -- Runtime: node ui_onboarding_hints_test.mjs ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® 17/17 PASS
    -    +    +    -- Runtime: node ui_proposal_renderer_test.mjs ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® 3/3 PASS
    -    +    +    -- Contract: physics.yaml unchanged; minimal diff; no refactors
    -    +    +    +- TODO: verification evidence (static -> runtime -> behavior -> contract).
    -    +    +     
    -    +    +    -## Behavioral Design Notes
    -    +    +    -- Triple-tap on `.duet-stage` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
    -    +    +    -- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
    -    +    +    -- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` ├ö├Â┬úÔö£├é├ö├Â┬úÔö£├ª├ö├Â┬úÔö£├æ sends, clears, hides overlay
    -    +    +    -- Double-tap uses `pointerdown` on backdrop only ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® cannot fire during text selection inside input
    -    +    +    -- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
    -    +    +    -- Shell (`#duet-shell`) is never repositioned ├ö├Â┬úÔö£├é├ö├Â┬úÔö£┬║├ö├Â┬úÔö£├® only the narrator overlay adjusts
    -    +    +    -- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur
    -    +    +    +## Notes (optional)
    -    +    +    +- TODO: blockers, risks, constraints.
    -    +    +     
    -    +    +     ## Next Steps
    -    +    +    -- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
    -    +    +    -- Phase 6C: Render deployment + smoke tests
    -    +    +    -- Future cycle: mic button / STT live transcription
    -    +    +    +- TODO: next actions (small, specific).
    -    +    +     
    -    +    +    diff --git a/web/dist/main.js b/web/dist/main.js
    -    +    +    index 18ca797..92f9e81 100644
    -    +    +    --- a/web/dist/main.js
    -    +    +    +++ b/web/dist/main.js
    -    +    +    @@ -2112,6 +2112,14 @@ function ensureComposeOverlay() {
    -    +    +         const backdrop = document.createElement("div");
    -    +    +         backdrop.className = "compose-overlay-backdrop";
    -    +    +         overlay.appendChild(backdrop);
    -    +    +    +    // Close button inside overlay (above backdrop, always clickable)
    -    +    +    +    const closeBtn = document.createElement("button");
    -    +    +    +    closeBtn.type = "button";
    -    +    +    +    closeBtn.className = "compose-close-btn";
    -    +    +    +    closeBtn.textContent = "\u2715";
    -    +    +    +    closeBtn.setAttribute("aria-label", "Close composer");
    -    +    +    +    closeBtn.addEventListener("click", () => hideComposeOverlay());
    -    +    +    +    overlay.appendChild(closeBtn);
    -    +    +         const narrator = document.createElement("div");
    -    +    +         narrator.className = "compose-narrator";
    -    +    +         overlay.appendChild(narrator);
    -    +    +    @@ -2290,20 +2298,16 @@ function syncFlowMenuVisibility() {
    -    +    +             return;
    -    +    +         const trigger = document.getElementById("flow-menu-trigger");
    -    +    +         if (composerVisible) {
    -    +    +    -        // Show trigger as a red ├ö├Â┬úÔö£├é├ö├Â┬╝Ôö£Ôòæ├ö├Â┬ú├ö├╗├┤ close button instead of hiding it
    -    +    +    -        flowMenuContainer.classList.remove("hidden");
    -    +    +    -        if (trigger) {
    -    +    +    -            trigger.classList.add("close-mode");
    -    +    +    -            trigger.textContent = "├ö├Â┬úÔö£├é├ö├Â┬╝Ôö£Ôòæ├ö├Â┬ú├ö├╗├┤";
    -    +    +    -            trigger.setAttribute("aria-label", "Close composer");
    -    +    +    -        }
    -    +    +    -        // Hide the dropdown while in close mode
    -    +    +    +        // Hide the flow-menu trigger (compose overlay has its own close button)
    -    +    +    +        flowMenuContainer.classList.add("hidden");
    -    +    +    +        // Hide the dropdown while in compose mode
    -    +    +             if (flowMenuDropdown) {
    -    +    +                 flowMenuDropdown.style.display = "none";
    -    +    +                 flowMenuDropdown.classList.remove("open");
    -    +    +             }
    -    +    +         }
    -    +    +         else {
    -    +    +    +        flowMenuContainer.classList.remove("hidden");
    -    +    +             if (trigger) {
    -    +    +                 trigger.classList.remove("close-mode");
    -    +    +                 trigger.textContent = "├ö├Â┬úÔö£├é├ö├Â┬úÔö¼├║├ö├Â┬úÔö£Ôòù";
    -    +    +    diff --git a/web/dist/style.css b/web/dist/style.css
    -    +    +    index a94e659..0ff97ac 100644
    -    +    +    --- a/web/dist/style.css
    -    +    +    +++ b/web/dist/style.css
    -    +    +    @@ -275,6 +275,32 @@ pre {
    -    +    +       transform: translateY(-1px);
    -    +    +     }
    -    +    +     
    -    +    +    +/* Close button inside compose overlay */
    -    +    +    +.compose-close-btn {
    -    +    +    +  position: absolute;
    -    +    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    -    +    +    +  right: 22px;
    -    +    +    +  z-index: 2;
    -    +    +    +  width: 46px;
    -    +    +    +  height: 46px;
    -    +    +    +  border-radius: 12px;
    -    +    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    -    +    +    +  background: rgba(220, 38, 38, 0.85);
    -    +    +    +  color: #fff;
    -    +    +    +  font-size: 18px;
    -    +    +    +  font-weight: 700;
    -    +    +    +  display: inline-flex;
    -    +    +    +  align-items: center;
    -    +    +    +  justify-content: center;
    -    +    +    +  cursor: pointer;
    -    +    +    +  box-shadow: var(--shadow);
    -    +    +    +  transition: background 120ms ease;
    -    +    +    +}
    -    +    +    +
    -    +    +    +.compose-close-btn:hover {
    -    +    +    +  background: rgba(239, 68, 68, 1);
    -    +    +    +}
    -    +    +    +
    -    +    +     .flow-menu-dropdown {
    -    +    +       position: absolute;
    -    +    +       top: calc(100% + 6px);
    -    +    +    @@ -802,9 +828,7 @@ pre {
    -    +    +     .compose-overlay-backdrop {
    -    +    +       position: absolute;
    -    +    +       inset: 0;
    -    +    +    -  background: rgba(5, 12, 20, 0.45);
    -    +    +    -  backdrop-filter: blur(6px);
    -    +    +    -  -webkit-backdrop-filter: blur(6px);
    -    +    +    +  background: rgba(5, 12, 20, 0.18);
    -    +    +     }
    -    +    +     
    -    +    +     .compose-narrator {
    -    +    +    diff --git a/web/src/main.ts b/web/src/main.ts
    -    +    +    index dc4ec82..756b656 100644
    -    +    +    --- a/web/src/main.ts
    -    +    +    +++ b/web/src/main.ts
    -    +    +    @@ -2218,6 +2218,15 @@ function ensureComposeOverlay(): HTMLDivElement {
    -    +    +       backdrop.className = "compose-overlay-backdrop";
    -    +    +       overlay.appendChild(backdrop);
    -    +    +     
    -    +    +    +  // Close button inside overlay (above backdrop, always clickable)
    -    +    +    +  const closeBtn = document.createElement("button");
    -    +    +    +  closeBtn.type = "button";
    -    +    +    +  closeBtn.className = "compose-close-btn";
    -    +    +    +  closeBtn.textContent = "\u2715";
    -    +    +    +  closeBtn.setAttribute("aria-label", "Close composer");
    -    +    +    +  closeBtn.addEventListener("click", () => hideComposeOverlay());
    -    +    +    +  overlay.appendChild(closeBtn);
    -    +    +    +
    -    +    +       const narrator = document.createElement("div");
    -    +    +       narrator.className = "compose-narrator";
    -    +    +       overlay.appendChild(narrator);
    -    +    +    @@ -2397,19 +2406,15 @@ function syncFlowMenuVisibility() {
    -    +    +       if (!flowMenuContainer) return;
    -    +    +       const trigger = document.getElementById("flow-menu-trigger");
    -    +    +       if (composerVisible) {
    -    +    +    -    // Show trigger as a red ├ö├Â┬úÔö£├é├ö├Â┬╝Ôö£Ôòæ├ö├Â┬ú├ö├╗├┤ close button instead of hiding it
    -    +    +    -    flowMenuContainer.classList.remove("hidden");
    -    +    +    -    if (trigger) {
    -    +    +    -      trigger.classList.add("close-mode");
    -    +    +    -      trigger.textContent = "├ö├Â┬úÔö£├é├ö├Â┬╝Ôö£Ôòæ├ö├Â┬ú├ö├╗├┤";
    -    +    +    -      trigger.setAttribute("aria-label", "Close composer");
    -    +    +    -    }
    -    +    +    -    // Hide the dropdown while in close mode
    -    +    +    +    // Hide the flow-menu trigger (compose overlay has its own close button)
    -    +    +    +    flowMenuContainer.classList.add("hidden");
    -    +    +    +    // Hide the dropdown while in compose mode
    -    +    +         if (flowMenuDropdown) {
    -    +    +           flowMenuDropdown.style.display = "none";
    -    +    +           flowMenuDropdown.classList.remove("open");
    -    +    +         }
    -    +    +       } else {
    -    +    +    +    flowMenuContainer.classList.remove("hidden");
    -    +    +         if (trigger) {
    -    +    +           trigger.classList.remove("close-mode");
    -    +    +           trigger.textContent = "├ö├Â┬úÔö£├é├ö├Â┬úÔö¼├║├ö├Â┬úÔö£Ôòù";
    -    +    +    diff --git a/web/src/style.css b/web/src/style.css
    -    +    +    index a94e659..0ff97ac 100644
    -    +    +    --- a/web/src/style.css
    -    +    +    +++ b/web/src/style.css
    -    +    +    @@ -275,6 +275,32 @@ pre {
    -    +    +       transform: translateY(-1px);
    -    +    +     }
    -    +    +     
    -    +    +    +/* Close button inside compose overlay */
    -    +    +    +.compose-close-btn {
    -    +    +    +  position: absolute;
    -    +    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    -    +    +    +  right: 22px;
    -    +    +    +  z-index: 2;
    -    +    +    +  width: 46px;
    -    +    +    +  height: 46px;
    -    +    +    +  border-radius: 12px;
    -    +    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    -    +    +    +  background: rgba(220, 38, 38, 0.85);
    -    +    +    +  color: #fff;
    -    +    +    +  font-size: 18px;
    -    +    +    +  font-weight: 700;
    -    +    +    +  display: inline-flex;
    -    +    +    +  align-items: center;
    -    +    +    +  justify-content: center;
    -    +    +    +  cursor: pointer;
    -    +    +    +  box-shadow: var(--shadow);
    -    +    +    +  transition: background 120ms ease;
    -    +    +    +}
    -    +    +    +
    -    +    +    +.compose-close-btn:hover {
    -    +    +    +  background: rgba(239, 68, 68, 1);
    -    +    +    +}
    -    +    +    +
    -    +    +     .flow-menu-dropdown {
    -    +    +       position: absolute;
    -    +    +       top: calc(100% + 6px);
    -    +    +    @@ -802,9 +828,7 @@ pre {
    -    +    +     .compose-overlay-backdrop {
    -    +    +       position: absolute;
    -    +    +       inset: 0;
    -    +    +    -  background: rgba(5, 12, 20, 0.45);
    -    +    +    -  backdrop-filter: blur(6px);
    -    +    +    -  -webkit-backdrop-filter: blur(6px);
    -    +    +    +  background: rgba(5, 12, 20, 0.18);
    -    +    +     }
    -    +    +     
    -    +    +     .compose-narrator {
    -    +     
    -    +     ## Verification
    -    +    -- Static: `tsc --noEmit` Ôö£├ÂÔö£├ºÔö£├é 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
    -    +    +- Static: `tsc --noEmit` Ôö£├ÂÔö£├ºÔö£├é 1 pre-existing TS2339 (line 1174 `item.location`), no new errors
    -    +     - Static: `tsc -p tsconfig.json --noCheck` Ôö£├ÂÔö£├ºÔö£├é build emits successfully
    -    +    -- Runtime: pytest 183 passed, 1 warning in 114.43s
    -    +    +- Runtime: pytest 183 passed, 1 warning in 114.30s
    -    +     - Runtime: node ui_onboarding_hints_test.mjs Ôö£├ÂÔö£├ºÔö£├é 17/17 PASS
    -    +     - Runtime: node ui_proposal_renderer_test.mjs Ôö£├ÂÔö£├ºÔö£├é 3/3 PASS
    -    +     - Contract: physics.yaml unchanged; minimal diff; no refactors
    -    +     
    -    +    -## Behavioral Design Notes
    -    +    -- Triple-tap on `.duet-stage` Ôö£├ÂÔö£├æÔö£├Ñ `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
    -    +    -- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
    -    +    -- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` Ôö£├ÂÔö£├æÔö£├Ñ sends, clears, hides overlay
    -    +    -- Double-tap uses `pointerdown` on backdrop only Ôö£├ÂÔö£├ºÔö£├é cannot fire during text selection inside input
    -    +    -- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
    -    +    -- Shell (`#duet-shell`) is never repositioned Ôö£├ÂÔö£├ºÔö£├é only the narrator overlay adjusts
    -    +    -- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur
    -    +    +## Notes
    -    +    +- Root cause: `.duet-shell` has `backdrop-filter: blur(10px)` (style.css L65) which creates a stacking context. Even `position: fixed; z-index: 110` on a child cannot escape it. Compose overlay at z-index 100 on body always wins.
    -    +     
    -    +     ## Next Steps
    -    +    -- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
    -    +    +- Physical iPhone Safari testing: confirm Ôö£├ÂÔö¼├║Ôö£Ôûô clickable, blur readable, double-tap send works
    -    +     - Phase 6C: Render deployment + smoke tests
    -    +    -- Future cycle: mic button / STT live transcription
    -    +     
    -    +    diff --git a/web/dist/main.js b/web/dist/main.js
    -    +    index 18ca797..4cde744 100644
    -    +    --- a/web/dist/main.js
    -    +    +++ b/web/dist/main.js
    -    +    @@ -2112,6 +2112,14 @@ function ensureComposeOverlay() {
    -    +         const backdrop = document.createElement("div");
    -    +         backdrop.className = "compose-overlay-backdrop";
    -    +         overlay.appendChild(backdrop);
    -    +    +    // Close button inside overlay (above backdrop, always clickable)
    -    +    +    const closeBtn = document.createElement("button");
    -    +    +    closeBtn.type = "button";
    -    +    +    closeBtn.className = "compose-close-btn";
    -    +    +    closeBtn.textContent = "\u2715";
    -    +    +    closeBtn.setAttribute("aria-label", "Close composer");
    -    +    +    closeBtn.addEventListener("click", () => hideComposeOverlay());
    -    +    +    overlay.appendChild(closeBtn);
    -    +         const narrator = document.createElement("div");
    -    +         narrator.className = "compose-narrator";
    -    +         overlay.appendChild(narrator);
    -    +    @@ -2173,6 +2181,14 @@ function showComposeOverlay() {
    -    +         // Move input into narrator container
    -    +         const narrator = overlay.querySelector(".compose-narrator");
    -    +         narrator.insertBefore(input, narrator.firstChild);
    -    +    +    // Position close button to match original flow-menu-trigger location
    -    +    +    const fmTrigger = document.getElementById("flow-menu-trigger");
    -    +    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    -    +    +    if (fmTrigger && closeBtn) {
    -    +    +        const rect = fmTrigger.getBoundingClientRect();
    -    +    +        closeBtn.style.top = rect.top + "px";
    -    +    +        closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    -    +    +    }
    -    +         overlay.classList.add("active");
    -    +         composeActive = true;
    -    +         composerVisible = true;
    -    +    @@ -2208,6 +2224,12 @@ function hideComposeOverlay() {
    -    +                 composer.appendChild(input);
    -    +             }
    -    +         }
    -    +    +    // Clear inline positioning from compose-close-btn
    -    +    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    -    +    +    if (closeBtn) {
    -    +    +        closeBtn.style.top = "";
    -    +    +        closeBtn.style.right = "";
    -    +    +    }
    -    +         overlay.classList.remove("active");
    -    +         composeActive = false;
    -    +         composerVisible = false;
    -    +    @@ -2290,20 +2312,16 @@ function syncFlowMenuVisibility() {
    -    +             return;
    -    +         const trigger = document.getElementById("flow-menu-trigger");
    -    +         if (composerVisible) {
    -    +    -        // Show trigger as a red Ôö£├ÂÔö¼├║Ôö£Ôûô close button instead of hiding it
    -    +    -        flowMenuContainer.classList.remove("hidden");
    -    +    -        if (trigger) {
    -    +    -            trigger.classList.add("close-mode");
    -    +    -            trigger.textContent = "Ôö£├ÂÔö¼├║Ôö£Ôûô";
    -    +    -            trigger.setAttribute("aria-label", "Close composer");
    -    +    -        }
    -    +    -        // Hide the dropdown while in close mode
    -    +    +        // Hide the flow-menu trigger (compose overlay has its own close button)
    -    +    +        flowMenuContainer.classList.add("hidden");
    -    +    +        // Hide the dropdown while in compose mode
    -    +             if (flowMenuDropdown) {
    -    +                 flowMenuDropdown.style.display = "none";
    -    +                 flowMenuDropdown.classList.remove("open");
    -    +             }
    -    +         }
    -    +         else {
    -    +    +        flowMenuContainer.classList.remove("hidden");
    -    +             if (trigger) {
    -    +                 trigger.classList.remove("close-mode");
    -    +                 trigger.textContent = "Ôö£├ÂÔö£┬úÔö£├╗";
    -    +    diff --git a/web/dist/style.css b/web/dist/style.css
    -    +    index a94e659..9f2258c 100644
    -    +    --- a/web/dist/style.css
    -    +    +++ b/web/dist/style.css
    -    +    @@ -275,6 +275,32 @@ pre {
    -    +       transform: translateY(-1px);
    -    +     }
    -    +     
    -    +    +/* Close button inside compose overlay */
    -    +    +.compose-close-btn {
    -    +    +  position: absolute;
    -    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    -    +    +  right: 22px;
    -    +    +  z-index: 2;
    -    +    +  width: 46px;
    -    +    +  height: 46px;
    -    +    +  border-radius: 12px;
    -    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    -    +    +  background: rgba(220, 38, 38, 0.85);
    -    +    +  color: #fff;
    -    +    +  font-size: 18px;
    -    +    +  font-weight: 700;
    -    +    +  display: inline-flex;
    -    +    +  align-items: center;
    -    +    +  justify-content: center;
    -    +    +  cursor: pointer;
    -    +    +  box-shadow: var(--shadow);
    -    +    +  transition: background 120ms ease;
    -    +    +}
    -    +    +
    -    +    +.compose-close-btn:hover {
    -    +    +  background: rgba(239, 68, 68, 1);
    -    +    +}
    -    +    +
    -    +     .flow-menu-dropdown {
    -    +       position: absolute;
    -    +       top: calc(100% + 6px);
    -    +    @@ -802,9 +828,9 @@ pre {
    -    +     .compose-overlay-backdrop {
    -    +       position: absolute;
    -    +       inset: 0;
    -    +    -  background: rgba(5, 12, 20, 0.45);
    -    +    -  backdrop-filter: blur(6px);
    -    +    -  -webkit-backdrop-filter: blur(6px);
    -    +    +  background: rgba(5, 12, 20, 0.18);
    -    +    +  backdrop-filter: blur(2px);
    -    +    +  -webkit-backdrop-filter: blur(2px);
    -    +     }
    -    +     
    -    +     .compose-narrator {
    -    +    diff --git a/web/src/main.ts b/web/src/main.ts
    -    +    index dc4ec82..4e8a831 100644
    -    +    --- a/web/src/main.ts
    -    +    +++ b/web/src/main.ts
    -    +    @@ -2218,6 +2218,15 @@ function ensureComposeOverlay(): HTMLDivElement {
    -    +       backdrop.className = "compose-overlay-backdrop";
    -    +       overlay.appendChild(backdrop);
    -    +     
    -    +    +  // Close button inside overlay (above backdrop, always clickable)
    -    +    +  const closeBtn = document.createElement("button");
    -    +    +  closeBtn.type = "button";
    -    +    +  closeBtn.className = "compose-close-btn";
    -    +    +  closeBtn.textContent = "\u2715";
    -    +    +  closeBtn.setAttribute("aria-label", "Close composer");
    -    +    +  closeBtn.addEventListener("click", () => hideComposeOverlay());
    -    +    +  overlay.appendChild(closeBtn);
    -    +    +
    -    +       const narrator = document.createElement("div");
    -    +       narrator.className = "compose-narrator";
    -    +       overlay.appendChild(narrator);
    -    +    @@ -2283,6 +2292,15 @@ function showComposeOverlay() {
    -    +       const narrator = overlay.querySelector(".compose-narrator") as HTMLElement;
    -    +       narrator.insertBefore(input, narrator.firstChild);
    -    +     
    -    +    +  // Position close button to match original flow-menu-trigger location
    -    +    +  const fmTrigger = document.getElementById("flow-menu-trigger");
    -    +    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    -    +    +  if (fmTrigger && closeBtn) {
    -    +    +    const rect = fmTrigger.getBoundingClientRect();
    -    +    +    closeBtn.style.top = rect.top + "px";
    -    +    +    closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    -    +    +  }
    -    +    +
    -    +       overlay.classList.add("active");
    -    +       composeActive = true;
    -    +       composerVisible = true;
    -    +    @@ -2320,6 +2338,13 @@ function hideComposeOverlay() {
    -    +         }
    -    +       }
    -    +     
    -    +    +  // Clear inline positioning from compose-close-btn
    -    +    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    -    +    +  if (closeBtn) {
    -    +    +    closeBtn.style.top = "";
    -    +    +    closeBtn.style.right = "";
    -    +    +  }
    -    +    +
    -    +       overlay.classList.remove("active");
    -    +       composeActive = false;
    -    +       composerVisible = false;
    -    +    @@ -2397,19 +2422,15 @@ function syncFlowMenuVisibility() {
    -    +       if (!flowMenuContainer) return;
    -    +       const trigger = document.getElementById("flow-menu-trigger");
    -    +       if (composerVisible) {
    -    +    -    // Show trigger as a red Ôö£├ÂÔö¼├║Ôö£Ôûô close button instead of hiding it
    -    +    -    flowMenuContainer.classList.remove("hidden");
    -    +    -    if (trigger) {
    -    +    -      trigger.classList.add("close-mode");
    -    +    -      trigger.textContent = "Ôö£├ÂÔö¼├║Ôö£Ôûô";
    -    +    -      trigger.setAttribute("aria-label", "Close composer");
    -    +    -    }
    -    +    -    // Hide the dropdown while in close mode
    -    +    +    // Hide the flow-menu trigger (compose overlay has its own close button)
    -    +    +    flowMenuContainer.classList.add("hidden");
    -    +    +    // Hide the dropdown while in compose mode
    -    +         if (flowMenuDropdown) {
    -    +           flowMenuDropdown.style.display = "none";
    -    +           flowMenuDropdown.classList.remove("open");
    -    +         }
    -    +       } else {
    -    +    +    flowMenuContainer.classList.remove("hidden");
    -    +         if (trigger) {
    -    +           trigger.classList.remove("close-mode");
    -    +           trigger.textContent = "Ôö£├ÂÔö£┬úÔö£├╗";
    -    +    diff --git a/web/src/style.css b/web/src/style.css
    -    +    index a94e659..9f2258c 100644
    -    +    --- a/web/src/style.css
    -    +    +++ b/web/src/style.css
    -    +    @@ -275,6 +275,32 @@ pre {
    -    +       transform: translateY(-1px);
    -    +     }
    -    +     
    -    +    +/* Close button inside compose overlay */
    -    +    +.compose-close-btn {
    -    +    +  position: absolute;
    -    +    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    -    +    +  right: 22px;
    -    +    +  z-index: 2;
    -    +    +  width: 46px;
    -    +    +  height: 46px;
    -    +    +  border-radius: 12px;
    -    +    +  border: 1px solid rgba(248, 113, 113, 0.5);
    -    +    +  background: rgba(220, 38, 38, 0.85);
    -    +    +  color: #fff;
    -    +    +  font-size: 18px;
    -    +    +  font-weight: 700;
    -    +    +  display: inline-flex;
    -    +    +  align-items: center;
    -    +    +  justify-content: center;
    -    +    +  cursor: pointer;
    -    +    +  box-shadow: var(--shadow);
    -    +    +  transition: background 120ms ease;
    -    +    +}
    -    +    +
    -    +    +.compose-close-btn:hover {
    -    +    +  background: rgba(239, 68, 68, 1);
    -    +    +}
    -    +    +
    -    +     .flow-menu-dropdown {
    -    +       position: absolute;
    -    +       top: calc(100% + 6px);
    -    +    @@ -802,9 +828,9 @@ pre {
    -    +     .compose-overlay-backdrop {
    -    +       position: absolute;
    -    +       inset: 0;
    -    +    -  background: rgba(5, 12, 20, 0.45);
    -    +    -  backdrop-filter: blur(6px);
    -    +    -  -webkit-backdrop-filter: blur(6px);
    -    +    +  background: rgba(5, 12, 20, 0.18);
    -    +    +  backdrop-filter: blur(2px);
    -    +    +  -webkit-backdrop-filter: blur(2px);
    -    +     }
    -    +     
    -    +     .compose-narrator {
    -     
    -     ## Verification
    -    -- Static: `tsc --noEmit` ├ö├ç├Â 1 pre-existing TS2339 (`item.location` on line 1174), no new errors
    -    +- Static: `tsc --noEmit` ├ö├ç├Â 1 pre-existing TS2339 (line 1174 `item.location`), no new errors
    -     - Static: `tsc -p tsconfig.json --noCheck` ├ö├ç├Â build emits successfully
    -    -- Runtime: pytest 183 passed, 1 warning in 114.43s
    -    +- Runtime: pytest 183 passed, 1 warning in 114.58s
    -     - Runtime: node ui_onboarding_hints_test.mjs ├ö├ç├Â 17/17 PASS
    -     - Runtime: node ui_proposal_renderer_test.mjs ├ö├ç├Â 3/3 PASS
    -     - Contract: physics.yaml unchanged; minimal diff; no refactors
    -     
    -    -## Behavioral Design Notes
    -    -- Triple-tap on `.duet-stage` ├ö├Ñ├å `showComposeOverlay()` creates/shows overlay, moves `#duet-input` textarea into `.compose-narrator`, focuses it
    -    -- Typing wraps naturally in textarea; auto-expand adjusts height up to 200px (40vh in overlay)
    -    -- Double-tap on `.compose-overlay-backdrop` triggers `composeOverlaySend()` ├ö├Ñ├å sends, clears, hides overlay
    -    -- Double-tap uses `pointerdown` on backdrop only ├ö├ç├Â cannot fire during text selection inside input
    -    -- VisualViewport resize/scroll repositions narrator at 35% of visible height (keeps it above iOS keyboard)
    -    -- Shell (`#duet-shell`) is never repositioned ├ö├ç├Â only the narrator overlay adjusts
    -    -- After send: overlay hides, input returns to `#duet-composer`, keyboard dismisses via blur
    -    +## Notes
    -    +- Original X: `.flow-menu` at `position: absolute; top: 90px; right: 22px` inside `.duet-shell` (relative). New `.compose-close-btn` is inside `.compose-overlay` (fixed inset:0 on body). Using `getBoundingClientRect()` maps the original's viewport position onto the overlay's coordinate space exactly.
    -     
    -     ## Next Steps
    -    -- Physical iPhone Safari testing: confirm no shell push, confirm double-tap send, confirm text selection works
    -    +- Physical iPhone Safari testing: confirm blur subtle, X position matches original, double-tap send works
    -     - Phase 6C: Render deployment + smoke tests
    -    -- Future cycle: mic button / STT live transcription
    -     
         diff --git a/web/dist/main.js b/web/dist/main.js
    -    index 18ca797..4cde744 100644
    +    index 4cde744..957cb28 100644
         --- a/web/dist/main.js
         +++ b/web/dist/main.js
    -    @@ -2112,6 +2112,14 @@ function ensureComposeOverlay() {
    -         const backdrop = document.createElement("div");
    -         backdrop.className = "compose-overlay-backdrop";
    -         overlay.appendChild(backdrop);
    -    +    // Close button inside overlay (above backdrop, always clickable)
    -    +    const closeBtn = document.createElement("button");
    -    +    closeBtn.type = "button";
    -    +    closeBtn.className = "compose-close-btn";
    -    +    closeBtn.textContent = "\u2715";
    -    +    closeBtn.setAttribute("aria-label", "Close composer");
    -    +    closeBtn.addEventListener("click", () => hideComposeOverlay());
    -    +    overlay.appendChild(closeBtn);
    +    @@ -224,6 +224,8 @@ let composeActive = false;
    +     let composeDblTapTimer = null;
    +     let composeDblTapCount = 0;
    +     const COMPOSE_DBL_TAP_WINDOW_MS = 350;
    +    +let dictationActive = false;
    +    +let speechRecognition = null;
    +     function headers() {
    +         var _a;
    +         const h = { "Content-Type": "application/json" };
    +    @@ -2120,6 +2122,14 @@ function ensureComposeOverlay() {
    +         closeBtn.setAttribute("aria-label", "Close composer");
    +         closeBtn.addEventListener("click", () => hideComposeOverlay());
    +         overlay.appendChild(closeBtn);
    +    +    // Mic button inside overlay (below close btn, same style)
    +    +    const micBtn = document.createElement("button");
    +    +    micBtn.type = "button";
    +    +    micBtn.className = "compose-mic-btn";
    +    +    micBtn.textContent = "\uD83C\uDFA4";
    +    +    micBtn.setAttribute("aria-label", "Toggle voice dictation");
    +    +    micBtn.addEventListener("click", () => toggleComposeDictation());
    +    +    overlay.appendChild(micBtn);
              const narrator = document.createElement("div");
              narrator.className = "compose-narrator";
              overlay.appendChild(narrator);
    -    @@ -2173,6 +2181,14 @@ function showComposeOverlay() {
    +    @@ -2134,6 +2144,10 @@ function ensureComposeOverlay() {
    +         return overlay;
    +     }
    +     function handleComposeBackdropTap() {
    +    +    // Single tap on backdrop stops dictation (if running) without sending
    +    +    if (dictationActive) {
    +    +        stopComposeDictation();
    +    +    }
    +         composeDblTapCount += 1;
    +         if (composeDblTapTimer !== null) {
    +             window.clearTimeout(composeDblTapTimer);
    +    @@ -2153,6 +2167,7 @@ function handleComposeBackdropTap() {
    +     }
    +     function composeOverlaySend() {
    +         var _a, _b;
    +    +    stopComposeDictation();
    +         const input = document.getElementById("duet-input");
    +         const text = (_a = input === null || input === void 0 ? void 0 : input.value.trim()) !== null && _a !== void 0 ? _a : "";
    +         if (!text || composerBusy)
    +    @@ -2181,13 +2196,18 @@ function showComposeOverlay() {
              // Move input into narrator container
              const narrator = overlay.querySelector(".compose-narrator");
              narrator.insertBefore(input, narrator.firstChild);
    -    +    // Position close button to match original flow-menu-trigger location
    -    +    const fmTrigger = document.getElementById("flow-menu-trigger");
    -    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    -    +    if (fmTrigger && closeBtn) {
    -    +        const rect = fmTrigger.getBoundingClientRect();
    -    +        closeBtn.style.top = rect.top + "px";
    -    +        closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    -    +    }
    +    -    // Position close button to match original flow-menu-trigger location
    +    +    // Position close button and mic button to match original flow-menu-trigger location
    +         const fmTrigger = document.getElementById("flow-menu-trigger");
    +         const closeBtn = overlay.querySelector(".compose-close-btn");
    +    +    const micBtn = overlay.querySelector(".compose-mic-btn");
    +         if (fmTrigger && closeBtn) {
    +             const rect = fmTrigger.getBoundingClientRect();
    +             closeBtn.style.top = rect.top + "px";
    +             closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    +        if (micBtn) {
    +    +            micBtn.style.top = (rect.top + 46 + 8) + "px";
    +    +            micBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    +        }
    +         }
              overlay.classList.add("active");
              composeActive = true;
    -         composerVisible = true;
    -    @@ -2208,6 +2224,12 @@ function hideComposeOverlay() {
    +    @@ -2203,6 +2223,7 @@ function showComposeOverlay() {
    +         setFlowMenuOpen(false);
    +         window.requestAnimationFrame(() => {
    +             input.focus();
    +    +        input.setSelectionRange(input.value.length, input.value.length);
    +             autoExpandTextarea(input);
    +         });
    +     }
    +    @@ -2224,12 +2245,19 @@ function hideComposeOverlay() {
                      composer.appendChild(input);
                  }
              }
    -    +    // Clear inline positioning from compose-close-btn
    -    +    const closeBtn = overlay.querySelector(".compose-close-btn");
    -    +    if (closeBtn) {
    -    +        closeBtn.style.top = "";
    -    +        closeBtn.style.right = "";
    +    -    // Clear inline positioning from compose-close-btn
    +    +    // Stop dictation if running
    +    +    stopComposeDictation();
    +    +    // Clear inline positioning from compose-close-btn and compose-mic-btn
    +         const closeBtn = overlay.querySelector(".compose-close-btn");
    +         if (closeBtn) {
    +             closeBtn.style.top = "";
    +             closeBtn.style.right = "";
    +         }
    +    +    const micBtn = overlay.querySelector(".compose-mic-btn");
    +    +    if (micBtn) {
    +    +        micBtn.style.top = "";
    +    +        micBtn.style.right = "";
         +    }
              overlay.classList.remove("active");
              composeActive = false;
              composerVisible = false;
    -    @@ -2290,20 +2312,16 @@ function syncFlowMenuVisibility() {
    -             return;
    -         const trigger = document.getElementById("flow-menu-trigger");
    -         if (composerVisible) {
    -    -        // Show trigger as a red ├ö┬ú├▓ close button instead of hiding it
    -    -        flowMenuContainer.classList.remove("hidden");
    -    -        if (trigger) {
    -    -            trigger.classList.add("close-mode");
    -    -            trigger.textContent = "├ö┬ú├▓";
    -    -            trigger.setAttribute("aria-label", "Close composer");
    -    -        }
    -    -        // Hide the dropdown while in close mode
    -    +        // Hide the flow-menu trigger (compose overlay has its own close button)
    -    +        flowMenuContainer.classList.add("hidden");
    -    +        // Hide the dropdown while in compose mode
    -             if (flowMenuDropdown) {
    -                 flowMenuDropdown.style.display = "none";
    -                 flowMenuDropdown.classList.remove("open");
    -             }
    -         }
    -         else {
    -    +        flowMenuContainer.classList.remove("hidden");
    -             if (trigger) {
    -                 trigger.classList.remove("close-mode");
    -                 trigger.textContent = "├ö├£├û";
    +    @@ -2240,6 +2268,96 @@ function autoExpandTextarea(el) {
    +         el.style.height = "auto";
    +         el.style.height = Math.min(el.scrollHeight, 200) + "px";
    +     }
    +    +// ├ö├Â├ç├ö├Â├ç Compose dictation (Web Speech API) ├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç
    +    +function getSpeechRecognitionCtor() {
    +    +    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
    +    +}
    +    +function toggleComposeDictation() {
    +    +    if (dictationActive) {
    +    +        stopComposeDictation();
    +    +    }
    +    +    else {
    +    +        startComposeDictation();
    +    +    }
    +    +}
    +    +function startComposeDictation() {
    +    +    const SRCtor = getSpeechRecognitionCtor();
    +    +    if (!SRCtor) {
    +    +        setDuetStatus("Voice dictation is not supported on this browser.", false);
    +    +        const micBtn = composeOverlay === null || composeOverlay === void 0 ? void 0 : composeOverlay.querySelector(".compose-mic-btn");
    +    +        if (micBtn)
    +    +            micBtn.classList.add("disabled");
    +    +        return;
    +    +    }
    +    +    const input = document.getElementById("duet-input");
    +    +    if (!input)
    +    +        return;
    +    +    const sr = new SRCtor();
    +    +    sr.continuous = true;
    +    +    sr.interimResults = true;
    +    +    sr.lang = "en-US";
    +    +    // Track the text that existed before dictation started
    +    +    const baseText = input.value;
    +    +    sr.onresult = (event) => {
    +    +        let interim = "";
    +    +        let final = "";
    +    +        for (let i = 0; i < event.results.length; i++) {
    +    +            const transcript = event.results[i][0].transcript;
    +    +            if (event.results[i].isFinal) {
    +    +                final += transcript;
    +    +            }
    +    +            else {
    +    +                interim += transcript;
    +    +            }
    +    +        }
    +    +        const separator = baseText.length > 0 && !baseText.endsWith(" ") ? " " : "";
    +    +        input.value = baseText + separator + final + interim;
    +    +        autoExpandTextarea(input);
    +    +        input.setSelectionRange(input.value.length, input.value.length);
    +    +    };
    +    +    sr.onerror = (event) => {
    +    +        if (event.error !== "aborted" && event.error !== "no-speech") {
    +    +            setDuetStatus("Dictation error: " + event.error, false);
    +    +        }
    +    +        stopComposeDictation();
    +    +    };
    +    +    sr.onend = () => {
    +    +        // If still marked active, recognition stopped unexpectedly ├ö├ç├Â update UI
    +    +        if (dictationActive) {
    +    +            dictationActive = false;
    +    +            updateMicButtonState();
    +    +        }
    +    +    };
    +    +    try {
    +    +        sr.start();
    +    +        speechRecognition = sr;
    +    +        dictationActive = true;
    +    +        updateMicButtonState();
    +    +    }
    +    +    catch (e) {
    +    +        setDuetStatus("Could not start dictation.", false);
    +    +    }
    +    +}
    +    +function stopComposeDictation() {
    +    +    if (!dictationActive && !speechRecognition)
    +    +        return;
    +    +    dictationActive = false;
    +    +    if (speechRecognition) {
    +    +        try {
    +    +            speechRecognition.stop();
    +    +        }
    +    +        catch (_) { /* ignore */ }
    +    +        speechRecognition = null;
    +    +    }
    +    +    updateMicButtonState();
    +    +}
    +    +function updateMicButtonState() {
    +    +    const micBtn = composeOverlay === null || composeOverlay === void 0 ? void 0 : composeOverlay.querySelector(".compose-mic-btn");
    +    +    if (!micBtn)
    +    +        return;
    +    +    micBtn.classList.toggle("recording", dictationActive);
    +    +    micBtn.setAttribute("aria-label", dictationActive ? "Stop voice dictation" : "Start voice dictation");
    +    +}
    +     function wireComposeOverlayKeyboard() {
    +         // Use VisualViewport to keep compose overlay centered above keyboard on iOS
    +         if (typeof window === "undefined")
         diff --git a/web/dist/style.css b/web/dist/style.css
    -    index a94e659..08e5f8c 100644
    +    index 08e5f8c..7563518 100644
         --- a/web/dist/style.css
         +++ b/web/dist/style.css
    -    @@ -275,6 +275,33 @@ pre {
    -       transform: translateY(-1px);
    +    @@ -302,6 +302,49 @@ pre {
    +       background: rgba(239, 68, 68, 1);
          }
          
    -    +/* Close button inside compose overlay */
    -    +.compose-close-btn {
    +    +/* Mic button inside compose overlay (below close btn) */
    +    +.compose-mic-btn {
         +  position: absolute;
    -    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +    +  top: max(144px, calc(env(safe-area-inset-top) + 134px));
         +  right: 22px;
         +  z-index: 2;
         +  margin: 0;
         +  width: 46px;
         +  height: 46px;
         +  border-radius: 12px;
    -    +  border: 1px solid rgba(248, 113, 113, 0.5);
    -    +  background: rgba(220, 38, 38, 0.85);
    -    +  color: #fff;
    -    +  font-size: 18px;
    -    +  font-weight: 700;
    +    +  border: 1px solid rgba(255, 255, 255, 0.16);
    +    +  background: rgba(255, 255, 255, 0.08);
    +    +  color: var(--text);
    +    +  font-size: 20px;
         +  display: inline-flex;
         +  align-items: center;
         +  justify-content: center;
         +  cursor: pointer;
         +  box-shadow: var(--shadow);
    -    +  transition: background 120ms ease;
    +    +  transition: background 120ms ease, border-color 120ms ease;
    +    +}
    +    +
    +    +.compose-mic-btn:hover {
    +    +  background: rgba(255, 255, 255, 0.14);
         +}
         +
    -    +.compose-close-btn:hover {
    -    +  background: rgba(239, 68, 68, 1);
    +    +.compose-mic-btn.recording {
    +    +  background: rgba(220, 38, 38, 0.85);
    +    +  border-color: rgba(248, 113, 113, 0.5);
    +    +  color: #fff;
    +    +  animation: mic-pulse 1.2s ease-in-out infinite;
    +    +}
    +    +
    +    +.compose-mic-btn.disabled {
    +    +  opacity: 0.35;
    +    +  cursor: not-allowed;
    +    +}
    +    +
    +    +@keyframes mic-pulse {
    +    +  0%, 100% { box-shadow: var(--shadow); }
    +    +  50% { box-shadow: 0 0 16px 4px rgba(239, 68, 68, 0.4); }
         +}
         +
          .flow-menu-dropdown {
            position: absolute;
            top: calc(100% + 6px);
    -    @@ -802,9 +829,9 @@ pre {
    -     .compose-overlay-backdrop {
    -       position: absolute;
    -       inset: 0;
    -    -  background: rgba(5, 12, 20, 0.45);
    -    -  backdrop-filter: blur(6px);
    -    -  -webkit-backdrop-filter: blur(6px);
    -    +  background: rgba(5, 12, 20, 0.18);
    -    +  backdrop-filter: blur(2px);
    -    +  -webkit-backdrop-filter: blur(2px);
    -     }
    -     
    -     .compose-narrator {
         diff --git a/web/src/main.ts b/web/src/main.ts
    -    index dc4ec82..4e8a831 100644
    +    index 4e8a831..d3bdfc2 100644
         --- a/web/src/main.ts
         +++ b/web/src/main.ts
    -    @@ -2218,6 +2218,15 @@ function ensureComposeOverlay(): HTMLDivElement {
    -       backdrop.className = "compose-overlay-backdrop";
    -       overlay.appendChild(backdrop);
    +    @@ -237,6 +237,8 @@ let composeActive = false;
    +     let composeDblTapTimer: number | null = null;
    +     let composeDblTapCount = 0;
    +     const COMPOSE_DBL_TAP_WINDOW_MS = 350;
    +    +let dictationActive = false;
    +    +let speechRecognition: any = null;
          
    -    +  // Close button inside overlay (above backdrop, always clickable)
    -    +  const closeBtn = document.createElement("button");
    -    +  closeBtn.type = "button";
    -    +  closeBtn.className = "compose-close-btn";
    -    +  closeBtn.textContent = "\u2715";
    -    +  closeBtn.setAttribute("aria-label", "Close composer");
    -    +  closeBtn.addEventListener("click", () => hideComposeOverlay());
    -    +  overlay.appendChild(closeBtn);
    +     function headers() {
    +       const h: Record<string, string> = { "Content-Type": "application/json" };
    +    @@ -2227,6 +2229,15 @@ function ensureComposeOverlay(): HTMLDivElement {
    +       closeBtn.addEventListener("click", () => hideComposeOverlay());
    +       overlay.appendChild(closeBtn);
    +     
    +    +  // Mic button inside overlay (below close btn, same style)
    +    +  const micBtn = document.createElement("button");
    +    +  micBtn.type = "button";
    +    +  micBtn.className = "compose-mic-btn";
    +    +  micBtn.textContent = "\uD83C\uDFA4";
    +    +  micBtn.setAttribute("aria-label", "Toggle voice dictation");
    +    +  micBtn.addEventListener("click", () => toggleComposeDictation());
    +    +  overlay.appendChild(micBtn);
         +
            const narrator = document.createElement("div");
            narrator.className = "compose-narrator";
            overlay.appendChild(narrator);
    -    @@ -2283,6 +2292,15 @@ function showComposeOverlay() {
    +    @@ -2246,6 +2257,10 @@ function ensureComposeOverlay(): HTMLDivElement {
    +     }
    +     
    +     function handleComposeBackdropTap() {
    +    +  // Single tap on backdrop stops dictation (if running) without sending
    +    +  if (dictationActive) {
    +    +    stopComposeDictation();
    +    +  }
    +       composeDblTapCount += 1;
    +       if (composeDblTapTimer !== null) {
    +         window.clearTimeout(composeDblTapTimer);
    +    @@ -2264,6 +2279,7 @@ function handleComposeBackdropTap() {
    +     }
    +     
    +     function composeOverlaySend() {
    +    +  stopComposeDictation();
    +       const input = document.getElementById("duet-input") as HTMLTextAreaElement | null;
    +       const text = input?.value.trim() ?? "";
    +       if (!text || composerBusy) return;
    +    @@ -2292,13 +2308,18 @@ function showComposeOverlay() {
            const narrator = overlay.querySelector(".compose-narrator") as HTMLElement;
            narrator.insertBefore(input, narrator.firstChild);
          
    -    +  // Position close button to match original flow-menu-trigger location
    -    +  const fmTrigger = document.getElementById("flow-menu-trigger");
    -    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    -    +  if (fmTrigger && closeBtn) {
    -    +    const rect = fmTrigger.getBoundingClientRect();
    -    +    closeBtn.style.top = rect.top + "px";
    -    +    closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    -    +  }
    -    +
    +    -  // Position close button to match original flow-menu-trigger location
    +    +  // Position close button and mic button to match original flow-menu-trigger location
    +       const fmTrigger = document.getElementById("flow-menu-trigger");
    +       const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    +    +  const micBtn = overlay.querySelector(".compose-mic-btn") as HTMLElement | null;
    +       if (fmTrigger && closeBtn) {
    +         const rect = fmTrigger.getBoundingClientRect();
    +         closeBtn.style.top = rect.top + "px";
    +         closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    +    if (micBtn) {
    +    +      micBtn.style.top = (rect.top + 46 + 8) + "px";
    +    +      micBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    +    }
    +       }
    +     
            overlay.classList.add("active");
    -       composeActive = true;
    -       composerVisible = true;
    -    @@ -2320,6 +2338,13 @@ function hideComposeOverlay() {
    +    @@ -2317,6 +2338,7 @@ function showComposeOverlay() {
    +       setFlowMenuOpen(false);
    +       window.requestAnimationFrame(() => {
    +         input.focus();
    +    +    input.setSelectionRange(input.value.length, input.value.length);
    +         autoExpandTextarea(input);
    +       });
    +     }
    +    @@ -2338,12 +2360,20 @@ function hideComposeOverlay() {
              }
            }
          
    -    +  // Clear inline positioning from compose-close-btn
    -    +  const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    -    +  if (closeBtn) {
    -    +    closeBtn.style.top = "";
    -    +    closeBtn.style.right = "";
    -    +  }
    +    -  // Clear inline positioning from compose-close-btn
    +    +  // Stop dictation if running
    +    +  stopComposeDictation();
         +
    +    +  // Clear inline positioning from compose-close-btn and compose-mic-btn
    +       const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    +       if (closeBtn) {
    +         closeBtn.style.top = "";
    +         closeBtn.style.right = "";
    +       }
    +    +  const micBtn = overlay.querySelector(".compose-mic-btn") as HTMLElement | null;
    +    +  if (micBtn) {
    +    +    micBtn.style.top = "";
    +    +    micBtn.style.right = "";
    +    +  }
    +     
            overlay.classList.remove("active");
            composeActive = false;
    -       composerVisible = false;
    -    @@ -2397,19 +2422,15 @@ function syncFlowMenuVisibility() {
    -       if (!flowMenuContainer) return;
    -       const trigger = document.getElementById("flow-menu-trigger");
    -       if (composerVisible) {
    -    -    // Show trigger as a red ├ö┬ú├▓ close button instead of hiding it
    -    -    flowMenuContainer.classList.remove("hidden");
    -    -    if (trigger) {
    -    -      trigger.classList.add("close-mode");
    -    -      trigger.textContent = "├ö┬ú├▓";
    -    -      trigger.setAttribute("aria-label", "Close composer");
    -    -    }
    -    -    // Hide the dropdown while in close mode
    -    +    // Hide the flow-menu trigger (compose overlay has its own close button)
    -    +    flowMenuContainer.classList.add("hidden");
    -    +    // Hide the dropdown while in compose mode
    -         if (flowMenuDropdown) {
    -           flowMenuDropdown.style.display = "none";
    -           flowMenuDropdown.classList.remove("open");
    -         }
    -       } else {
    -    +    flowMenuContainer.classList.remove("hidden");
    -         if (trigger) {
    -           trigger.classList.remove("close-mode");
    -           trigger.textContent = "├ö├£├û";
    +    @@ -2357,6 +2387,97 @@ function autoExpandTextarea(el: HTMLTextAreaElement) {
    +       el.style.height = Math.min(el.scrollHeight, 200) + "px";
    +     }
    +     
    +    +// ├ö├Â├ç├ö├Â├ç Compose dictation (Web Speech API) ├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç├ö├Â├ç
    +    +function getSpeechRecognitionCtor(): any {
    +    +  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
    +    +}
    +    +
    +    +function toggleComposeDictation() {
    +    +  if (dictationActive) {
    +    +    stopComposeDictation();
    +    +  } else {
    +    +    startComposeDictation();
    +    +  }
    +    +}
    +    +
    +    +function startComposeDictation() {
    +    +  const SRCtor = getSpeechRecognitionCtor();
    +    +  if (!SRCtor) {
    +    +    setDuetStatus("Voice dictation is not supported on this browser.", false);
    +    +    const micBtn = composeOverlay?.querySelector(".compose-mic-btn") as HTMLElement | null;
    +    +    if (micBtn) micBtn.classList.add("disabled");
    +    +    return;
    +    +  }
    +    +  const input = document.getElementById("duet-input") as HTMLTextAreaElement | null;
    +    +  if (!input) return;
    +    +
    +    +  const sr = new SRCtor();
    +    +  sr.continuous = true;
    +    +  sr.interimResults = true;
    +    +  sr.lang = "en-US";
    +    +
    +    +  // Track the text that existed before dictation started
    +    +  const baseText = input.value;
    +    +
    +    +  sr.onresult = (event: any) => {
    +    +    let interim = "";
    +    +    let final = "";
    +    +    for (let i = 0; i < event.results.length; i++) {
    +    +      const transcript = event.results[i][0].transcript;
    +    +      if (event.results[i].isFinal) {
    +    +        final += transcript;
    +    +      } else {
    +    +        interim += transcript;
    +    +      }
    +    +    }
    +    +    const separator = baseText.length > 0 && !baseText.endsWith(" ") ? " " : "";
    +    +    input.value = baseText + separator + final + interim;
    +    +    autoExpandTextarea(input);
    +    +    input.setSelectionRange(input.value.length, input.value.length);
    +    +  };
    +    +
    +    +  sr.onerror = (event: any) => {
    +    +    if (event.error !== "aborted" && event.error !== "no-speech") {
    +    +      setDuetStatus("Dictation error: " + event.error, false);
    +    +    }
    +    +    stopComposeDictation();
    +    +  };
    +    +
    +    +  sr.onend = () => {
    +    +    // If still marked active, recognition stopped unexpectedly ├ö├ç├Â update UI
    +    +    if (dictationActive) {
    +    +      dictationActive = false;
    +    +      updateMicButtonState();
    +    +    }
    +    +  };
    +    +
    +    +  try {
    +    +    sr.start();
    +    +    speechRecognition = sr;
    +    +    dictationActive = true;
    +    +    updateMicButtonState();
    +    +  } catch (e) {
    +    +    setDuetStatus("Could not start dictation.", false);
    +    +  }
    +    +}
    +    +
    +    +function stopComposeDictation() {
    +    +  if (!dictationActive && !speechRecognition) return;
    +    +  dictationActive = false;
    +    +  if (speechRecognition) {
    +    +    try { speechRecognition.stop(); } catch (_) { /* ignore */ }
    +    +    speechRecognition = null;
    +    +  }
    +    +  updateMicButtonState();
    +    +}
    +    +
    +    +function updateMicButtonState() {
    +    +  const micBtn = composeOverlay?.querySelector(".compose-mic-btn") as HTMLElement | null;
    +    +  if (!micBtn) return;
    +    +  micBtn.classList.toggle("recording", dictationActive);
    +    +  micBtn.setAttribute("aria-label", dictationActive ? "Stop voice dictation" : "Start voice dictation");
    +    +}
    +    +
    +     function wireComposeOverlayKeyboard() {
    +       // Use VisualViewport to keep compose overlay centered above keyboard on iOS
    +       if (typeof window === "undefined") return;
         diff --git a/web/src/style.css b/web/src/style.css
    -    index a94e659..08e5f8c 100644
    +    index 08e5f8c..7563518 100644
         --- a/web/src/style.css
         +++ b/web/src/style.css
    -    @@ -275,6 +275,33 @@ pre {
    -       transform: translateY(-1px);
    +    @@ -302,6 +302,49 @@ pre {
    +       background: rgba(239, 68, 68, 1);
          }
          
    -    +/* Close button inside compose overlay */
    -    +.compose-close-btn {
    +    +/* Mic button inside compose overlay (below close btn) */
    +    +.compose-mic-btn {
         +  position: absolute;
    -    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +    +  top: max(144px, calc(env(safe-area-inset-top) + 134px));
         +  right: 22px;
         +  z-index: 2;
         +  margin: 0;
         +  width: 46px;
         +  height: 46px;
         +  border-radius: 12px;
    -    +  border: 1px solid rgba(248, 113, 113, 0.5);
    -    +  background: rgba(220, 38, 38, 0.85);
    -    +  color: #fff;
    -    +  font-size: 18px;
    -    +  font-weight: 700;
    +    +  border: 1px solid rgba(255, 255, 255, 0.16);
    +    +  background: rgba(255, 255, 255, 0.08);
    +    +  color: var(--text);
    +    +  font-size: 20px;
         +  display: inline-flex;
         +  align-items: center;
         +  justify-content: center;
         +  cursor: pointer;
         +  box-shadow: var(--shadow);
    -    +  transition: background 120ms ease;
    +    +  transition: background 120ms ease, border-color 120ms ease;
    +    +}
    +    +
    +    +.compose-mic-btn:hover {
    +    +  background: rgba(255, 255, 255, 0.14);
    +    +}
    +    +
    +    +.compose-mic-btn.recording {
    +    +  background: rgba(220, 38, 38, 0.85);
    +    +  border-color: rgba(248, 113, 113, 0.5);
    +    +  color: #fff;
    +    +  animation: mic-pulse 1.2s ease-in-out infinite;
    +    +}
    +    +
    +    +.compose-mic-btn.disabled {
    +    +  opacity: 0.35;
    +    +  cursor: not-allowed;
         +}
         +
    -    +.compose-close-btn:hover {
    -    +  background: rgba(239, 68, 68, 1);
    +    +@keyframes mic-pulse {
    +    +  0%, 100% { box-shadow: var(--shadow); }
    +    +  50% { box-shadow: 0 0 16px 4px rgba(239, 68, 68, 0.4); }
         +}
         +
          .flow-menu-dropdown {
            position: absolute;
            top: calc(100% + 6px);
    -    @@ -802,9 +829,9 @@ pre {
    -     .compose-overlay-backdrop {
    -       position: absolute;
    -       inset: 0;
    -    -  background: rgba(5, 12, 20, 0.45);
    -    -  backdrop-filter: blur(6px);
    -    -  -webkit-backdrop-filter: blur(6px);
    -    +  background: rgba(5, 12, 20, 0.18);
    -    +  backdrop-filter: blur(2px);
    -    +  -webkit-backdrop-filter: blur(2px);
    -     }
    -     
    -     .compose-narrator {
     
     ## Verification
    -- Static: `tsc --noEmit` ÔÇö 1 pre-existing TS2339 (line 1174), no new errors
    -- Runtime: pytest 183 passed, 1 warning in 114.07s
    +- Static: `tsc --noEmit` ÔÇö 1 pre-existing TS2339 (line 1176), no new errors
    +- Static: `tsc -p tsconfig.json --noCheck` ÔÇö build emits successfully
    +- Runtime: pytest 183 passed, 1 warning in 119.29s
     - Runtime: node ui_onboarding_hints_test.mjs ÔÇö 17/17 PASS
     - Runtime: node ui_proposal_renderer_test.mjs ÔÇö 3/3 PASS
    -- Contract: physics.yaml unchanged; 1 CSS property added; no refactors
    +- Contract: physics.yaml unchanged; minimal diff; no refactors
     
     ## Notes
    -- Global rule `button { margin-top: 6px }` at style.css L180 affects all `<button>` elements. `.flow-menu-toggle` also inherits this margin but `getBoundingClientRect()` captures its actual rendered position (post-margin), so the rect is accurate. The fix ensures `.compose-close-btn`'s margin-box matches its border-box.
    +- Web Speech API requires HTTPS or localhost on most browsers. iOS Safari supports it natively.
    +- `sr.continuous = true` keeps recognition running until explicitly stopped.
    +- `sr.interimResults = true` provides live word-by-word updates.
    +- `baseText` captured at dictation start ensures existing typed text is preserved.
     
     ## Next Steps
    -- Physical iPhone Safari testing: confirm close button pixel-aligned with gear button
    +- Physical iPhone Safari testing: confirm auto-focus keyboard, mic start/stop, live transcription
     - Phase 6C: Render deployment + smoke tests
     
    diff --git a/web/dist/main.js b/web/dist/main.js
    index 4cde744..2215814 100644
    --- a/web/dist/main.js
    +++ b/web/dist/main.js
    @@ -224,6 +224,8 @@ let composeActive = false;
     let composeDblTapTimer = null;
     let composeDblTapCount = 0;
     const COMPOSE_DBL_TAP_WINDOW_MS = 350;
    +let dictationActive = false;
    +let speechRecognition = null;
     function headers() {
         var _a;
         const h = { "Content-Type": "application/json" };
    @@ -2120,6 +2122,14 @@ function ensureComposeOverlay() {
         closeBtn.setAttribute("aria-label", "Close composer");
         closeBtn.addEventListener("click", () => hideComposeOverlay());
         overlay.appendChild(closeBtn);
    +    // Mic button inside overlay (below close btn, same style)
    +    const micBtn = document.createElement("button");
    +    micBtn.type = "button";
    +    micBtn.className = "compose-mic-btn";
    +    micBtn.textContent = "\uD83C\uDFA4";
    +    micBtn.setAttribute("aria-label", "Toggle voice dictation");
    +    micBtn.addEventListener("click", () => toggleComposeDictation());
    +    overlay.appendChild(micBtn);
         const narrator = document.createElement("div");
         narrator.className = "compose-narrator";
         overlay.appendChild(narrator);
    @@ -2134,6 +2144,10 @@ function ensureComposeOverlay() {
         return overlay;
     }
     function handleComposeBackdropTap() {
    +    // Single tap on backdrop stops dictation (if running) without sending
    +    if (dictationActive) {
    +        stopComposeDictation();
    +    }
         composeDblTapCount += 1;
         if (composeDblTapTimer !== null) {
             window.clearTimeout(composeDblTapTimer);
    @@ -2153,6 +2167,7 @@ function handleComposeBackdropTap() {
     }
     function composeOverlaySend() {
         var _a, _b;
    +    stopComposeDictation();
         const input = document.getElementById("duet-input");
         const text = (_a = input === null || input === void 0 ? void 0 : input.value.trim()) !== null && _a !== void 0 ? _a : "";
         if (!text || composerBusy)
    @@ -2181,13 +2196,20 @@ function showComposeOverlay() {
         // Move input into narrator container
         const narrator = overlay.querySelector(".compose-narrator");
         narrator.insertBefore(input, narrator.firstChild);
    -    // Position close button to match original flow-menu-trigger location
    +    // Position mic button where flow-menu-trigger (gear) is, close button where history-toggle is
         const fmTrigger = document.getElementById("flow-menu-trigger");
    +    const htToggle = document.getElementById("duet-history-toggle");
         const closeBtn = overlay.querySelector(".compose-close-btn");
    -    if (fmTrigger && closeBtn) {
    -        const rect = fmTrigger.getBoundingClientRect();
    -        closeBtn.style.top = rect.top + "px";
    -        closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +    const micBtn = overlay.querySelector(".compose-mic-btn");
    +    if (fmTrigger && micBtn) {
    +        const fmRect = fmTrigger.getBoundingClientRect();
    +        micBtn.style.top = fmRect.top + "px";
    +        micBtn.style.right = (window.innerWidth - fmRect.right) + "px";
    +    }
    +    if (htToggle && closeBtn) {
    +        const htRect = htToggle.getBoundingClientRect();
    +        closeBtn.style.top = htRect.top + "px";
    +        closeBtn.style.right = (window.innerWidth - htRect.right) + "px";
         }
         overlay.classList.add("active");
         composeActive = true;
    @@ -2203,6 +2225,7 @@ function showComposeOverlay() {
         setFlowMenuOpen(false);
         window.requestAnimationFrame(() => {
             input.focus();
    +        input.setSelectionRange(input.value.length, input.value.length);
             autoExpandTextarea(input);
         });
     }
    @@ -2224,12 +2247,19 @@ function hideComposeOverlay() {
                 composer.appendChild(input);
             }
         }
    -    // Clear inline positioning from compose-close-btn
    +    // Stop dictation if running
    +    stopComposeDictation();
    +    // Clear inline positioning from compose-close-btn and compose-mic-btn
         const closeBtn = overlay.querySelector(".compose-close-btn");
         if (closeBtn) {
             closeBtn.style.top = "";
             closeBtn.style.right = "";
         }
    +    const micBtn = overlay.querySelector(".compose-mic-btn");
    +    if (micBtn) {
    +        micBtn.style.top = "";
    +        micBtn.style.right = "";
    +    }
         overlay.classList.remove("active");
         composeActive = false;
         composerVisible = false;
    @@ -2240,6 +2270,96 @@ function autoExpandTextarea(el) {
         el.style.height = "auto";
         el.style.height = Math.min(el.scrollHeight, 200) + "px";
     }
    +// ÔöÇÔöÇ Compose dictation (Web Speech API) ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
    +function getSpeechRecognitionCtor() {
    +    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
    +}
    +function toggleComposeDictation() {
    +    if (dictationActive) {
    +        stopComposeDictation();
    +    }
    +    else {
    +        startComposeDictation();
    +    }
    +}
    +function startComposeDictation() {
    +    const SRCtor = getSpeechRecognitionCtor();
    +    if (!SRCtor) {
    +        setDuetStatus("Voice dictation is not supported on this browser.", false);
    +        const micBtn = composeOverlay === null || composeOverlay === void 0 ? void 0 : composeOverlay.querySelector(".compose-mic-btn");
    +        if (micBtn)
    +            micBtn.classList.add("disabled");
    +        return;
    +    }
    +    const input = document.getElementById("duet-input");
    +    if (!input)
    +        return;
    +    const sr = new SRCtor();
    +    sr.continuous = true;
    +    sr.interimResults = true;
    +    sr.lang = "en-US";
    +    // Track the text that existed before dictation started
    +    const baseText = input.value;
    +    sr.onresult = (event) => {
    +        let interim = "";
    +        let final = "";
    +        for (let i = 0; i < event.results.length; i++) {
    +            const transcript = event.results[i][0].transcript;
    +            if (event.results[i].isFinal) {
    +                final += transcript;
    +            }
    +            else {
    +                interim += transcript;
    +            }
    +        }
    +        const separator = baseText.length > 0 && !baseText.endsWith(" ") ? " " : "";
    +        input.value = baseText + separator + final + interim;
    +        autoExpandTextarea(input);
    +        input.setSelectionRange(input.value.length, input.value.length);
    +    };
    +    sr.onerror = (event) => {
    +        if (event.error !== "aborted" && event.error !== "no-speech") {
    +            setDuetStatus("Dictation error: " + event.error, false);
    +        }
    +        stopComposeDictation();
    +    };
    +    sr.onend = () => {
    +        // If still marked active, recognition stopped unexpectedly ÔÇö update UI
    +        if (dictationActive) {
    +            dictationActive = false;
    +            updateMicButtonState();
    +        }
    +    };
    +    try {
    +        sr.start();
    +        speechRecognition = sr;
    +        dictationActive = true;
    +        updateMicButtonState();
    +    }
    +    catch (e) {
    +        setDuetStatus("Could not start dictation.", false);
    +    }
    +}
    +function stopComposeDictation() {
    +    if (!dictationActive && !speechRecognition)
    +        return;
    +    dictationActive = false;
    +    if (speechRecognition) {
    +        try {
    +            speechRecognition.stop();
    +        }
    +        catch (_) { /* ignore */ }
    +        speechRecognition = null;
    +    }
    +    updateMicButtonState();
    +}
    +function updateMicButtonState() {
    +    const micBtn = composeOverlay === null || composeOverlay === void 0 ? void 0 : composeOverlay.querySelector(".compose-mic-btn");
    +    if (!micBtn)
    +        return;
    +    micBtn.classList.toggle("recording", dictationActive);
    +    micBtn.setAttribute("aria-label", dictationActive ? "Stop voice dictation" : "Start voice dictation");
    +}
     function wireComposeOverlayKeyboard() {
         // Use VisualViewport to keep compose overlay centered above keyboard on iOS
         if (typeof window === "undefined")
    diff --git a/web/dist/style.css b/web/dist/style.css
    index 08e5f8c..aa42a34 100644
    --- a/web/dist/style.css
    +++ b/web/dist/style.css
    @@ -278,7 +278,7 @@ pre {
     /* Close button inside compose overlay */
     .compose-close-btn {
       position: absolute;
    -  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +  top: max(32px, calc(env(safe-area-inset-top) + 22px));
       right: 22px;
       z-index: 2;
       margin: 0;
    @@ -302,6 +302,49 @@ pre {
       background: rgba(239, 68, 68, 1);
     }
     
    +/* Mic button inside compose overlay (at gear/options position) */
    +.compose-mic-btn {
    +  position: absolute;
    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +  right: 22px;
    +  z-index: 2;
    +  margin: 0;
    +  width: 46px;
    +  height: 46px;
    +  border-radius: 12px;
    +  border: 1px solid rgba(255, 255, 255, 0.16);
    +  background: rgba(255, 255, 255, 0.08);
    +  color: var(--text);
    +  font-size: 20px;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  cursor: pointer;
    +  box-shadow: var(--shadow);
    +  transition: background 120ms ease, border-color 120ms ease;
    +}
    +
    +.compose-mic-btn:hover {
    +  background: rgba(255, 255, 255, 0.14);
    +}
    +
    +.compose-mic-btn.recording {
    +  background: rgba(220, 38, 38, 0.85);
    +  border-color: rgba(248, 113, 113, 0.5);
    +  color: #fff;
    +  animation: mic-pulse 1.2s ease-in-out infinite;
    +}
    +
    +.compose-mic-btn.disabled {
    +  opacity: 0.35;
    +  cursor: not-allowed;
    +}
    +
    +@keyframes mic-pulse {
    +  0%, 100% { box-shadow: var(--shadow); }
    +  50% { box-shadow: 0 0 16px 4px rgba(239, 68, 68, 0.4); }
    +}
    +
     .flow-menu-dropdown {
       position: absolute;
       top: calc(100% + 6px);
    diff --git a/web/src/main.ts b/web/src/main.ts
    index 4e8a831..f2b2bf7 100644
    --- a/web/src/main.ts
    +++ b/web/src/main.ts
    @@ -237,6 +237,8 @@ let composeActive = false;
     let composeDblTapTimer: number | null = null;
     let composeDblTapCount = 0;
     const COMPOSE_DBL_TAP_WINDOW_MS = 350;
    +let dictationActive = false;
    +let speechRecognition: any = null;
     
     function headers() {
       const h: Record<string, string> = { "Content-Type": "application/json" };
    @@ -2227,6 +2229,15 @@ function ensureComposeOverlay(): HTMLDivElement {
       closeBtn.addEventListener("click", () => hideComposeOverlay());
       overlay.appendChild(closeBtn);
     
    +  // Mic button inside overlay (below close btn, same style)
    +  const micBtn = document.createElement("button");
    +  micBtn.type = "button";
    +  micBtn.className = "compose-mic-btn";
    +  micBtn.textContent = "\uD83C\uDFA4";
    +  micBtn.setAttribute("aria-label", "Toggle voice dictation");
    +  micBtn.addEventListener("click", () => toggleComposeDictation());
    +  overlay.appendChild(micBtn);
    +
       const narrator = document.createElement("div");
       narrator.className = "compose-narrator";
       overlay.appendChild(narrator);
    @@ -2246,6 +2257,10 @@ function ensureComposeOverlay(): HTMLDivElement {
     }
     
     function handleComposeBackdropTap() {
    +  // Single tap on backdrop stops dictation (if running) without sending
    +  if (dictationActive) {
    +    stopComposeDictation();
    +  }
       composeDblTapCount += 1;
       if (composeDblTapTimer !== null) {
         window.clearTimeout(composeDblTapTimer);
    @@ -2264,6 +2279,7 @@ function handleComposeBackdropTap() {
     }
     
     function composeOverlaySend() {
    +  stopComposeDictation();
       const input = document.getElementById("duet-input") as HTMLTextAreaElement | null;
       const text = input?.value.trim() ?? "";
       if (!text || composerBusy) return;
    @@ -2292,13 +2308,20 @@ function showComposeOverlay() {
       const narrator = overlay.querySelector(".compose-narrator") as HTMLElement;
       narrator.insertBefore(input, narrator.firstChild);
     
    -  // Position close button to match original flow-menu-trigger location
    +  // Position mic button where flow-menu-trigger (gear) is, close button where history-toggle is
       const fmTrigger = document.getElementById("flow-menu-trigger");
    +  const htToggle = document.getElementById("duet-history-toggle");
       const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
    -  if (fmTrigger && closeBtn) {
    -    const rect = fmTrigger.getBoundingClientRect();
    -    closeBtn.style.top = rect.top + "px";
    -    closeBtn.style.right = (window.innerWidth - rect.right) + "px";
    +  const micBtn = overlay.querySelector(".compose-mic-btn") as HTMLElement | null;
    +  if (fmTrigger && micBtn) {
    +    const fmRect = fmTrigger.getBoundingClientRect();
    +    micBtn.style.top = fmRect.top + "px";
    +    micBtn.style.right = (window.innerWidth - fmRect.right) + "px";
    +  }
    +  if (htToggle && closeBtn) {
    +    const htRect = htToggle.getBoundingClientRect();
    +    closeBtn.style.top = htRect.top + "px";
    +    closeBtn.style.right = (window.innerWidth - htRect.right) + "px";
       }
     
       overlay.classList.add("active");
    @@ -2317,6 +2340,7 @@ function showComposeOverlay() {
       setFlowMenuOpen(false);
       window.requestAnimationFrame(() => {
         input.focus();
    +    input.setSelectionRange(input.value.length, input.value.length);
         autoExpandTextarea(input);
       });
     }
    @@ -2338,12 +2362,20 @@ function hideComposeOverlay() {
         }
       }
     
    -  // Clear inline positioning from compose-close-btn
    +  // Stop dictation if running
    +  stopComposeDictation();
    +
    +  // Clear inline positioning from compose-close-btn and compose-mic-btn
       const closeBtn = overlay.querySelector(".compose-close-btn") as HTMLElement | null;
       if (closeBtn) {
         closeBtn.style.top = "";
         closeBtn.style.right = "";
       }
    +  const micBtn = overlay.querySelector(".compose-mic-btn") as HTMLElement | null;
    +  if (micBtn) {
    +    micBtn.style.top = "";
    +    micBtn.style.right = "";
    +  }
     
       overlay.classList.remove("active");
       composeActive = false;
    @@ -2357,6 +2389,97 @@ function autoExpandTextarea(el: HTMLTextAreaElement) {
       el.style.height = Math.min(el.scrollHeight, 200) + "px";
     }
     
    +// ÔöÇÔöÇ Compose dictation (Web Speech API) ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
    +function getSpeechRecognitionCtor(): any {
    +  return (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition || null;
    +}
    +
    +function toggleComposeDictation() {
    +  if (dictationActive) {
    +    stopComposeDictation();
    +  } else {
    +    startComposeDictation();
    +  }
    +}
    +
    +function startComposeDictation() {
    +  const SRCtor = getSpeechRecognitionCtor();
    +  if (!SRCtor) {
    +    setDuetStatus("Voice dictation is not supported on this browser.", false);
    +    const micBtn = composeOverlay?.querySelector(".compose-mic-btn") as HTMLElement | null;
    +    if (micBtn) micBtn.classList.add("disabled");
    +    return;
    +  }
    +  const input = document.getElementById("duet-input") as HTMLTextAreaElement | null;
    +  if (!input) return;
    +
    +  const sr = new SRCtor();
    +  sr.continuous = true;
    +  sr.interimResults = true;
    +  sr.lang = "en-US";
    +
    +  // Track the text that existed before dictation started
    +  const baseText = input.value;
    +
    +  sr.onresult = (event: any) => {
    +    let interim = "";
    +    let final = "";
    +    for (let i = 0; i < event.results.length; i++) {
    +      const transcript = event.results[i][0].transcript;
    +      if (event.results[i].isFinal) {
    +        final += transcript;
    +      } else {
    +        interim += transcript;
    +      }
    +    }
    +    const separator = baseText.length > 0 && !baseText.endsWith(" ") ? " " : "";
    +    input.value = baseText + separator + final + interim;
    +    autoExpandTextarea(input);
    +    input.setSelectionRange(input.value.length, input.value.length);
    +  };
    +
    +  sr.onerror = (event: any) => {
    +    if (event.error !== "aborted" && event.error !== "no-speech") {
    +      setDuetStatus("Dictation error: " + event.error, false);
    +    }
    +    stopComposeDictation();
    +  };
    +
    +  sr.onend = () => {
    +    // If still marked active, recognition stopped unexpectedly ÔÇö update UI
    +    if (dictationActive) {
    +      dictationActive = false;
    +      updateMicButtonState();
    +    }
    +  };
    +
    +  try {
    +    sr.start();
    +    speechRecognition = sr;
    +    dictationActive = true;
    +    updateMicButtonState();
    +  } catch (e) {
    +    setDuetStatus("Could not start dictation.", false);
    +  }
    +}
    +
    +function stopComposeDictation() {
    +  if (!dictationActive && !speechRecognition) return;
    +  dictationActive = false;
    +  if (speechRecognition) {
    +    try { speechRecognition.stop(); } catch (_) { /* ignore */ }
    +    speechRecognition = null;
    +  }
    +  updateMicButtonState();
    +}
    +
    +function updateMicButtonState() {
    +  const micBtn = composeOverlay?.querySelector(".compose-mic-btn") as HTMLElement | null;
    +  if (!micBtn) return;
    +  micBtn.classList.toggle("recording", dictationActive);
    +  micBtn.setAttribute("aria-label", dictationActive ? "Stop voice dictation" : "Start voice dictation");
    +}
    +
     function wireComposeOverlayKeyboard() {
       // Use VisualViewport to keep compose overlay centered above keyboard on iOS
       if (typeof window === "undefined") return;
    diff --git a/web/src/style.css b/web/src/style.css
    index 08e5f8c..aa42a34 100644
    --- a/web/src/style.css
    +++ b/web/src/style.css
    @@ -278,7 +278,7 @@ pre {
     /* Close button inside compose overlay */
     .compose-close-btn {
       position: absolute;
    -  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +  top: max(32px, calc(env(safe-area-inset-top) + 22px));
       right: 22px;
       z-index: 2;
       margin: 0;
    @@ -302,6 +302,49 @@ pre {
       background: rgba(239, 68, 68, 1);
     }
     
    +/* Mic button inside compose overlay (at gear/options position) */
    +.compose-mic-btn {
    +  position: absolute;
    +  top: max(90px, calc(env(safe-area-inset-top) + 80px));
    +  right: 22px;
    +  z-index: 2;
    +  margin: 0;
    +  width: 46px;
    +  height: 46px;
    +  border-radius: 12px;
    +  border: 1px solid rgba(255, 255, 255, 0.16);
    +  background: rgba(255, 255, 255, 0.08);
    +  color: var(--text);
    +  font-size: 20px;
    +  display: inline-flex;
    +  align-items: center;
    +  justify-content: center;
    +  cursor: pointer;
    +  box-shadow: var(--shadow);
    +  transition: background 120ms ease, border-color 120ms ease;
    +}
    +
    +.compose-mic-btn:hover {
    +  background: rgba(255, 255, 255, 0.14);
    +}
    +
    +.compose-mic-btn.recording {
    +  background: rgba(220, 38, 38, 0.85);
    +  border-color: rgba(248, 113, 113, 0.5);
    +  color: #fff;
    +  animation: mic-pulse 1.2s ease-in-out infinite;
    +}
    +
    +.compose-mic-btn.disabled {
    +  opacity: 0.35;
    +  cursor: not-allowed;
    +}
    +
    +@keyframes mic-pulse {
    +  0%, 100% { box-shadow: var(--shadow); }
    +  50% { box-shadow: 0 0 16px 4px rgba(239, 68, 68, 0.4); }
    +}
    +
     .flow-menu-dropdown {
       position: absolute;
       top: calc(100% + 6px);

## Verification
- Static: `tsc --noEmit` — 1 pre-existing TS2339 (line 1176), no new errors
- Static: `tsc -p tsconfig.json --noCheck` — build emits successfully
- Runtime: pytest 183 passed, 1 warning in 118.71s
- Runtime: node ui_onboarding_hints_test.mjs — 17/17 PASS
- Runtime: node ui_proposal_renderer_test.mjs — 3/3 PASS
- Contract: physics.yaml unchanged; minimal diff; no refactors

## Notes
- Both buttons remain inside `.compose-overlay` (z-index 100, fixed on body) so they stay above all duet-shell children.
- Inline styles from `getBoundingClientRect()` override CSS fallback tops.

## Next Steps
- Physical iPhone Safari testing: confirm Mic at old X position, X at history toggle position
- Phase 6C: Render deployment + smoke tests

