from datetime import date
from typing import Dict, List, Optional, Tuple

RawItem = Dict[str, Optional[str]]


def _parse_quantity_unit(raw_qty: Optional[str], raw_unit: Optional[str]) -> Tuple[Optional[float], Optional[str], List[str]]:
    warnings: List[str] = []
    if raw_qty is None or raw_qty == "":
        return None, None, warnings
    try:
        qty = float(str(raw_qty).replace(",", "."))
    except ValueError:
        return None, None, warnings
    unit = (raw_unit or "").lower()
    if unit in {"kg"}:
        qty *= 1000
        unit = "g"
    elif unit in {"l", "lt"}:
        qty *= 1000
        unit = "ml"
    elif unit in {"g", "ml", "count"}:
        pass
    elif unit == "":
        unit = "g"
        warnings.append("UNIT_ASSUMED_G")
    else:
        unit = "g"
        warnings.append("UNIT_ASSUMED_G")
    return qty, unit, warnings


def _parse_date_gb(raw: Optional[str]) -> Tuple[Optional[str], List[str]]:
    warnings: List[str] = []
    if not raw:
        warnings.append("EXPIRY_UNKNOWN")
        return None, warnings
    parts = raw.replace("-", "/").split("/")
    try:
        if len(parts) == 2:
            day, month = map(int, parts)
            year = date.today().year
            cand = date(year, month, day)
            if cand < date.today():
                cand = date(year + 1, month, day)
            warnings.append("DATE_PARSED_GB_NUMERIC")
            return cand.isoformat(), warnings
        if len(parts) == 3:
            day, month, year = map(int, parts)
            cand = date(year, month, day)
            warnings.append("DATE_PARSED_GB_NUMERIC")
            return cand.isoformat(), warnings
    except Exception:
        warnings.append("EXPIRY_UNKNOWN")
        return None, warnings
    warnings.append("EXPIRY_UNKNOWN")
    return None, warnings


def normalize_items(raw_items: List[RawItem], location: str) -> List[Dict]:
    out: List[Dict] = []
    for r in raw_items:
        name_raw = (r.get("name_raw") or "").strip()
        base = name_raw.lower()
        variant = None
        if " " in base:
            parts = base.split(" ", 1)
            base = parts[0]
            variant = parts[1].strip() or None
        item_key = base if not variant else f"{base}|{variant}"

        qty, unit, w_units = _parse_quantity_unit(r.get("quantity_raw"), r.get("unit_raw"))
        expires_on, w_date = _parse_date_gb(r.get("expires_raw"))

        warnings = w_units + w_date
        if location == "pantry" and base in {"eggs"}:
            warnings.append("LOCATION_SUSPICIOUS")
        item = {
            "item": {
                "name_raw": name_raw,
                "base_name": base,
                "variant": variant,
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
