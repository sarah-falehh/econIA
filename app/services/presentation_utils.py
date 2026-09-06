from __future__ import annotations

import pandas as pd


def is_emptyish_display(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip().lower() in {"", "none", "nan", "null", "<na>"}


def prune_display_columns(frame: pd.DataFrame, force_drop: tuple[str, ...] = ("Source période", "Avertissements", "Page", "Tableau", "Ligne du tableau", "Colonne du tableau", "Secteur")) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    for column in force_drop:
        if column in out.columns:
            out = out.drop(columns=[column])
    empty_columns = [column for column in out.columns if out[column].map(is_emptyish_display).all()]
    if empty_columns:
        out = out.drop(columns=empty_columns)
    return out


def period_label(frame: pd.DataFrame) -> pd.Series:
    if "period_label" in frame.columns:
        provided = frame["period_label"].fillna("").astype(str)
    else:
        provided = pd.Series("", index=frame.index)
    year = pd.to_numeric(frame.get("current_year"), errors="coerce")
    quarter = pd.to_numeric(frame.get("current_quarter"), errors="coerce")
    month = pd.to_numeric(frame.get("current_month"), errors="coerce")
    labels: list[str] = []
    for idx in frame.index:
        if provided.loc[idx].strip():
            labels.append(provided.loc[idx].strip())
            continue
        y = year.loc[idx] if idx in year.index else None
        if pd.isna(y):
            labels.append("—")
            continue
        year_value = int(y)
        quarter_value = quarter.loc[idx] if idx in quarter.index else None
        month_value = month.loc[idx] if idx in month.index else None
        if pd.notna(quarter_value):
            labels.append(f"{year_value}-Q{int(quarter_value)}")
        elif pd.notna(month_value):
            labels.append(f"{year_value}-M{int(month_value):02d}")
        else:
            labels.append(str(year_value))
    return pd.Series(labels, index=frame.index)


def horizontal_series_table(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["Pays", "Indicateur", "Unité"])
    table = pd.DataFrame(index=frame.index)
    table["Pays"] = frame.get("country", frame.get("Pays"))
    table["Indicateur"] = frame.get("indicator", frame.get("Indicateur"))
    table["Période"] = period_label(frame if "current_year" in frame.columns or "period_label" in frame.columns else frame.rename(columns={"Période": "period_label"}))
    if "current_value" in frame.columns:
        values = pd.to_numeric(frame.get("current_value"), errors="coerce")
    else:
        values = frame.get("Valeur")
    table["Valeur"] = values.astype(str)

    unit = frame.get("current_unit", frame.get("Unité", pd.Series("", index=frame.index))).fillna("").astype(str)
    scale = frame.get("current_scale", pd.Series("", index=frame.index)).fillna("").astype(str)
    currency = frame.get("current_currency", pd.Series("", index=frame.index)).fillna("").astype(str)
    table["Unité"] = [" ".join(x for x in (s, u, c) if x and x.lower() not in {"nan", "none"}).strip() for s, u, c in zip(scale, unit, currency)]

    period_order = list(dict.fromkeys(table["Période"].astype(str).tolist()))
    pivot = (
        table.groupby(["Pays", "Indicateur", "Unité", "Période"], dropna=False)["Valeur"]
        .apply(lambda items: " | ".join(dict.fromkeys(items.astype(str))))
        .unstack("Période")
        .reset_index()
    )
    ordered_columns = [c for c in ["Pays", "Indicateur", "Unité"] if c in pivot.columns] + [c for c in period_order if c in pivot.columns]
    return pivot.reindex(columns=ordered_columns)
