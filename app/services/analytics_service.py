from __future__ import annotations

from io import BytesIO

import pandas as pd


VALUE_TYPE_LABELS = {
    "level": "Niveau",
    "relative_change": "Variation relative",
    "absolute_change": "Variation absolue",
}

DIRECTION_LABELS = {
    "increase": "Hausse",
    "decrease": "Baisse",
    "stable": "Stable",
    "unknown": "Non déterminable",
}

MONTH_NAMES = {
    1: "Janvier",
    2: "Février",
    3: "Mars",
    4: "Avril",
    5: "Mai",
    6: "Juin",
    7: "Juillet",
    8: "Août",
    9: "Septembre",
    10: "Octobre",
    11: "Novembre",
    12: "Décembre",
}


def prepare_analysis_dataframe(
    facts: list[dict],
) -> pd.DataFrame:
    df = pd.DataFrame(facts)

    if df.empty:
        return df

    numeric_columns = [
        "current_value",
        "variation_value",
        "reference_value",
        "absolute_change",
        "relative_change",
        "confidence",
        "current_month",
        "current_quarter",
        "current_year",
        "reference_month",
        "reference_quarter",
        "reference_year",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    df["value_type_label"] = (
        df["value_type"]
        .map(VALUE_TYPE_LABELS)
        .fillna(df["value_type"])
    )

    df["direction_label"] = (
        df["direction"]
        .map(DIRECTION_LABELS)
        .fillna("Non déterminable")
    )

    df["country_label"] = df["country"].fillna(
        "Non détecté"
    )

    df["source_label"] = df["source"].fillna(
        "Non détectée"
    )

    df["validation_label"] = (
        df["validation_status"]
        .map(
            {
                "validated": "Validé",
                "rejected": "Rejeté",
                "pending": "En attente",
            }
        )
        .fillna("En attente")
    )

    df["effective_value"] = df.apply(
        lambda row: (
            row["current_value"]
            if row["value_type"] == "level"
            else row["variation_value"]
        ),
        axis=1,
    )

    df["effective_unit"] = df.apply(
        lambda row: (
            row["current_unit"]
            if row["value_type"] == "level"
            else row["variation_unit"]
        ),
        axis=1,
    )

    df["period_label"] = df.apply(
        lambda row: build_period_label(
            row.get("current_month"),
            row.get("current_quarter"),
            row.get("current_year"),
        ),
        axis=1,
    )

    df["reference_period_label"] = df.apply(
        lambda row: build_period_label(
            row.get("reference_month"),
            row.get("reference_quarter"),
            row.get("reference_year"),
        ),
        axis=1,
    )

    df["confidence_percent"] = (
        df["confidence"].fillna(0) * 100
    )

    df["review_label"] = df.apply(
        lambda row: (
            "À vérifier"
            if bool(row.get("needs_review"))
            else "Validable"
        ),
        axis=1,
    )

    return df


def build_period_label(
    month,
    quarter,
    year,
) -> str:
    parts = []

    if pd.notna(month) and month:
        parts.append(
            MONTH_NAMES.get(
                int(month),
                f"M{int(month):02d}",
            )
        )

    if pd.notna(quarter) and quarter:
        parts.append(f"T{int(quarter)}")

    if pd.notna(year) and year:
        parts.append(str(int(year)))

    return (
        " ".join(parts)
        if parts
        else "Non détectée"
    )


def format_numeric_value(
    value,
    unit,
) -> str:
    if pd.isna(value):
        return "Non disponible"

    numeric = float(value)

    if numeric.is_integer():
        formatted = f"{int(numeric):,}"
    else:
        formatted = f"{numeric:,.2f}".rstrip("0").rstrip(".")

    formatted = formatted.replace(",", " ")

    if pd.isna(unit) or not unit:
        return formatted

    return f"{formatted} {unit}"


def business_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    if df.empty:
        return df

    result = pd.DataFrame(
        {
            "Pays": df["country_label"],
            "Indicateur": df["indicator"],
            "Type": df["value_type_label"],
            "Valeur": [
                format_numeric_value(value, unit)
                for value, unit in zip(
                    df["effective_value"],
                    df["effective_unit"],
                )
            ],
            "Période": df["period_label"],
            "Référence": [
                format_numeric_value(value, unit)
                for value, unit in zip(
                    df["reference_value"],
                    df["reference_unit"],
                )
            ],
            "Période de référence": (
                df["reference_period_label"]
            ),
            "Direction": df["direction_label"],
            "Source": df["source_label"],
            "Validation": df["validation_label"],
            "Confiance": df["confidence_percent"],
            "Phrase justificative": df["sentence"],
        }
    )

    return result


def comparison_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    if df.empty:
        return df

    comparisons = df[
        df["reference_value"].notna()
        | df["comparison_type"].notna()
    ].copy()

    if comparisons.empty:
        return comparisons

    return pd.DataFrame(
        {
            "Pays": comparisons["country_label"],
            "Indicateur": comparisons["indicator"],
            "Valeur actuelle": [
                format_numeric_value(value, unit)
                for value, unit in zip(
                    comparisons["current_value"],
                    comparisons["current_unit"],
                )
            ],
            "Période actuelle": (
                comparisons["period_label"]
            ),
            "Valeur de référence": [
                format_numeric_value(value, unit)
                for value, unit in zip(
                    comparisons["reference_value"],
                    comparisons["reference_unit"],
                )
            ],
            "Période de référence": (
                comparisons["reference_period_label"]
            ),
            "Écart absolu": (
                comparisons["absolute_change"]
            ),
            "Variation relative (%)": (
                comparisons["relative_change"]
            ),
            "Direction": comparisons["direction_label"],
            "Phrase justificative": comparisons["sentence"],
        }
    )


def export_analysis_excel(
    filtered_df: pd.DataFrame,
) -> bytes:
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="xlsxwriter",
    ) as writer:
        business = business_table(filtered_df)
        comparisons = comparison_table(filtered_df)

        business.to_excel(
            writer,
            sheet_name="Faits économiques",
            index=False,
        )

        if not comparisons.empty:
            comparisons.to_excel(
                writer,
                sheet_name="Comparaisons",
                index=False,
            )

        indicator_summary = (
            filtered_df.groupby(
                ["country_label", "indicator"],
                dropna=False,
            )
            .size()
            .reset_index(name="Nombre de faits")
            .rename(
                columns={
                    "country_label": "Pays",
                    "indicator": "Indicateur",
                }
            )
        )

        indicator_summary.to_excel(
            writer,
            sheet_name="Résumé indicateurs",
            index=False,
        )

        workbook = writer.book

        header_format = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#003087",
                "font_color": "#FFFFFF",
                "border": 1,
            }
        )

        for sheet_name, worksheet in writer.sheets.items():
            worksheet.freeze_panes(1, 0)
            worksheet.autofilter(
                0,
                0,
                worksheet.dim_rowmax,
                worksheet.dim_colmax,
            )

            for column_index, column_name in enumerate(
                writer.sheets[sheet_name].table
                if hasattr(
                    writer.sheets[sheet_name],
                    "table",
                )
                else []
            ):
                _ = column_index, column_name

            worksheet.set_row(
                0,
                24,
                header_format,
            )

            worksheet.set_column(
                0,
                20,
                20,
            )

    output.seek(0)
    return output.getvalue()
