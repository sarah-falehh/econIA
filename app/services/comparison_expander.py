from __future__ import annotations

import copy
import re
from typing import Iterable

from app.services.economic_extractor import compute_changes, numeric_mentions

PERIOD_PATTERNS = {
    "quarter": re.compile(r"(?:Q|T)\s*([1-4])", re.I),
    "year": re.compile(r"\b(19\d{2}|20\d{2})\b"),
}

COMPARISON_CUES = re.compile(
    r"\b(?:from|to|compared\s+(?:with|to)|versus|vs\.?|against|down\s+from|up\s+from|"
    r"de|à|contre|par\s+rapport\s+à|comparé(?:e)?\s+à|contre|passant\s+de|"
    r"من|إلى|مقارنة\s+ب|مقابل)\b",
    re.I,
)


def _period_near(text: str, start: int, end: int) -> tuple[int | None, int | None, int | None]:
    window = text[max(0, start - 35): min(len(text), end + 55)]
    quarter_match = PERIOD_PATTERNS["quarter"].search(window)
    years = PERIOD_PATTERNS["year"].findall(window)
    quarter = int(quarter_match.group(1)) if quarter_match else None
    year = int(years[-1]) if years else None
    return None, quarter, year


def _inside_parentheses(text: str, position: int) -> bool:
    left = text.rfind("(", 0, position)
    right = text.rfind(")", 0, position)
    return left > right


def _compatible_unit(current: dict, candidate: dict) -> bool:
    cu = (current.get("unit") or "").lower()
    ru = (candidate.get("unit") or "").lower()
    cc = (current.get("currency") or "").lower()
    rc = (candidate.get("currency") or "").lower()
    # Percentages must only be compared with percentages. Currencies must match.
    if bool(cu) != bool(ru):
        return False
    if cu and ru and cu != ru:
        return False
    if cc and rc and cc != rc:
        return False
    return True


def expand_comparisons(facts: Iterable[dict]) -> list[dict]:
    """Create one row per *explicit* comparison while avoiding numeric lists.

    Previous versions treated every number after the first one as a reference.
    This produced false comparisons for ages, dates, category shares and monetary
    amounts. V17 expands only sentences containing comparison cues and keeps
    values with compatible units. The reference already selected by the main
    extractor is always preserved.
    """
    expanded: list[dict] = []
    for fact in facts:
        item = dict(fact)
        sentence = item.get("sentence") or ""
        current_value = item.get("current_value")
        original_reference = item.get("reference_value")

        if item.get("value_type") != "level" or current_value is None:
            item["comparison_index"] = 1 if original_reference is not None else 0
            item["comparison_count"] = 1 if original_reference is not None else 0
            expanded.append(item)
            continue

        # No explicit comparison: never manufacture references from a list.
        if not COMPARISON_CUES.search(sentence):
            item["comparison_index"] = 1 if original_reference is not None else 0
            item["comparison_count"] = 1 if original_reference is not None else 0
            expanded.append(item)
            continue

        mentions = [m for m in numeric_mentions(sentence) if not m.get("is_year")]
        if not mentions:
            expanded.append(item)
            continue

        current = min(
            mentions,
            key=lambda m: abs(float(m.get("value", 0)) - float(current_value)),
        )
        refs = []
        seen = set()

        # Keep the extractor's original reference first.
        if original_reference is not None:
            for m in mentions:
                if abs(float(m.get("value", 0)) - float(original_reference)) < 1e-9:
                    if _compatible_unit(current, m):
                        refs.append(m)
                        seen.add((float(m["value"]), m.get("raw")))
                    break

        for m in mentions:
            key = (float(m.get("value", 0)), m.get("raw"))
            if key in seen or m is current:
                continue
            if _inside_parentheses(sentence, int(m.get("start", 0))):
                continue
            # Ignore day/month numbers and bare list items.
            if not _compatible_unit(current, m):
                continue
            local = sentence[max(0, int(m.get("start", 0)) - 32): int(m.get("end", 0)) + 8]
            if not COMPARISON_CUES.search(local):
                continue
            refs.append(m)
            seen.add(key)

        if not refs:
            item["comparison_index"] = 0
            item["comparison_count"] = 0
            expanded.append(item)
            continue

        for pos, ref in enumerate(refs, start=1):
            row = copy.deepcopy(item)
            ref_value = float(ref["value"])
            row["reference_value"] = ref_value
            row["reference_value_raw"] = ref.get("raw")
            row["reference_unit"] = ref.get("unit") or item.get("current_unit")
            row["reference_scale"] = ref.get("scale")
            row["reference_currency"] = ref.get("currency")
            month, quarter, year = _period_near(sentence, int(ref.get("start", 0)), int(ref.get("end", 0)))
            row["reference_month"] = month
            row["reference_quarter"] = quarter
            row["reference_year"] = year
            absolute, relative, direction = compute_changes(float(current_value), ref_value)
            row["absolute_change"] = absolute
            row["relative_change"] = relative
            row["direction"] = direction
            row["comparison_index"] = pos
            row["comparison_count"] = len(refs)
            expanded.append(row)
    return expanded
