from __future__ import annotations

from dataclasses import dataclass
import math
import re
import unicodedata
from typing import Any


def norm_text(value: Any) -> str:
    if value is None: return ""
    s = unicodedata.normalize("NFKC", str(value)).strip().lower()
    s = s.replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", s)


def norm_number(value: Any) -> float | None:
    if value is None or value == "": return None
    try: return round(float(str(value).replace(" ", "").replace(",", ".")), 8)
    except (TypeError, ValueError): return None


def canonical_unit(unit: Any, indicator: Any = None, scale: Any = None, currency: Any = None) -> str:
    pieces=[]
    if scale: pieces.append(norm_text(scale))
    if currency: pieces.append(norm_text(currency).upper())
    if unit: pieces.append(norm_text(unit))
    u=" ".join(pieces).strip().lower()
    u=u.replace("millions", "million").replace("milliards", "milliard")
    if norm_text(indicator) == norm_text("Dette publique (% du PIB)") and "%" in u:
        return "% du pib"
    if u in {"million tnd", "million TND".lower()}: return "million tnd"
    if u in {"milliard tnd", "milliard TND".lower()}: return "milliard tnd"
    return u


def normalize_gold(row: dict) -> dict:
    return {
        "country": norm_text(row.get("country")), "indicator": norm_text(row.get("indicator")),
        "value": norm_number(row.get("value")), "unit": canonical_unit(row.get("unit"), row.get("indicator")),
        "year": int(float(row["year"])) if row.get("year") not in (None,"") else None,
        "quarter": int(float(row["quarter"])) if row.get("quarter") not in (None,"") else None,
        "month": int(float(row["month"])) if row.get("month") not in (None,"") else None,
        "observation_type": norm_text(row.get("observation_type")),
    }


def normalize_prediction(row: dict) -> dict:
    return {
        "country": norm_text(row.get("country")), "indicator": norm_text(row.get("indicator")),
        "value": norm_number(row.get("current_value")),
        "unit": canonical_unit(row.get("current_unit"), row.get("indicator"), row.get("current_scale"), row.get("current_currency")),
        "year": int(row["current_year"]) if row.get("current_year") is not None else None,
        "quarter": int(row["current_quarter"]) if row.get("current_quarter") is not None else None,
        "month": int(row["current_month"]) if row.get("current_month") is not None else None,
        "observation_type": norm_text(row.get("fact_type")),
        "needs_review": bool(row.get("needs_review")),
    }


def exact_equal(a: dict, b: dict, include_type: bool = False) -> bool:
    fields=["country","indicator","value","unit","year","quarter","month"]
    if include_type: fields.append("observation_type")
    return all(a.get(k)==b.get(k) for k in fields)


def identity_distance(g: dict, p: dict) -> tuple:
    # Used only for component diagnostics; exact matching remains strict.
    return (
        g["indicator"] != p["indicator"],
        g["value"] != p["value"],
        g["year"] != p["year"],
        g["quarter"] != p["quarter"],
        g["month"] != p["month"],
        g["country"] != p["country"],
        g["unit"] != p["unit"],
    )


def evaluate(gold_rows: list[dict], predicted_rows: list[dict]) -> dict:
    gold=[normalize_gold(r) for r in gold_rows]
    pred=[normalize_prediction(r) for r in predicted_rows]
    unmatched_pred=set(range(len(pred))); matches=[]
    for gi,g in enumerate(gold):
        hit=next((pi for pi in unmatched_pred if exact_equal(g,pred[pi],include_type=False)),None)
        if hit is not None:
            unmatched_pred.remove(hit); matches.append((gi,hit))
    tp=len(matches); fp=len(pred)-tp; fn=len(gold)-tp
    precision=tp/(tp+fp) if tp+fp else 0.0; recall=tp/(tp+fn) if tp+fn else 0.0
    f1=2*precision*recall/(precision+recall) if precision+recall else 0.0

    # Pair each gold item with the closest remaining prediction sharing indicator/value when possible.
    paired=[]; available=set(range(len(pred)))
    for gi,g in enumerate(gold):
        if not available: break
        candidates=sorted(available,key=lambda pi: identity_distance(g,pred[pi]))
        pi=candidates[0]; available.remove(pi); paired.append((gi,pi))
    def acc(field):
        return sum(gold[gi].get(field)==pred[pi].get(field) for gi,pi in paired)/len(gold) if gold else 0.0
    exact_with_type=sum(exact_equal(gold[gi],pred[pi],include_type=True) for gi,pi in matches)
    review=sum(p.get("needs_review",False) for p in pred)
    return {
        "gold_events":len(gold), "predicted_events":len(pred), "tp":tp, "fp":fp, "fn":fn,
        "precision":precision, "recall":recall, "f1":f1, "event_exact_match":tp/len(gold) if gold else 0.0,
        "event_exact_match_with_type":exact_with_type/len(gold) if gold else 0.0,
        "country_accuracy":acc("country"), "indicator_accuracy":acc("indicator"), "value_accuracy":acc("value"),
        "unit_accuracy":acc("unit"), "period_accuracy":sum((gold[gi]["year"],gold[gi]["quarter"],gold[gi]["month"])==(pred[pi]["year"],pred[pi]["quarter"],pred[pi]["month"]) for gi,pi in paired)/len(gold) if gold else 0.0,
        "observation_type_accuracy":acc("observation_type"), "review_rate":review/len(pred) if pred else 0.0,
    }
