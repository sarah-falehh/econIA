from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations

import pandas as pd


@dataclass
class Contradiction:
    country: str
    indicator: str
    period_key: str
    fact_id_a: int
    fact_id_b: int
    value_a: float
    value_b: float
    unit_a: str | None
    unit_b: str | None
    source_a: str | None
    source_b: str | None
    sentence_a: str
    sentence_b: str
    absolute_gap: float
    relative_gap_percent: float | None
    severity: str
    contradiction_type: str
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


def build_period_key(row: pd.Series) -> str | None:
    year = row.get("current_year")
    month = row.get("current_month")
    quarter = row.get("current_quarter")

    if pd.isna(year):
        return None

    year = int(year)

    if pd.notna(month) and month:
        return f"{year}-M{int(month):02d}"

    if pd.notna(quarter) and quarter:
        return f"{year}-Q{int(quarter)}"

    return str(year)


def normalize_unit(unit: str | None) -> str | None:
    if unit is None or pd.isna(unit):
        return None

    value = str(unit).strip().lower()

    aliases = {
        "pour cent": "%",
        "percent": "%",
        "percentage": "%",
        "percentage_point": "percentage_point",
        "points de pourcentage": "percentage_point",
        "tnd": "TND",
        "dt": "TND",
        "dinar": "TND",
        "dinars": "TND",
        "eur": "EUR",
        "euro": "EUR",
        "euros": "EUR",
        "usd": "USD",
        "dollar": "USD",
        "dollars": "USD",
        "million": "million",
        "millions": "million",
        "billion": "billion",
        "milliard": "billion",
        "milliards": "billion",
    }

    return aliases.get(value, unit)


def compute_severity(
    absolute_gap: float,
    relative_gap: float | None,
    unit: str | None,
) -> str:
    normalized_unit = normalize_unit(unit)

    if normalized_unit == "%":
        if absolute_gap >= 2:
            return "Élevée"
        if absolute_gap >= 0.5:
            return "Moyenne"
        return "Faible"

    if relative_gap is not None:
        if relative_gap >= 20:
            return "Élevée"
        if relative_gap >= 8:
            return "Moyenne"
        return "Faible"

    return "Moyenne"


def detect_contradictions(
    facts: list[dict],
) -> list[Contradiction]:
    if not facts:
        return []

    df = pd.DataFrame(facts)

    required_columns = [
        "id",
        "country",
        "indicator_code",
        "indicator",
        "value_type",
        "current_value",
        "current_unit",
        "current_year",
        "current_month",
        "current_quarter",
        "source",
        "sentence",
        "validation_status",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    # Contradictions are meaningful only for actual indicator levels.
    df = df[
        (df["value_type"] == "level")
        & df["current_value"].notna()
        & df["country"].notna()
        & df["indicator_code"].notna()
    ].copy()

    if df.empty:
        return []

    for column in [
        "current_value",
        "current_year",
        "current_month",
        "current_quarter",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["period_key"] = df.apply(
        build_period_key,
        axis=1,
    )

    df = df[df["period_key"].notna()].copy()

    contradictions: list[Contradiction] = []

    grouped = df.groupby(
        [
            "country",
            "indicator_code",
            "period_key",
        ],
        dropna=False,
    )

    for (
        country,
        indicator_code,
        period_key,
    ), group in grouped:
        if len(group) < 2:
            continue

        rows = list(
            group.to_dict("records")
        )

        for fact_a, fact_b in combinations(rows, 2):
            value_a = float(
                fact_a["current_value"]
            )
            value_b = float(
                fact_b["current_value"]
            )

            unit_a = normalize_unit(
                fact_a.get("current_unit")
            )
            unit_b = normalize_unit(
                fact_b.get("current_unit")
            )

            # Different units are reported as an incompatibility rather than
            # a direct numeric contradiction.
            if unit_a != unit_b:
                contradictions.append(
                    Contradiction(
                        country=str(country),
                        indicator=(
                            fact_a.get("indicator")
                            or str(indicator_code)
                        ),
                        period_key=str(period_key),
                        fact_id_a=int(fact_a["id"]),
                        fact_id_b=int(fact_b["id"]),
                        value_a=value_a,
                        value_b=value_b,
                        unit_a=unit_a,
                        unit_b=unit_b,
                        source_a=fact_a.get("source"),
                        source_b=fact_b.get("source"),
                        sentence_a=fact_a.get("sentence") or "",
                        sentence_b=fact_b.get("sentence") or "",
                        absolute_gap=abs(value_a - value_b),
                        relative_gap_percent=None,
                        severity="Élevée",
                        contradiction_type="Unités incompatibles",
                        explanation=(
                            "Les deux articles semblent parler du même "
                            "indicateur et de la même période, mais les "
                            "unités sont différentes."
                        ),
                    )
                )
                continue

            absolute_gap = abs(
                value_a - value_b
            )

            denominator = max(
                abs(value_a),
                abs(value_b),
                1e-9,
            )

            relative_gap = (
                absolute_gap
                / denominator
                * 100
            )

            # Ignore tiny differences caused by rounding.
            if unit_a == "%" and absolute_gap < 0.1:
                continue

            if unit_a != "%" and relative_gap < 1:
                continue

            severity = compute_severity(
                absolute_gap=absolute_gap,
                relative_gap=relative_gap,
                unit=unit_a,
            )

            contradiction_type = (
                "Valeurs divergentes"
            )

            explanation = (
                f"Deux valeurs différentes ont été détectées pour "
                f"{fact_a.get('indicator') or indicator_code}, "
                f"{country}, période {period_key}. "
                f"Écart absolu : {absolute_gap:.2f}"
            )

            if unit_a:
                explanation += f" {unit_a}"

            explanation += (
                f" ; écart relatif : "
                f"{relative_gap:.2f} %."
            )

            contradictions.append(
                Contradiction(
                    country=str(country),
                    indicator=(
                        fact_a.get("indicator")
                        or str(indicator_code)
                    ),
                    period_key=str(period_key),
                    fact_id_a=int(fact_a["id"]),
                    fact_id_b=int(fact_b["id"]),
                    value_a=value_a,
                    value_b=value_b,
                    unit_a=unit_a,
                    unit_b=unit_b,
                    source_a=fact_a.get("source"),
                    source_b=fact_b.get("source"),
                    sentence_a=fact_a.get("sentence") or "",
                    sentence_b=fact_b.get("sentence") or "",
                    absolute_gap=round(
                        absolute_gap,
                        4,
                    ),
                    relative_gap_percent=round(
                        relative_gap,
                        2,
                    ),
                    severity=severity,
                    contradiction_type=contradiction_type,
                    explanation=explanation,
                )
            )

    severity_order = {
        "Élevée": 0,
        "Moyenne": 1,
        "Faible": 2,
    }

    contradictions.sort(
        key=lambda item: (
            severity_order.get(
                item.severity,
                9,
            ),
            -item.absolute_gap,
        )
    )

    return contradictions


def detect_outliers(
    facts: list[dict],
) -> pd.DataFrame:
    """
    Statistical anomaly detection by country + indicator.
    Uses the robust IQR rule and requires at least four observations.
    """

    if not facts:
        return pd.DataFrame()

    df = pd.DataFrame(facts)

    required_columns = [
        "id",
        "country",
        "indicator_code",
        "indicator",
        "value_type",
        "current_value",
        "current_unit",
        "current_year",
        "current_month",
        "current_quarter",
        "source",
        "sentence",
    ]

    for column in required_columns:
        if column not in df.columns:
            df[column] = None

    df = df[
        (df["value_type"] == "level")
        & df["current_value"].notna()
        & df["country"].notna()
        & df["indicator_code"].notna()
    ].copy()

    if df.empty:
        return pd.DataFrame()

    df["current_value"] = pd.to_numeric(
        df["current_value"],
        errors="coerce",
    )

    df = df[
        df["current_value"].notna()
    ].copy()

    anomalies = []

    grouped = df.groupby(
        [
            "country",
            "indicator_code",
            "current_unit",
        ],
        dropna=False,
    )

    for (
        country,
        indicator_code,
        unit,
    ), group in grouped:
        if len(group) < 4:
            continue

        q1 = group["current_value"].quantile(
            0.25
        )
        q3 = group["current_value"].quantile(
            0.75
        )
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        group_anomalies = group[
            (group["current_value"] < lower_bound)
            | (group["current_value"] > upper_bound)
        ].copy()

        for _, row in group_anomalies.iterrows():
            distance = (
                lower_bound - row["current_value"]
                if row["current_value"] < lower_bound
                else row["current_value"] - upper_bound
            )

            anomalies.append(
                {
                    "Fact ID": int(row["id"]),
                    "Pays": country,
                    "Indicateur": (
                        row.get("indicator")
                        or indicator_code
                    ),
                    "Valeur": row["current_value"],
                    "Unité": unit,
                    "Année": row.get("current_year"),
                    "Source": row.get("source"),
                    "Distance à la limite": round(
                        float(distance),
                        4,
                    ),
                    "Phrase justificative": (
                        row.get("sentence")
                    ),
                }
            )

    return pd.DataFrame(anomalies)
