from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.services.auth_service import has_permission

from app.services.analytics_service import (
    business_table,
    comparison_table,
    export_analysis_excel,
    prepare_analysis_dataframe,
)
from app.services.database import fetch_business_facts


def _multiselect_filter(
    df: pd.DataFrame,
    column: str,
    label: str,
) -> list:
    values = sorted(
        value
        for value in df[column].dropna().unique()
    )

    return st.multiselect(
        label,
        options=values,
        default=values,
    )


def render_analysis_dashboard() -> None:
    st.title(
        "Tableau d’analyse économique"
    )

    st.caption(
        "Explorez les faits extraits, leurs comparaisons "
        "et leur niveau de validation."
    )

    facts = fetch_business_facts(
        limit=10000
    )

    if not facts:
        st.warning(
            "Aucun fait économique n’est disponible. "
            "Lancez d’abord une extraction."
        )
        return

    df = prepare_analysis_dataframe(facts)

    with st.expander(
        "Filtres",
        expanded=True,
    ):
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_countries = _multiselect_filter(
                df,
                "country_label",
                "Pays",
            )

            selected_indicators = _multiselect_filter(
                df,
                "indicator",
                "Indicateurs",
            )

        with col2:
            selected_types = _multiselect_filter(
                df,
                "value_type_label",
                "Types de valeurs",
            )

            selected_directions = _multiselect_filter(
                df,
                "direction_label",
                "Directions",
            )

        with col3:
            selected_validation = _multiselect_filter(
                df,
                "validation_label",
                "Statut de validation",
            )

            years = sorted(
                int(year)
                for year in df["current_year"]
                .dropna()
                .unique()
            )

            selected_years = st.multiselect(
                "Années",
                options=years,
                default=years,
            )

    filtered = df[
        df["country_label"].isin(selected_countries)
        & df["indicator"].isin(selected_indicators)
        & df["value_type_label"].isin(selected_types)
        & df["direction_label"].isin(selected_directions)
        & df["validation_label"].isin(selected_validation)
    ].copy()

    if selected_years:
        filtered = filtered[
            filtered["current_year"].isna()
            | filtered["current_year"].isin(
                selected_years
            )
        ]

    if filtered.empty:
        st.info(
            "Aucune donnée ne correspond aux filtres."
        )
        return

    st.subheader(
        "Vue d’ensemble"
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Faits",
        len(filtered),
    )

    col2.metric(
        "Pays",
        filtered["country_label"].nunique(),
    )

    col3.metric(
        "Indicateurs",
        filtered["indicator"].nunique(),
    )

    col4.metric(
        "Comparaisons",
        int(
            filtered["reference_value"]
            .notna()
            .sum()
        ),
    )

    col5.metric(
        "Validés",
        int(
            (
                filtered["validation_status"]
                == "validated"
            ).sum()
        ),
    )

    st.subheader(
        "Répartition des faits"
    )

    col_left, col_right = st.columns(2)

    with col_left:
        indicator_counts = (
            filtered["indicator"]
            .value_counts()
            .reset_index()
        )

        indicator_counts.columns = [
            "Indicateur",
            "Nombre",
        ]

        fig_indicators = px.bar(
            indicator_counts,
            x="Nombre",
            y="Indicateur",
            orientation="h",
            title="Faits par indicateur",
        )

        fig_indicators.update_layout(
            height=420,
            yaxis={
                "categoryorder": "total ascending"
            },
        )

        st.plotly_chart(
            fig_indicators,
            width="stretch",
        )

    with col_right:
        direction_counts = (
            filtered["direction_label"]
            .value_counts()
            .reset_index()
        )

        direction_counts.columns = [
            "Direction",
            "Nombre",
        ]

        fig_directions = px.pie(
            direction_counts,
            names="Direction",
            values="Nombre",
            title="Répartition des directions",
            hole=0.45,
        )

        fig_directions.update_layout(
            height=420
        )

        st.plotly_chart(
            fig_directions,
            width="stretch",
        )

    st.subheader(
        "Évolution des valeurs"
    )

    level_df = filtered[
        (filtered["value_type"] == "level")
        & filtered["current_value"].notna()
        & filtered["current_year"].notna()
    ].copy()

    if level_df.empty:
        st.info(
            "Aucune série de niveaux avec année "
            "n’est disponible pour les filtres choisis."
        )
    else:
        selected_indicator = st.selectbox(
            "Indicateur à visualiser",
            options=sorted(
                level_df["indicator"].unique()
            ),
        )

        trend_df = level_df[
            level_df["indicator"]
            == selected_indicator
        ].copy()

        trend_df = trend_df.sort_values(
            [
                "country_label",
                "current_year",
                "current_month",
                "current_quarter",
            ]
        )

        fig_trend = px.line(
            trend_df,
            x="current_year",
            y="current_value",
            color="country_label",
            markers=True,
            hover_data=[
                "period_label",
                "effective_unit",
                "source_label",
                "sentence",
            ],
            labels={
                "current_year": "Année",
                "current_value": "Valeur",
                "country_label": "Pays",
            },
            title=(
                f"Évolution de l’indicateur : "
                f"{selected_indicator}"
            ),
        )

        fig_trend.update_layout(
            height=430
        )

        st.plotly_chart(
            fig_trend,
            width="stretch",
        )

        st.caption(
            "Cette visualisation utilise les valeurs "
            "réellement extraites, et non le nombre de mentions."
        )

    st.subheader(
        "Comparaisons détectées"
    )

    comparisons = comparison_table(filtered)

    if comparisons.empty:
        st.info(
            "Aucune comparaison complète n’est disponible."
        )
    else:
        st.dataframe(
            comparisons,
            width="stretch",
            hide_index=True,
            column_config={
                "Phrase justificative": (
                    st.column_config.TextColumn(
                        "Phrase justificative",
                        width="large",
                    )
                )
            },
        )

        chart_comparisons = filtered[
            filtered["absolute_change"].notna()
        ].copy()

        if not chart_comparisons.empty:
            chart_comparisons["Libellé"] = (
                chart_comparisons["country_label"]
                + " — "
                + chart_comparisons["indicator"]
            )

            fig_comparison = go.Figure()

            fig_comparison.add_trace(
                go.Bar(
                    x=chart_comparisons["Libellé"],
                    y=chart_comparisons["reference_value"],
                    name="Référence",
                )
            )

            fig_comparison.add_trace(
                go.Bar(
                    x=chart_comparisons["Libellé"],
                    y=chart_comparisons["current_value"],
                    name="Valeur actuelle",
                )
            )

            fig_comparison.update_layout(
                barmode="group",
                height=430,
                title=(
                    "Valeur actuelle contre valeur "
                    "de référence"
                ),
                xaxis_title="",
                yaxis_title="Valeur",
            )

            st.plotly_chart(
                fig_comparison,
                width="stretch",
            )

    st.subheader(
        "Tableau détaillé"
    )

    clean_table = business_table(filtered)

    st.dataframe(
        clean_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Confiance": st.column_config.ProgressColumn(
                "Confiance",
                min_value=0,
                max_value=100,
                format="%.0f %%",
            ),
            "Phrase justificative": (
                st.column_config.TextColumn(
                    "Phrase justificative",
                    width="large",
                )
            ),
        },
    )

    excel_data = export_analysis_excel(
        filtered
    )

    if has_permission(st.session_state.get("user"), "export"):
        st.download_button(
            "Exporter l’analyse en Excel",
        data=excel_data,
        file_name="analyse_economique.xlsx",
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        width="stretch",
    )
