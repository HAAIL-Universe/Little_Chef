import re
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

RawItem = Dict[str, Optional[str]]

# Units the LLM is asked to return (plus conversions)
_VALID_UNITS = {
    "g", "ml", "count",
    "tin", "bag", "box", "jar", "bottle", "pack", "loaf", "slice", "piece",
    "bunch", "bulb", "head", "can", "carton", "tub", "pot",
}

_CONVERTIBLE = {
    "kg": ("g", 1000),
    "kilo": ("g", 1000),
    "kilos": ("g", 1000),
    "kilogram": ("g", 1000),
    "kilograms": ("g", 1000),
    "gram": ("g", 1),
    "grams": ("g", 1),
    "l": ("ml", 1000),
    "lt": ("ml", 1000),
    "litre": ("ml", 1000),
    "litres": ("ml", 1000),
    "liter": ("ml", 1000),
    "liters": ("ml", 1000),
    "tins": ("tin", 1),
    "bags": ("bag", 1),
    "boxes": ("box", 1),
    "jars": ("jar", 1),
    "bottles": ("bottle", 1),
    "packs": ("pack", 1),
    "loaves": ("loaf", 1),
    "slices": ("slice", 1),
    "pieces": ("piece", 1),
    "cans": ("can", 1),
    "cartons": ("carton", 1),
    "tubs": ("tub", 1),
    "pots": ("pot", 1),
    "bunches": ("bunch", 1),
    "bulbs": ("bulb", 1),
    "heads": ("head", 1),
}


def _parse_quantity_unit(raw_qty: Optional[str], raw_unit: Optional[str]) -> Tuple[Optional[float], Optional[str], List[str]]:
    warnings: List[str] = []
    if raw_qty is None or raw_qty == "":
        return None, None, warnings
    try:
        qty = float(str(raw_qty).replace(",", "."))
    except ValueError:
        return None, None, warnings
    unit = (raw_unit or "").lower().strip()

    # Direct match on valid units
    if unit in _VALID_UNITS:
        return qty, unit, warnings

    # Convertible units (kg→g, l→ml, plurals→singular)
    if unit in _CONVERTIBLE:
        target, multiplier = _CONVERTIBLE[unit]
        return qty * multiplier, target, warnings

    # Empty/missing unit — default to count for countable things, g otherwise
    if unit == "":
        unit = "count"
        warnings.append("UNIT_ASSUMED_COUNT")
        return qty, unit, warnings

    # Unrecognised unit — keep as-is but warn
    warnings.append(f"UNIT_UNRECOGNISED:{unit}")
    return qty, unit, warnings


_DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "weds": 2,
    "thu": 3, "thur": 3, "thurs": 3, "fri": 4, "sat": 5, "sun": 6,
}


def _parse_date_gb(raw: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """Parse expiry date from various formats including ISO, GB numeric, and relative."""
    warnings: List[str] = []
    if not raw:
        warnings.append("EXPIRY_UNKNOWN")
        return None, warnings

    text = raw.strip().lower()

    # Already ISO format (YYYY-MM-DD)? The LLM is instructed to return this.
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if iso_match:
        try:
            cand = date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
            return cand.isoformat(), warnings
        except ValueError:
            pass

    # Relative: "tomorrow", "today", "in N days"
    today = date.today()
    if text == "tomorrow":
        return (today + timedelta(days=1)).isoformat(), warnings
    if text == "today":
        return today.isoformat(), warnings
    in_days = re.match(r"in\s+(\d+)\s+days?", text)
    if in_days:
        return (today + timedelta(days=int(in_days.group(1)))).isoformat(), warnings

    # Day name: "thursday", "friday" etc → next occurrence
    for name, weekday in _DAY_NAMES.items():
        if text == name or text.startswith(name + " "):
            days_ahead = (weekday - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7  # next week if today
            return (today + timedelta(days=days_ahead)).isoformat(), warnings

    # GB numeric: dd/mm or dd/mm/yyyy
    parts = text.replace("-", "/").split("/")
    try:
        if len(parts) == 2:
            day, month = map(int, parts)
            year = today.year
            cand = date(year, month, day)
            if cand < today:
                cand = date(year + 1, month, day)
            warnings.append("DATE_PARSED_GB_NUMERIC")
            return cand.isoformat(), warnings
        if len(parts) == 3:
            day, month, year = map(int, parts)
            if year < 100:
                year += 2000
            cand = date(year, month, day)
            warnings.append("DATE_PARSED_GB_NUMERIC")
            return cand.isoformat(), warnings
    except Exception:
        pass

    # Month name: "5 March", "March 5", "February 2027" etc
    month_match = re.search(
        r"(\d{1,2})?\s*(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,4})?",
        text,
    )
    if month_match:
        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12,
        }
        month = months[month_match.group(2)]
        day_str = month_match.group(1) or month_match.group(3)
        year_str = month_match.group(3) if month_match.group(1) else None
        try:
            if day_str and int(day_str) > 31:
                # It's a year, e.g. "February 2027"
                return date(int(day_str), month, 1).isoformat(), warnings
            day = int(day_str) if day_str else 1
            year = today.year
            cand = date(year, month, day)
            if cand < today:
                cand = date(year + 1, month, day)
            return cand.isoformat(), warnings
        except Exception:
            pass

    warnings.append("EXPIRY_UNKNOWN")
    return None, warnings


def normalize_items(raw_items: List[RawItem], location: str) -> List[Dict]:
    out: List[Dict] = []
    for r in raw_items:
        name_raw = (r.get("name_raw") or "").strip()
        display_name = name_raw.lower()

        # Build a stable item_key: lowercase, spaces replaced with underscores
        item_key = re.sub(r"\s+", "_", display_name)

        qty, unit, w_units = _parse_quantity_unit(r.get("quantity_raw"), r.get("unit_raw"))
        expires_on, w_date = _parse_date_gb(r.get("expires_raw"))

        warnings = w_units + w_date
        if location == "pantry" and display_name in {"eggs"}:
            warnings.append("LOCATION_SUSPICIOUS")
        item = {
            "item": {
                "name_raw": name_raw,
                "display_name": display_name,
                "item_key": item_key,
                "location": location,
                "quantity": qty,
                "unit": unit,
                "expires_on": expires_on,
                "notes": r.get("notes_raw"),
            },
            "warnings": warnings,
            "normalization": {
                "quantity_raw": r.get("quantity_raw"),
                "unit_raw": r.get("unit_raw"),
                "expires_raw": r.get("expires_raw"),
                "locale": "en-GB",
            },
        }
        out.append(item)
    return out
