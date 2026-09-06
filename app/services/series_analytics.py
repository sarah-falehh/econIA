from __future__ import annotations

from io import BytesIO
import math
import pandas as pd

TYPE_LABELS = {"observed": "Observé", "estimate": "Estimé", "forecast": "Prévision"}


SERIES_DERIVED_COLUMNS = [
    "Année", "Valeur numérique", "Évolution absolue",
    "Évolution %", "Sens", "Valeur affichée",
]


def _ensure_series_schema(data: pd.DataFrame) -> pd.DataFrame:
    """Guarantee a stable dataframe contract, including for empty series."""
    out = data.copy()
    defaults = {
        "Année": pd.Series(dtype="Int64"),
        "Valeur numérique": pd.Series(dtype="float64"),
        "Évolution absolue": pd.Series(dtype="float64"),
        "Évolution %": pd.Series(dtype="float64"),
        "Sens": pd.Series(dtype="object"),
        "Valeur affichée": pd.Series(dtype="object"),
    }
    for column, empty_series in defaults.items():
        if column not in out.columns:
            out[column] = empty_series
    return out


def _clean_optional(value):
    """Return None for pandas/NumPy missing values and textual null sentinels."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if text.lower() in {"", "nan", "none", "null", "<na>"}:
        return None
    return text


def _measurement_label(row: pd.Series) -> str:
    """Build a clean business-facing unit label without leaking NaN sentinels."""
    unit = _clean_optional(row.get("current_unit"))
    currency = _clean_optional(row.get("current_currency"))
    scale = _clean_optional(row.get("current_scale"))
    measurement = unit or currency or ""
    if scale and measurement:
        return f"{scale} {measurement}"
    if scale:
        return scale
    return measurement

def _business_status(data: pd.DataFrame) -> pd.Series:
    if "validation_status" in data.columns:
        raw = data["validation_status"].fillna("")
        mapped = raw.replace({"pending": "À vérifier", "validated": "Validé", "rejected": "Rejeté", "Validable": "Validé"})
        fallback = data.get("needs_review", pd.Series(True, index=data.index)).fillna(True).astype(bool).map({False: "Validé", True: "À vérifier"})
        return mapped.where(mapped.isin(["Validé", "À vérifier", "Rejeté"]), fallback)
    return data.get("needs_review", pd.Series(True, index=data.index)).fillna(True).astype(bool).map({False: "Validé", True: "À vérifier"})

def _business_type(data: pd.DataFrame) -> pd.Series:
    raw = data.get("observation_type", data.get("fact_type", pd.Series("observed", index=data.index))).fillna("observed")
    return raw.map(TYPE_LABELS).fillna(raw)

def _historical_eligible(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return data
    status = _business_status(data)
    raw_type = data.get("observation_type", data.get("fact_type", pd.Series("observed", index=data.index))).fillna("observed")
    # Historical descriptive statistics must not silently mix forecasts with realized observations.
    mask = (status != "Rejeté") & (raw_type == "observed")
    return data.loc[mask].copy()


def build_indicator_series(df: pd.DataFrame, indicator: str | None = None) -> pd.DataFrame:
    data = df.copy()
    if not data.empty:
        data = data.loc[_business_status(data) != "Rejeté"].copy()
    if indicator is not None:
        data = data[data["indicator"] == indicator].copy()
    data["Année"] = pd.to_numeric(data.get("current_year"), errors="coerce")
    data["Valeur numérique"] = pd.to_numeric(data.get("current_value"), errors="coerce")
    data = data.dropna(subset=["indicator", "Année", "Valeur numérique"])
    if data.empty:
        return _ensure_series_schema(data)
    data["Année"] = data["Année"].astype(int)
    # Preserve genuine contradictions but remove exact duplicates.
    sort_keys = [c for c in ["country", "series_id", "indicator", "Année", "confidence"] if c in data.columns]
    data = data.sort_values(sort_keys).drop_duplicates(
        subset=[c for c in ["country", "series_id", "indicator", "Année", "Valeur numérique", "current_unit", "current_scale", "current_currency"] if c in data.columns],
        keep="last",
    )
    group_cols = [c for c in ["country", "series_id", "indicator", "current_unit", "current_scale", "current_currency"] if c in data.columns]
    data["Évolution absolue"] = data.groupby(group_cols, dropna=False)["Valeur numérique"].diff()
    data["Évolution %"] = data.groupby(group_cols, dropna=False)["Valeur numérique"].pct_change(fill_method=None) * 100
    data["Sens"] = data["Évolution absolue"].map(
        lambda x: "—" if pd.isna(x) else "Hausse" if x > 0 else "Baisse" if x < 0 else "Stable"
    )
    data["Valeur affichée"] = data.get("Valeur", data["Valeur numérique"].astype(str))
    data = _ensure_series_schema(data)
    return data.sort_values([c for c in ["country", "series_id", "indicator", "Année", "Valeur numérique"] if c in data.columns])


def indicator_statistics(series: pd.DataFrame) -> dict:
    if series.empty:
        return {}
    values = series["Valeur numérique"].astype(float)
    years = series["Année"].astype(int)
    first = float(values.iloc[0])
    last = float(values.iloc[-1])
    total_abs = last - first
    total_pct = None if first == 0 else total_abs / abs(first) * 100
    span = int(years.iloc[-1] - years.iloc[0])
    cagr = None
    if span > 0 and first > 0 and last > 0:
        cagr = (last / first) ** (1 / span) - 1
    return {
        "observations": int(len(series)),
        "premiere_annee": int(years.min()),
        "derniere_annee": int(years.max()),
        "minimum": float(values.min()),
        "annee_minimum": int(series.loc[values.idxmin(), "Année"]),
        "maximum": float(values.max()),
        "annee_maximum": int(series.loc[values.idxmax(), "Année"]),
        "moyenne": float(values.mean()),
        "mediane": float(values.median()),
        "ecart_type": float(values.std(ddof=0)),
        "evolution_absolue": round(float(total_abs), 10),
        "evolution_pct": None if total_pct is None else round(float(total_pct), 10),
        "cagr_pct": None if cagr is None or not math.isfinite(cagr) else float(cagr * 100),
    }


def all_series_export(df: pd.DataFrame) -> pd.DataFrame:
    series = build_indicator_series(df)
    if series.empty:
        return series
    cols = [
        "series_id", "country_iso3", "indicator_id", "indicator", "indicator_category", "external_standard", "external_indicator_code", "Année", "Valeur affichée", "Valeur numérique", "current_unit",
        "current_scale", "current_currency", "Évolution absolue", "Évolution %", "Sens",
        "fact_type", "country", "Source", "sentence", "confidence", "needs_review",
    ]
    available = [c for c in cols if c in series.columns]
    return series[available].rename(columns={
        "series_id": "ID de série", "country_iso3": "Code pays ISO3", "indicator_id": "ID indicateur", "indicator": "Nom officiel de l’indicateur", "indicator_category": "Catégorie", "external_standard": "Référentiel externe", "external_indicator_code": "Code externe", "current_unit": "Unité", "current_scale": "Échelle",
        "current_currency": "Devise", "fact_type": "Nature", "country": "Pays",
        "sentence": "Phrase d’origine", "confidence": "Confiance", "needs_review": "À vérifier",
    })


def statistics_export(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_columns = [c for c in ["country", "series_id", "indicator"] if c in df.columns]
    historical = _historical_eligible(df)
    if historical.empty:
        return pd.DataFrame(columns=["Pays", "Indicateur", "Min", "Max", "Moyenne", "Médiane", "Évolution", "Évolution %", "Première période", "Dernière période"])
    for keys, group in historical.groupby(group_columns, dropna=False):
        series = build_indicator_series(group)
        stats = indicator_statistics(series)
        if stats:
            if not isinstance(keys, tuple):
                keys = (keys,)
            identity = dict(zip(group_columns, keys))
            rows.append({"Pays": identity.get("country"), "ID de série": identity.get("series_id"), "Indicateur": identity.get("indicator"), **stats})
    return pd.DataFrame(rows)


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    detailed = all_series_export(df)
    stats = statistics_export(df)
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        detailed.to_excel(writer, sheet_name="Series", index=False)
        stats.to_excel(writer, sheet_name="Statistiques", index=False)
        workbook = writer.book
        header = workbook.add_format({"bold": True, "bg_color": "#0B4F8A", "font_color": "#FFFFFF", "border": 1})
        number = workbook.add_format({"num_format": "0.00"})
        pct = workbook.add_format({"num_format": "0.00%"})
        for sheet_name, frame in [("Series", detailed), ("Statistiques", stats)]:
            ws = writer.sheets[sheet_name]
            ws.freeze_panes(1, 0)
            ws.autofilter(0, 0, max(len(frame), 1), max(len(frame.columns)-1, 0))
            for col_idx, col in enumerate(frame.columns):
                ws.write(0, col_idx, col, header)
                lengths = frame[col].dropna().astype(str).str.len() if len(frame) else pd.Series(dtype=float)
                q90 = lengths.quantile(.9) if not lengths.empty else None
                content_width = 12 if q90 is None or pd.isna(q90) else int(q90) + 2
                width = min(45, max(12, len(str(col)) + 2, content_width))
                ws.set_column(col_idx, col_idx, width)
            if sheet_name == "Series":
                for col_name in ["Valeur numérique", "Évolution absolue", "Évolution %", "Confiance"]:
                    if col_name in frame.columns:
                        idx = frame.columns.get_loc(col_name)
                        ws.set_column(idx, idx, 16, number)
    return output.getvalue()


def observations_export(df: pd.DataFrame) -> pd.DataFrame:
    """Business export: auditable fields only, no technical identifiers."""
    columns = ["Pays", "Indicateur", "Valeur", "Unité", "Période", "Type", "Source", "Phrase", "Confiance", "Statut"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    data = df.copy().reset_index(drop=True)
    missing = pd.Series([pd.NA] * len(data), index=data.index, dtype="object")
    year = pd.to_numeric(data.get("current_year", missing), errors="coerce")
    quarter = pd.to_numeric(data.get("current_quarter", missing), errors="coerce")
    month = pd.to_numeric(data.get("current_month", missing), errors="coerce")
    def period(i):
        if "current_period_label" in data.columns:
            raw = data.loc[i, "current_period_label"]
            if pd.notna(raw) and str(raw).strip(): return str(raw)
        parts=[]
        if pd.notna(month.iloc[i]) and month.iloc[i]: parts.append(f"M{int(month.iloc[i]):02d}")
        if pd.notna(quarter.iloc[i]) and quarter.iloc[i]: parts.append(f"T{int(quarter.iloc[i])}")
        if pd.notna(year.iloc[i]) and year.iloc[i]: parts.append(str(int(year.iloc[i])))
        return " ".join(parts) if parts else "À vérifier"
    units = [_measurement_label(row) for _, row in data.iterrows()]
    confidence = (pd.to_numeric(data.get("confidence"), errors="coerce").fillna(0) * 100).round(0).astype(int)
    return pd.DataFrame({
        "Pays": data.get("country"),
        "Indicateur": data.get("indicator"),
        "Valeur": data.get("current_value"),
        "Unité": units,
        "Période": [period(i) for i in range(len(data))],
        "Type": _business_type(data).values,
        "Source": data.get("source"),
        "Phrase": data.get("sentence"),
        "Confiance": confidence.values,
        "Statut": _business_status(data).values,
    })


def auditable_observations_export(df: pd.DataFrame) -> pd.DataFrame:
    """Business export with the semantic dimensions required to audit facts.

    The legacy compact export remains stable for integrations. User downloads
    use this richer contract so sector/table/partner information is never lost.
    """
    compact = observations_export(df)
    if df.empty:
        for column in ["Type géographique", "Secteur", "Sous-secteur", "Partenaire",
                       "Page", "Tableau", "Ligne du tableau", "Colonne du tableau",
                       "Source période", "Avertissements"]:
            compact[column] = pd.Series(dtype="object")
        return compact
    data = df.copy().reset_index(drop=True)
    warnings = data.get("validation_warnings", pd.Series([None] * len(data)))
    def clean_warnings(value):
        if isinstance(value, (list, tuple, set)):
            return "; ".join(str(v) for v in value)
        return _clean_optional(value)
    compact.insert(1, "Type géographique", data.get("geography_type"))
    compact.insert(3, "Secteur", data.get("sector"))
    compact.insert(4, "Sous-secteur", data.get("subsector"))
    compact.insert(5, "Partenaire", data.get("partner_geography"))
    compact["Page"] = data.get("table_page", data.get("page_number"))
    compact["Tableau"] = data.get("table_index")
    compact["Ligne du tableau"] = data.get("table_row_label")
    compact["Colonne du tableau"] = data.get("table_column_label")
    compact["Source période"] = data.get("period_resolution_source")
    compact["Avertissements"] = warnings.map(clean_warnings)
    return compact

def simple_series_export(df: pd.DataFrame) -> pd.DataFrame:
    """One row per annual point; review points stay visible, rejected points do not."""
    series = build_indicator_series(df)
    columns = ["Pays", "Indicateur", "Année", "Valeur", "Unité", "Type", "Statut"]
    if series.empty:
        return pd.DataFrame(columns=columns)
    units = [_measurement_label(row) for _, row in series.iterrows()]
    return pd.DataFrame({
        "Pays": series.get("country"),
        "Indicateur": series.get("indicator"),
        "Année": series["Année"].astype(int),
        "Valeur": series["Valeur numérique"],
        "Unité": units,
        "Type": _business_type(series).values,
        "Statut": _business_status(series).values,
    })

def simple_statistics_export(df: pd.DataFrame) -> pd.DataFrame:
    """Compact historical statistics: observed, non-rejected points only."""
    rows=[]
    group_columns = [c for c in ["country", "series_id", "indicator"] if c in df.columns]
    if not group_columns:
        group_columns = ["indicator"]
    historical = _historical_eligible(df)
    if historical.empty:
        return pd.DataFrame(columns=["Pays", "Indicateur", "Min", "Max", "Moyenne", "Médiane", "Évolution", "Évolution %", "Première période", "Dernière période"])
    for keys, group in historical.groupby(group_columns, dropna=False):
        series = build_indicator_series(group)
        stats = indicator_statistics(series)
        if not stats:
            continue
        if not isinstance(keys, tuple): keys=(keys,)
        identity=dict(zip(group_columns, keys))
        rows.append({
            "Pays": identity.get("country"),
            "Indicateur": identity.get("indicator"),
            "Min": stats["minimum"],
            "Max": stats["maximum"],
            "Moyenne": stats["moyenne"],
            "Médiane": stats["mediane"],
            "Évolution": stats["evolution_absolue"],
            "Évolution %": stats["evolution_pct"],
            "Première période": stats["premiere_annee"],
            "Dernière période": stats["derniere_annee"],
        })
    return pd.DataFrame(rows)
