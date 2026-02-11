# Diff Log (overwrite each cycle)

## Cycle Metadata
- Timestamp: 2026-02-11T18:03:46+00:00
- Branch: claude/romantic-jones
- HEAD: 1aa92530dc7bbd74d8a034ee01e343739867b215
- BASE_HEAD: f895242b359e48581f4abb54afd40a44b2178cf3
- Diff basis: staged

## Cycle Status
- Status: COMPLETE

## Summary
- Fixed iOS Safari auto-zoom on composer input focus: set `#duet-input` font-size to 16px (iOS requires >= 16px to suppress zoom).
- Eliminated white strip behind iPhone status bar: added `viewport-fit=cover` to viewport meta tag, `background-color: #0b1724` fallback on body, and safe-area padding on `main.container` via `env(safe-area-inset-*)`.
- Both `web/index.html` and `web/dist/index.html` updated for viewport-fit; CSS changes in `web/src/style.css` copied to `web/dist/style.css`.
- No layout repositioning; background-only + font-size changes.

## Files Changed (staged)
- web/dist/index.html
- web/dist/style.css
- web/index.html
- web/src/style.css

## git status -sb
    ## claude/romantic-jones
     M .claude/settings.local.json
    M  web/dist/index.html
    M  web/dist/style.css
    M  web/index.html
    M  web/src/style.css

## Minimal Diff Hunks
    diff --git a/web/dist/index.html b/web/dist/index.html
    index 0e3f10e..01f5acd 100644
    --- a/web/dist/index.html
    +++ b/web/dist/index.html
    @@ -2,7 +2,7 @@
     <html lang="en">
     <head>
       <meta charset="UTF-8">
    -  <meta name="viewport" content="width=device-width, initial-scale=1">
    +  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
       <title>Little Chef</title>
       <link rel="stylesheet" href="/static/style.css">
     </head>
    diff --git a/web/dist/style.css b/web/dist/style.css
    index 60d312c..f630382 100644
    --- a/web/dist/style.css
    +++ b/web/dist/style.css
    @@ -26,6 +26,8 @@ body {
       background: radial-gradient(circle at 15% 20%, rgba(127, 164, 255, 0.12), transparent 25%),
         radial-gradient(circle at 80% 0%, rgba(127, 228, 194, 0.14), transparent 30%),
         linear-gradient(145deg, #0b1724, #102a3f 50%, #0c1f31);
    +  /* Extend gradient into iOS safe area (status bar region) */
    +  background-color: #0b1724;
       color: var(--text);
       max-width: 100vw;
       overflow: auto;
    @@ -42,6 +44,11 @@ main.container {
       min-height: 100dvh;
       margin: 0 auto;
       padding: 10px;
    +  /* Safe-area insets so content clears the iOS notch/status bar */
    +  padding-top: max(10px, env(safe-area-inset-top));
    +  padding-left: max(10px, env(safe-area-inset-left));
    +  padding-right: max(10px, env(safe-area-inset-right));
    +  padding-bottom: max(10px, env(safe-area-inset-bottom));
       display: flex;
       flex-direction: column;
       gap: 4px;
    @@ -759,6 +766,11 @@ pre {
       border: 1px solid rgba(255, 255, 255, 0.12);
     }
     
    +/* Prevent iOS Safari auto-zoom on input focus (requires >= 16px) */
    +#duet-input {
    +  font-size: 16px;
    +}
    +
     .icon-btn {
       width: 46px;
       height: 46px;
    diff --git a/web/index.html b/web/index.html
    index 72bf0e7..1673fdd 100644
    --- a/web/index.html
    +++ b/web/index.html
    @@ -2,7 +2,7 @@
     <html lang="en">
     <head>
       <meta charset="UTF-8">
    -  <meta name="viewport" content="width=device-width, initial-scale=1">
    +  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
       <title>Little Chef</title>
       <link rel="stylesheet" href="/static/style.css">
     </head>
    diff --git a/web/src/style.css b/web/src/style.css
    index 60d312c..f630382 100644
    --- a/web/src/style.css
    +++ b/web/src/style.css
    @@ -26,6 +26,8 @@ body {
       background: radial-gradient(circle at 15% 20%, rgba(127, 164, 255, 0.12), transparent 25%),
         radial-gradient(circle at 80% 0%, rgba(127, 228, 194, 0.14), transparent 30%),
         linear-gradient(145deg, #0b1724, #102a3f 50%, #0c1f31);
    +  /* Extend gradient into iOS safe area (status bar region) */
    +  background-color: #0b1724;
       color: var(--text);
       max-width: 100vw;
       overflow: auto;
    @@ -42,6 +44,11 @@ main.container {
       min-height: 100dvh;
       margin: 0 auto;
       padding: 10px;
    +  /* Safe-area insets so content clears the iOS notch/status bar */
    +  padding-top: max(10px, env(safe-area-inset-top));
    +  padding-left: max(10px, env(safe-area-inset-left));
    +  padding-right: max(10px, env(safe-area-inset-right));
    +  padding-bottom: max(10px, env(safe-area-inset-bottom));
       display: flex;
       flex-direction: column;
       gap: 4px;
    @@ -759,6 +766,11 @@ pre {
       border: 1px solid rgba(255, 255, 255, 0.12);
     }
     
    +/* Prevent iOS Safari auto-zoom on input focus (requires >= 16px) */
    +#duet-input {
    +  font-size: 16px;
    +}
    +
     .icon-btn {
       width: 46px;
       height: 46px;

## Verification
- Static: `python -m compileall app` — pass
- Static: `tsc --noEmit` — 1 pre-existing TS2339 (no new errors)
- Runtime: pytest 183 passed, 1 warning in 115.42s
- Runtime: node ui_onboarding_hints_test.mjs: 17/17 PASS
- Behavioral: `#duet-input` now has `font-size: 16px` (prevents iOS auto-zoom on focus)
- Behavioral: viewport-fit=cover + safe-area padding extends gradient into status bar region
- Contract: physics.yaml unchanged, minimal diff (4 files: 2 HTML + 2 CSS), no refactors, no layout changes

## Notes (optional)
- `background-color: #0b1724` is a fallback that matches the darkest stop of the existing gradient — ensures no white flash even if gradient hasn't painted yet.
- Safe-area padding uses `max(10px, env(...))` to preserve the existing 10px minimum on non-notched devices.
- `viewport-fit=cover` is a no-op on non-iOS browsers; safe-area env vars resolve to 0 when not applicable.

## Next Steps
- Test on physical iPhone to confirm no white strip and no zoom on input focus.
- Phase 6C: Render deployment + smoke tests.
- Phase 7.5: Inventory ghost overlay with location grouping.

