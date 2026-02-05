# Phase 7.6 — Inventory conversational parsing & normalization (draft → confirm → write events)

## 1. Purpose
Voice-first “cupboard scan” input (speech or text) should be parsed into draft inventory items, normalized deterministically, surfaced with warnings, reviewed, and only then written as inventory events after confirm/edit/deny.

## 2. Scope
**In scope**
- Draft extraction from free-flow user text.
- Manual location toggle integration (pantry/fridge/freezer).
- Deterministic normalization (UK units + GB dates).
- Warning flags on ambiguous assumptions.
- Bulk confirm/edit/deny draft UX (no writes until confirm).
- Persist confirmed items as inventory_events (one event per item).

**Out of scope**
- Recall/retrieval.
- Auto-location.
- Batches/lots.
- Region/onboarding metrics.
- Advanced mid-stream corrections (handled via Edit at confirm step).

## 3. Data model assumptions (current repo)
- inventory_events fields: event_id, user_id, occurred_at, event_type (text), payload (JSON), created_at.
- Totals model: current inventory is aggregated by (item_key, location) over events.

## 4. Canonical item fields (nullable except name)
- name_raw (string; from user)
- base_name (string; canonical noun)
- variant (nullable string; descriptors)
- item_key (string; base_name if no variant; else base_name|variant)
- location (enum pantry|fridge|freezer; manual)
- quantity (number; normalized)
- unit (enum g|ml|count)
- expires_on (nullable ISO YYYY-MM-DD)
- notes (nullable string)

## 5. Payload schema (inventory_events.payload)
```
{
  "item": {base fields above},
  "normalization": {
    "quantity_raw": "...",
    "unit_raw": "...",
    "expires_raw": "...",
    "locale": "en-GB"
  },
  "warnings": ["..."],
  "parse_meta": {
    "source": "voice|text",
    "confidence": null|number
  }
}
```
Examples:
- Flour: “bag of flour, one kilo, no sell-by date” (pantry)
  - quantity=1000, unit=g, expires_on=null, item_key=flour, warnings=[]
- Hot dogs: “8 hot dogs, use by 12/03” (fridge)
  - quantity=8, unit=count, expires_on=YYYY-03-12 (GB DD/MM rule with year handling), warnings include DATE_PARSED_GB_NUMERIC
- Eggs: “12 eggs” (pantry)
  - quantity=12, unit=count, warnings include LOCATION_SUSPICIOUS (but location stored as pantry)

## 6. Normalization rules
**Units**
- Canonical: g, ml, count.
- Conversions: kg→g (x1000); l→ml (x1000).
- If quantity present, unit missing: assume g for obvious dry goods; add warning UNIT_ASSUMED_G.

**Dates**
- Normalize to ISO YYYY-MM-DD.
- GB numeric assumes DD/MM (or DD/MM/YYYY if provided).
- Missing year: assume current year; if date already passed, roll to next year; add DATE_PARSED_GB_NUMERIC warning.
- Unknown/no label → expires_on=null.

**Name/variant/item_key**
- base_name = core noun; variant = descriptors.
- item_key = base_name if variant empty else base_name + "|" + variant.

**Location**
- Manual toggle decides stored location.
- If suspicious (e.g., eggs in pantry), add LOCATION_SUSPICIOUS but do not block.

## 7. Warning/flag system (v0)
- UNIT_ASSUMED_G
- QUANTITY_ASSUMED_1 (if missing quantity and policy chooses 1; otherwise quantity may stay null)
- LOCATION_SUSPICIOUS
- DATE_PARSED_GB_NUMERIC
- EXPIRY_UNKNOWN

Warnings travel in payload for future “flagged items” UX; do not block writes.

## 8. Parsing pipeline (draft → review → confirm)
1) User enters Inventory and chooses manual location.
2) User provides free-flow text/voice list.
3) LLM extraction → DRAFT items (no DB writes).
4) Normalizer produces canonical fields + warnings.
5) UI review: Confirm (writes events), Edit (adjust draft), Deny (discard). No DB writes until Confirm.

## 9. LLM extraction contract (draft schema)
LLM returns JSON-only draft list:
- name_raw
- quantity_raw (optional)
- unit_raw (optional)
- expires_raw (optional)
- notes_raw (optional)
LLM does not decide location. Normalizer computes base_name/variant/key, units, dates.

## 10. Acceptance criteria
A) Pantry scan low friction  
- Input: “Cereal 500, flour one kilo, no sell by date”; location=pantry  
- Output: cereal quantity=500 unit=g (UNIT_ASSUMED_G if no unit); flour=1000g; expires_on null; one event per item on confirm.

B) GB date normalization  
- Input: “Hot dogs 8, use by 12/03”; location=fridge  
- Output: quantity=8 unit=count; expires_on ISO using DD/MM; warning DATE_PARSED_GB_NUMERIC.

C) Location suspicious warning  
- Input: “12 eggs”; location=pantry  
- Output: stored pantry; warnings include LOCATION_SUSPICIOUS.

D) Bulk confirm/edit/deny  
- Deny → zero events; Edit → change fields then confirm; Confirm → exactly N events for N items.

E) Totals model compatibility  
- Multiple adds with same item_key aggregate via events; no schema changes.

## 11. Test plan (future impl)
- Unit tests for normalization (units, dates, warnings).
- Mocked LLM extraction tests (no network).
- API tests ensuring confirm-before-write.
- Deterministic behavior gate.

## 12. Future enhancements (later)
- Auto-location suggestions.
- Onboarding for locale/units.
- Recall and flagged-item workflows.
- Voice confirm/edit/deny commands.
- Event type refinements.
