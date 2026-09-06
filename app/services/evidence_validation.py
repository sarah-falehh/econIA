from __future__ import annotations
from typing import Any

# v4.14: the score is an auditable triage index, not a probability.
# Decisions are made from validation dimensions + critical rules, not one threshold.
VALIDATION_WEIGHTS: dict[str, float] = {
    "base": 0.0, "conflict": -0.18,
}

EVIDENCE_LABELS = {
    "indicator_explicit":"indicateur explicite", "indicator_context":"indicateur résolu par contexte",
    "value_explicit":"valeur explicite", "period_explicit":"période explicite",
    "period_resolved":"période résolue par contexte", "unit_explicit":"unité/devise explicite",
    "unit_inferred":"unité sémantique propagée", "country_explicit":"pays explicite",
    "country_inherited":"pays hérité du document", "semantic_compatibility":"unité compatible avec l’indicateur",
    "comparison_resolved":"comparaison temporelle résolue", "linguistic_relation":"relation valeur-indicateur",
    "forecast_marker":"marqueur de prévision", "estimate_marker":"marqueur d’estimation",
    "deterministic_association":"association valeur-indicateur-période déterministe",
    "safe_context_inheritance":"contexte hérité avec antécédent local unique",
    "structured_table_evidence":"cellule issue d’un tableau macroéconomique structuré",
    "rounding_compatible":"écart compatible avec l’arrondi publié",
}
WARNING_LABELS = {
    "period_resolved":"période héritée/résolue", "unit_inferred":"unité propagée",
    "country_inherited":"pays hérité", "indicator_context":"indicateur hérité du contexte",
    "missing_period":"Période absente", "missing_unit":"Unité ou devise absente", "missing_country":"Pays absent",
    "ambiguous_context":"Contexte potentiellement ambigu", "suspicious_section":"Section documentaire potentiellement non économique",
    "conflict":"Valeurs contradictoires détectées pour le même pays, indicateur, période et unité",
    "critical_unit_mismatch":"Unité incompatible avec l’indicateur",
    "weak_association":"Association valeur-indicateur-période insuffisamment établie",
    "safe_context_inheritance":"Contexte hérité résolu de façon déterministe",
}
CRITICAL_WARNINGS={"critical_unit_mismatch","suspicious_section"}
REVIEW_WARNINGS={"conflict","ambiguous_context","weak_association","missing_country"}

PERCENTAGE_CODES={
    "public_debt_ratio","external_debt_ratio","internal_debt_ratio","budget_deficit","primary_balance",
    "gdp_growth","inflation_rate","inflation_annual_average","inflation_end_period","core_inflation","food_inflation",
    "unemployment_rate","activity_rate","public_spending_ratio","external_debt_share","internal_debt_share",
    "public_debt_state_share","trade_coverage_ratio","cpi_monthly_change","fdi_growth","exports_growth","imports_growth",
    "current_account_balance",
    "policy_rate","money_market_rate","real_money_market_rate","nominal_effective_exchange_rate",
    "real_effective_exchange_rate","relative_price_change","exchange_rate_change","unit_labor_cost",
    "nominal_wage_rate","labor_productivity","value_added_price","wage_cost_margin",
    "competitiveness_index","competitor_prices",
}
MONETARY_CODES={"public_debt_stock","internal_debt_stock","external_debt_stock","exports","imports","foreign_direct_investment","foreign_exchange_reserves","trade_balance"}

def _expected_unit_compatible(code, unit, currency, scale):
    if not code: return None
    if code in PERCENTAGE_CODES: return bool(unit and "%" in str(unit))
    if code in MONETARY_CODES: return bool(currency or scale)
    return None

def _relation_strength(sentence: str, cur: dict[str,Any]) -> float:
    low=(sentence or "").lower().replace("’","'")
    if cur.get("indicator_source") in {"structured_table_header", "explicit_table"}:
        return 1.0
    # Strong economic predicates and explicit comparison grammar.
    strong=("atteint","atteign", "ressort", "s'est établi","s'établissait","s'est élevée","s'est élevé","représent", "passé", "progress", "augment", "recul", "diminu", "élevées", "élevés", "estim", "serait", "seraient", "devrait", "devraient", "atteindrait", "atteindraient", "remonterait", "remonteraient", "ralentirait", "ralentiraient")
    if any(x in low for x in strong): return 1.0
    # A short nominal coreference such as "ce ratio était de ..." is still a
    # strong local value relation when the resolver has already supplied a
    # unique indicator. Ambiguity is handled separately by ambiguous_context.
    coref_value = bool(__import__("re").search(
        r"\b(?:ce\s+(?:ratio|taux|niveau)|il|elle|ils|elles)\b.{0,45}\b(?:était|etait|etaient|étaient|valait|représentait)\b",
        low, __import__("re").I
    ))
    if coref_value and cur.get("indicator_source") != "explicit": return 0.90
    if cur.get("indicator_source") != "explicit" and cur.get("code") in {"inflation_rate","inflation_annual_average","inflation_end_period"} and __import__("re").search(r"\bhausse\s+sur\s+(?:douze|12)\s+mois\b", low, __import__("re").I):
        return 0.90
    return 0.82 if cur.get("indicator_source")=="explicit" else 0.62

def score_event(cur: dict[str,Any], sentence: str, context: dict[str,Any], explicit_country: bool=False) -> dict[str,Any]:
    signals=["value_explicit"]; warnings=[]
    indicator_explicit=cur.get("code") not in {None,"other"} and cur.get("indicator_source") in {"explicit","explicit_table","structured_table_header"}
    indicator_ok=cur.get("code") not in {None,"other"}
    if indicator_ok:
        signals.append("indicator_explicit" if indicator_explicit else "indicator_context")
        if not indicator_explicit: warnings.append("indicator_context")

    has_period=any(cur.get(k) is not None for k in ("year","quarter","month")) or bool(cur.get("period_label"))
    period_explicit=has_period and cur.get("period_source") in {"explicit","explicit_table","table_header","explicit_range","explicit_open_range","explicit_average_unknown_range"}
    if has_period:
        signals.append("period_explicit" if period_explicit else "period_resolved")
        if not period_explicit: warnings.append("period_resolved")
    else: warnings.append("missing_period")

    has_unit=bool(cur.get("unit") or cur.get("currency") or cur.get("scale"))
    unit_explicit=has_unit and cur.get("unit_source") in {"explicit","explicit_table","table_header"}
    if has_unit:
        signals.append("unit_explicit" if unit_explicit else "unit_inferred")
        if not unit_explicit: warnings.append("unit_inferred")
    else: warnings.append("missing_unit")

    row_country_explicit=bool(cur.get("country")) and cur.get("country_source") in {"explicit_table_row","explicit_local","explicit_clause","respectively_geography_alignment","explicit_group_local"}
    has_country=explicit_country or row_country_explicit or bool(context.get("country"))
    if explicit_country or row_country_explicit: signals.append("country_explicit")
    elif has_country:
        signals.append("country_inherited"); warnings.append("country_inherited")
    else: warnings.append("missing_country")

    compat=_expected_unit_compatible(cur.get("code"),cur.get("unit"),cur.get("currency"),cur.get("scale"))
    if compat is True: signals.append("semantic_compatibility")
    elif compat is False: warnings.append("critical_unit_mismatch")

    low=(sentence or "").lower().replace("’","'")
    comparison=any(t in low for t in ("contre","après","l'année précédente","l'année suivante","trimestre précédent","trimestre suivant","un an auparavant","de "," à "))
    if comparison: signals.append("comparison_resolved")
    relation=_relation_strength(sentence,cur)
    if relation >= .8: signals.append("linguistic_relation")
    if cur.get("status")=="forecast": signals.append("forecast_marker")
    elif cur.get("status")=="estimate": signals.append("estimate_marker")

    # Independent dimensions: explicitness and safe deterministic inheritance are not the same thing.
    dims={
        "indicator": 1.0 if indicator_explicit else (0.78 if indicator_ok else 0.0),
        "value": 1.0,
        "unit": 1.0 if unit_explicit else (0.84 if has_unit else 0.0),
        "period": 1.0 if period_explicit else (0.84 if has_period else 0.0),
        "country": 1.0 if (explicit_country or row_country_explicit) else (0.92 if has_country else 0.0),
        "association": relation,
        "semantic": 1.0 if compat is True else (0.72 if compat is None else 0.0),
        "context": 1.0 if indicator_explicit and period_explicit else (0.82 if indicator_ok and has_period else 0.55),
    }
    if cur.get("indicator_source") in {"explicit_table","structured_table_header"} and cur.get("period_source") in {"explicit_table","table_header"}:
        signals.append("structured_table_evidence")
        dims["context"] = max(dims["context"], .95)
        dims["association"] = max(dims["association"], .95)

    # Safe contextual inheritance: an inherited indicator/pronoun is acceptable when
    # the local sentence provides a unique economic relation and the remaining fields
    # are resolved without competing candidates. This is deliberately narrower than
    # simply removing the context penalty.
    pronoun_or_relative = any(t in low for t in (
        "il ", "elle ", "elles ", "ils ", "ce ratio", "ce taux", "ce niveau",
        "un an auparavant", "un an plus tot", "un mois plus tot", "l'année précédente", "l’année précédente", "l'annee precedente",
        "trimestre précédent", "trimestre precedent", "trimestre qui precedait", "trimestre suivant", "trois mois plus tard",
        "année suivante", "annee suivante", "l'annee d'avant", "deux ans plus tot", "hausse sur douze mois", "serait", "devrait", "remonterait"
    ))
    safe_context = (
        not indicator_explicit and indicator_ok and has_period and has_unit and has_country
        and relation >= .82 and compat is not False and pronoun_or_relative
        and not bool(cur.get("ambiguous_context"))
    )
    if bool(cur.get("ambiguous_context")):
        warnings.append("ambiguous_context")
    if safe_context:
        dims["indicator"] = max(dims["indicator"], .86)
        dims["context"] = max(dims["context"], .90)
        dims["association"] = max(dims["association"], .90)
        signals.append("safe_context_inheritance")

    deterministic=(min(dims[k] for k in ("indicator","value","unit","period","country","association")) >= .82 and dims["semantic"] >= .72)
    if deterministic: signals.append("deterministic_association")
    elif dims["association"] < .75 or dims["indicator"] < .7 or dims["period"] < .7: warnings.append("weak_association")

    # Weighted diagnostic score. No single cutoff decides the business status.
    weights={"indicator":.17,"value":.16,"unit":.12,"period":.17,"country":.10,"association":.16,"semantic":.08,"context":.04}
    score=sum(dims[k]*w for k,w in weights.items())
    if "critical_unit_mismatch" in warnings: score-=.30
    if "missing_period" in warnings: score-=.15
    if "missing_country" in warnings: score-=.10
    score=round(max(.05,min(score,.98)),2)
    return {"confidence":score,"validation_dimensions":dims,"validation_evidence":signals,"validation_warnings":warnings,
            "confidence_evidence":[EVIDENCE_LABELS.get(x,x) for x in signals],"confidence_warnings":[WARNING_LABELS.get(x,x) for x in warnings]}

def finalize_status(row: dict[str,Any]) -> dict[str,Any]:
    warnings=set(row.get("validation_warnings") or [])
    conflict=bool(row.get("conflict_status")); score=float(row.get("confidence") or 0)
    dims=row.get("validation_dimensions") or {}
    if conflict:
        warnings.add("conflict"); score=min(score,.80)
    deterministic="deterministic_association" in set(row.get("validation_evidence") or [])
    if warnings & CRITICAL_WARNINGS:
        status="Rejeté"
    elif conflict or warnings & REVIEW_WARNINGS:
        status="À vérifier"
    elif deterministic:
        status="Validé"
    elif dims and min(dims.get("indicator",0),dims.get("value",0),dims.get("period",0),dims.get("association",0)) >= .78 and dims.get("semantic",0)>=.72:
        status="Validé"
    else:
        status="À vérifier"
    row["confidence"]=round(max(.05,min(score,.98)),2); row["validation_status"]=status; row["needs_review"]=status!="Validé"
    row["validation_warnings"]=sorted(warnings); row["confidence_warnings"]=[WARNING_LABELS.get(x,x) for x in sorted(warnings)]
    row["review_reason"]="; ".join(row["confidence_warnings"]) if status!="Validé" else None
    row["observation_type"]=row.get("fact_type") or "observed"
    return row
