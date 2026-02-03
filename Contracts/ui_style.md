# Little Chef — UI Style Spec (v0.1)

Status: Draft (authoritative for v0.1 UI look/feel)  
Owner: Julius  
Purpose: Define the visual language so UI work stays consistent and does not drift.

---

## 1) Visual language

Target vibe:
- Multicoloured blurred gradient background
- Glass-style (glassmorphism) tabs/panels everywhere
- Clean, modern, “soft neon” accents
- Mobile-first, PWA-friendly

Non-goals (v0.1):
- Heavy animations
- Complex themes system / theme editor
- Multiple theme packs

---

## 2) Foundations (rules)

### Background
- Use 1–2 layered gradients (radial + linear is fine).
- Background must feel “alive” but remain readable under glass panels.
- Optional subtle noise overlay (very light), but avoid heavy textures.

### Glass surfaces
All primary UI surfaces (tabs/cards/modals/nav) use a glass panel:
- translucent fill (not opaque)
- blur via backdrop filter when supported
- thin border + soft shadow
- rounded corners

### Readability
- Glass panels must maintain readable contrast for body text.
- Always have a “fallback” for blur-off environments: slightly more opaque surface.

### Motion
- Prefer subtle transitions only (hover/press/focus).
- Respect reduced motion (no constant background movement by default).

---

## 3) Component styling (minimum set)

### Tabs (primary UI pattern)
- Tabs look like glass chips/pills.
- Active tab: slightly brighter surface + clearer border + optional glow.
- Inactive tabs: slightly dimmer with hover brighten.

### Cards / Panels
- Same glass styling as tabs, but larger padding and less glow.
- Used for dashboard sections: inventory, prefs summary, plan, shopping list.

### Inputs / Chat composer
- Glass input bar, clear focus ring, no harsh borders.
- Buttons are glass with a clear “press” state.

### Modals / Drawers
- Full-screen dim overlay (soft), modal is a glass panel.

---

## 4) Accessibility + UX constraints

- Must work on mobile and desktop.
- Focus rings must be visible (keyboard navigation).
- Text sizes must not be tiny; avoid low-contrast text on gradients.
- Provide a “High Contrast” toggle later (not MVP), but don’t block MVP on it.

---

## 5) Implementation tokens (not code, but the contract target)

These are the *design tokens* the CSS should implement.

- Background: multi-stop gradient(s), cool-to-warm mix
- Surface (glass):
  - blur: medium
  - fill: translucent
  - border: thin, translucent
  - shadow: soft
- Radius: medium-large (tabs slightly smaller than cards)
- Spacing: comfortable (no cramped UI)
- Accent: 1 primary accent + 1 secondary accent
- States:
  - hover: brighten
  - active: brighten + border clarity
  - focus: clear ring
  - disabled: dim

---

## 6) Minimal CSS starter (to be created when web/ exists)

When the web UI is scaffolded, create a single stylesheet implementing:
- background gradients
- glass panel base class
- tab styles
- input/button styles
- focus rings
- reduced motion handling

No additional style systems unless explicitly approved.

--- End of UI Style Spec ---
