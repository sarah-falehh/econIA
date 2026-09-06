from __future__ import annotations

"""Generic semantic decoding of geometry-backed economic tables.

The module deliberately knows table *shapes* and economic header concepts, not
documents, page numbers, countries or observed values.  It emits an
intermediate event representation consumed by the canonical validation layer.
"""

import re
from typing import Any

from app.services.country_registry import detect_country


_NUM = re.compile(r"^\s*([-+]?\d+(?:[.,]\d+)?)\s*(%)?\s*$")
_PERIOD = re.compile(r"^\s*((?:19|20)\d{2})(?:\s*[-–]\s*((?:19|20)\d{2}))?\s*$")

HEADER_CONCEPTS = {
    "nominal": ("nominal_effective_exchange_rate", "Variation du taux de change effectif nominal (TCEN)"),
    "réel": ("real_effective_exchange_rate", "Variation du taux de change effectif réel (TCER)"),
    "reel": ("real_effective_exchange_rate", "Variation du taux de change effectif réel (TCER)"),
    "prix relatif": ("relative_price_change", "Variation des prix relatifs"),
    "csu nominal": ("unit_labor_cost", "Variation du coût salarial unitaire nominal (CSU)"),
    "csu": ("unit_labor_cost", "Variation du coût salarial unitaire nominal (CSU)"),
    "taux de salaire": ("nominal_wage_rate", "Variation du taux de salaire nominal"),
    "productivité du travail": ("labor_productivity", "Variation de la productivité du travail"),
    "productivite du travail": ("labor_productivity", "Variation de la productivité du travail"),
    "prix de la valeur ajoutée": ("value_added_price", "Variation du prix de la valeur ajoutée"),
    "prix de la valeur ajoutee": ("value_added_price", "Variation du prix de la valeur ajoutée"),
    "marge sur coût salarial": ("wage_cost_margin", "Variation de la marge sur coût salarial"),
    "marge sur cout salarial": ("wage_cost_margin", "Variation de la marge sur coût salarial"),
    "isc": ("competitiveness_index", "Variation de l’indicateur synthétique de compétitivité"),
    "prix des concurrents": ("competitor_prices", "Variation des prix des concurrents"),
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\n", " ")).strip()


def _parse_number(value: Any) -> tuple[float, bool] | None:
    m = _NUM.match(_clean(value))
    if not m:
        return None
    return float(m.group(1).replace(",", ".")), bool(m.group(2))


def _parse_period(value: Any) -> tuple[int, int, str] | None:
    text = _clean(value)
    text = re.sub(r"^(?:moyenne\s*)?[()]", "", text, flags=re.I)
    text = text.rstrip(")")
    m = _PERIOD.match(text)
    if not m:
        return None
    start, end = int(m.group(1)), int(m.group(2) or m.group(1))
    return start, end, "year" if start == end else "average_range"


def _compress(rows: list[list[Any]]) -> list[list[str]]:
    width = max((len(r) for r in rows), default=0)
    keep = [i for i in range(width) if any(i < len(r) and _clean(r[i]) for r in rows)]
    return [[_clean(r[i]) if i < len(r) else "" for i in keep] for r in rows]


def _concept(text: str) -> tuple[str, str] | None:
    low = _clean(text).lower()
    if re.search(r"\bPIB\s+r[ée]el\b|croissance\s+(?:du\s+)?PIB", low, re.I):
        return "gdp_growth", "Taux de croissance du PIB réel (variation annuelle)"
    if re.search(r"inflation\s+moyenne", low, re.I):
        return "inflation_annual_average", "Taux d’inflation des prix à la consommation (moyenne annuelle)"
    if re.search(r"dette\s+publique", low, re.I):
        return "public_debt_ratio", "Dette publique (% du PIB)"
    # Prefer the longest phrase so "CSU nominal" wins over "nominal".
    for key in sorted(HEADER_CONCEPTS, key=len, reverse=True):
        if key in low:
            return HEADER_CONCEPTS[key]
    if re.search(r"ch[oô]mage", low, re.I):
        return "unemployment_rate", "Taux de chômage"
    if re.search(r"taux\s+directeur", low, re.I):
        return "policy_rate", "Taux directeur de la banque centrale"
    if re.search(r"inflation", low, re.I):
        return "inflation_rate", "Taux d’inflation des prix à la consommation"
    return None


def _fact_type(text: str) -> str:
    low=_clean(text).lower()
    if "prévision" in low or "prevision" in low or "forecast" in low: return "forecast"
    if "estim" in low: return "estimate"
    return "observed"


def _point_period(text: str) -> tuple[int, int | None, int | None, str] | None:
    value=_clean(text)
    m=re.fullmatch(r"((?:19|20)\d{2})(?:-Q([1-4])|-M(0?[1-9]|1[0-2]))?",value,re.I)
    if not m: return None
    return int(m.group(1)), int(m.group(3)) if m.group(3) else None, int(m.group(2)) if m.group(2) else None, value.upper()


def _country(text: str) -> tuple[str | None,str | None]:
    return detect_country(_clean(text), None)


def _parse_long_table(grid: list[list[str]], meta: dict[str,Any]) -> list[dict[str,Any]]:
    if not grid: return []
    header=[_clean(c).lower() for c in grid[0]]
    required={"pays","période","indicateur","valeur"}
    if not required.issubset(set(header)): return []
    idx={name:header.index(name) for name in required}
    unit_idx=header.index("unité") if "unité" in header else None
    nature_idx=header.index("nature") if "nature" in header else None
    out=[]
    for row in grid[1:]:
        if max(idx.values())>=len(row): continue
        concept=_concept(row[idx["indicateur"]]); parsed=_parse_number(row[idx["valeur"]]); point=_point_period(row[idx["période"]])
        if concept is None or parsed is None or point is None: continue
        year,month,quarter,label=point; country,iso3=_country(row[idx["pays"]])
        unit=_clean(row[unit_idx]) if unit_idx is not None and unit_idx<len(row) else ("%" if parsed[1] else None)
        event=_event(code=concept[0],label=concept[1],value=parsed[0],period=(year,year,"year"),page=meta["page"],table_index=meta["table_index"],row_label=" | ".join(row),column_label=row[idx["indicateur"]],unit=unit or "%",geometry=meta.get("bbox"))
        event.update({"year":year,"month":month,"quarter":quarter,"period_label":label,"period_start":label,"period_end":label,"period_type":"month" if month else "quarter" if quarter else "year","country":country or row[idx["pays"]],"country_iso3":iso3,"country_source":"explicit_table_row","geography_type":"country","status":_fact_type(row[nature_idx]) if nature_idx is not None and nature_idx<len(row) else "observed"})
        out.append(event)
    return out


def _parse_wide_country_year(grid:list[list[str]],meta:dict[str,Any])->list[dict[str,Any]]:
    if not grid:return []
    header=[_clean(c) for c in grid[0]]; low=[c.lower() for c in header]
    if "pays" not in low or not any(x in low for x in ("année","annee","year")): return []
    country_i=low.index("pays"); year_i=next(low.index(x) for x in ("année","annee","year") if x in low)
    type_i=next((i for i,x in enumerate(low) if x in {"type","nature"}),None)
    concepts=[_concept(c) for c in header]
    if sum(c is not None for c in concepts)<2:return []
    out=[]
    for row in grid[1:]:
        if max(country_i,year_i)>=len(row):continue
        point=_point_period(row[year_i]); country,iso3=_country(row[country_i])
        if point is None:continue
        year=point[0]
        for col,concept in enumerate(concepts):
            if concept is None or col>=len(row):continue
            parsed=_parse_number(row[col])
            if parsed is None:continue
            event=_event(code=concept[0],label=concept[1],value=parsed[0],period=(year,year,"year"),page=meta["page"],table_index=meta["table_index"],row_label=" | ".join(row),column_label=header[col],unit="%",geometry=meta.get("bbox"))
            event.update({"country":country or row[country_i],"country_iso3":iso3,"country_source":"explicit_table_row","geography_type":"country","status":_fact_type(row[type_i]) if type_i is not None and type_i<len(row) else "observed"})
            out.append(event)
    return out


def _event(*, code: str, label: str, value: float, period: tuple[int, int, str],
           page: int, table_index: int, row_label: str, column_label: str,
           sector: str | None = None, unit: str = "%", geometry: Any = None) -> dict[str, Any]:
    start, end, kind = period
    period_label = str(start) if start == end else f"{start}-{end}"
    return {
        "code": code, "label": label, "value": value, "raw": str(value),
        "unit": unit, "scale": None, "currency": None,
        "year": start if start == end else None, "month": None, "quarter": None,
        "period_label": period_label, "period_type": kind,
        "period_start": str(start), "period_end": str(end), "frequency": "annual",
        "status": "observed", "indicator_source": "structured_table_header",
        "unit_source": "table_header", "period_source": "table_header",
        "position": 0, "end_position": 0, "sector": sector,
        "table_page": page, "table_index": table_index,
        "table_row_label": row_label, "table_column_label": column_label,
        "table_bbox": geometry,
    }


def _parse_column_matrix(grid: list[list[str]], meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse period rows crossed with explicit indicator column headers."""
    out: list[dict[str, Any]] = []
    header_row = next((r for r in grid[:6] if sum(_concept(c) is not None for c in r) >= 2), None)
    if header_row is None:
        return out
    concepts = [_concept(c) for c in header_row]
    for row_index, row in enumerate(grid):
        if not row:
            continue
        period = _parse_period(row[0])
        if period is None:
            continue
        for col, concept in enumerate(concepts):
            if col == 0 or concept is None or col >= len(row):
                continue
            parsed = _parse_number(row[col])
            if parsed is None:
                continue
            value, printed_percent = parsed
            out.append(_event(code=concept[0], label=concept[1], value=value, period=period,
                              page=meta["page"], table_index=meta["table_index"],
                              row_label=row[0], column_label=header_row[col],
                              unit="%", geometry=meta.get("bbox")))
    return out


def _repair_wrapped_rows(grid: list[list[str]]) -> list[list[str]]:
    """Merge rows whose label and numeric cells were split by PDF wrapping."""
    repaired: list[list[str]] = []
    pending_label = ""
    for row_index, row in enumerate(grid):
        numeric_count = sum(_parse_number(c) is not None for c in row[1:])
        label = row[0] if row else ""
        if label and numeric_count == 0 and not _concept(" ".join(row)) and not any(_parse_period(c) for c in row):
            next_row = grid[row_index + 1] if row_index + 1 < len(grid) else []
            next_has_numbers = sum(_parse_number(c) is not None for c in next_row[1:]) > 0
            next_has_label = bool(next_row and next_row[0])
            if next_has_numbers and not next_has_label:
                pending_label = f"{pending_label} {label}".strip()
                continue
            if repaired and sum(_parse_number(c) is not None for c in repaired[-1][1:]) > 0 and not pending_label:
                repaired[-1][0] = f"{repaired[-1][0]} {label}".strip()
                continue
            pending_label = f"{pending_label} {label}".strip()
            continue
        if numeric_count and pending_label:
            row = list(row)
            row[0] = f"{pending_label} {row[0]}".strip()
            pending_label = ""
        repaired.append(row)
    return repaired


def _parse_grouped_columns(grid: list[list[str]], meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse sector rows under multi-level indicator × period headers."""
    out: list[dict[str, Any]] = []
    concept_row_idx = next((i for i, r in enumerate(grid[:6]) if sum(_concept(c) is not None for c in r) >= 2), None)
    if concept_row_idx is None or concept_row_idx + 1 >= len(grid):
        return out
    concept_row = grid[concept_row_idx]
    period_row = list(grid[concept_row_idx + 1])
    # A wrapped terminal period fragment may occupy the next row.
    if concept_row_idx + 2 < len(grid):
        extra = grid[concept_row_idx + 2]
        for i, cell in enumerate(extra):
            if cell and i < len(period_row) and period_row[i] and not _parse_period(period_row[i]):
                period_row[i] = f"{period_row[i]}{cell}"
        # Some PDFs place a wrapped last header in an extra geometry column,
        # while the values remain in the preceding column.
        for i in range(1, len(period_row) - 1):
            if not period_row[i] and _parse_period(period_row[i + 1]):
                period_row[i] = period_row[i + 1]
    current_concept = None
    columns: list[tuple[tuple[str, str] | None, tuple[int, int, str] | None, str]] = []
    for i in range(len(concept_row)):
        explicit = _concept(concept_row[i])
        if explicit:
            current_concept = explicit
        period = _parse_period(period_row[i]) if i < len(period_row) else None
        columns.append((current_concept, period, f"{concept_row[i]} {period_row[i] if i < len(period_row) else ''}".strip()))
    for row in _repair_wrapped_rows(grid[concept_row_idx + 2:]):
        if not row or not row[0] or sum(_parse_number(c) is not None for c in row[1:]) < 2:
            continue
        sector = row[0]
        for col in range(1, min(len(row), len(columns))):
            concept, period, col_label = columns[col]
            parsed = _parse_number(row[col])
            if concept is None or period is None or parsed is None:
                continue
            out.append(_event(code=concept[0], label=concept[1], value=parsed[0], period=period,
                              page=meta["page"], table_index=meta["table_index"], sector=sector,
                              row_label=sector, column_label=col_label, geometry=meta.get("bbox")))
    return out


def _parse_sector_blocks(grid: list[list[str]], meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse sector heading rows followed by indicator rows and period columns."""
    if not grid:
        return []
    periods = [_parse_period(c) for c in grid[0]]
    if sum(p is not None for p in periods) < 2:
        return []
    out: list[dict[str, Any]] = []
    sector: str | None = None
    pending_sector = ""
    for row in grid[1:]:
        row_text = " ".join(row[:2])
        concept = _concept(row_text)
        numeric = sum(_parse_number(c) is not None for c in row)
        if concept is None and numeric == 0:
            label = " ".join(c for c in row[:2] if c)
            pending_sector = f"{pending_sector} {label}".strip()
            if label:
                sector = pending_sector
            continue
        if concept is None:
            continue
        if pending_sector:
            sector = pending_sector
            pending_sector = ""
        for col, period in enumerate(periods):
            if period is None or col >= len(row):
                continue
            parsed = _parse_number(row[col])
            if parsed is None:
                continue
            out.append(_event(code=concept[0], label=concept[1], value=parsed[0], period=period,
                              page=meta["page"], table_index=meta["table_index"], sector=sector,
                              row_label=row_text, column_label=grid[0][col], geometry=meta.get("bbox")))
    return out


def _parse_simple_sector_average(grid: list[list[str]], meta: dict[str, Any], page_text: str) -> list[dict[str, Any]]:
    header = " ".join(" ".join(r) for r in grid[:3])
    period_match = re.search(r"moyenne\s*\(((?:19|20)\d{2})\s*[-–]\s*((?:19|20)\d{2})\)", header, re.I)
    if not period_match or not re.search(r"co[uû]ts?\s+salariaux?\s+unitaires?", page_text, re.I):
        return []
    period = (int(period_match.group(1)), int(period_match.group(2)), "average_range")
    out = []
    for row in grid[2:]:
        parsed_cells = [(i, _parse_number(c)) for i, c in enumerate(row)]
        parsed_cells = [(i, p) for i, p in parsed_cells if p is not None]
        label = " ".join(c for c in row[:-1] if c)
        if not label or len(parsed_cells) != 1:
            continue
        value = parsed_cells[0][1][0]
        out.append(_event(code="unit_labor_cost_level", label="Coût salarial unitaire",
                          value=value, period=period, page=meta["page"],
                          table_index=meta["table_index"], sector=label,
                          row_label=label, column_label=f"Moyenne ({period[0]}-{period[1]})",
                          unit="ratio", geometry=meta.get("bbox")))
    return out


def extract_structured_table_events(document: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return semantic table events and an audit entry for every table."""
    events: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    pages = {int(m.group(1)): body for m, body in []}
    text = document.get("text") or ""
    page_texts: dict[int, str] = {}
    chunks = re.split(r"\[\[PAGE\s+(\d+)\]\]", text)
    for i in range(1, len(chunks), 2):
        page_texts[int(chunks[i])] = chunks[i + 1]
    for table in document.get("structured_tables") or []:
        grid = _compress(table.get("rows") or [])
        if not grid:
            continue
        parsers = (_parse_long_table, _parse_wide_country_year, _parse_grouped_columns, _parse_sector_blocks, _parse_column_matrix)
        parsed: list[dict[str, Any]] = []
        for parser in parsers:
            parsed = parser(grid, table)
            if parsed:
                break
        if not parsed:
            parsed = _parse_simple_sector_average(grid, table, page_texts.get(int(table["page"]), ""))
        events.extend(parsed)
        audit.append({
            "page": table.get("page"), "table_index": table.get("table_index"),
            "rows": len(grid), "columns": max((len(r) for r in grid), default=0),
            "events": len(parsed), "status": "extracted" if parsed else "unresolved_table",
            "bbox": table.get("bbox"),
        })
    return events, audit
