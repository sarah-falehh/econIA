from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.services.auth_service import has_permission

from app.services.contradiction_detector import (
    detect_contradictions,
    detect_outliers,
)
from app.services.database import (
    fetch_business_facts,
)


SEVERITY_ICONS = {
    "Élevée": "🔴",
    "Moyenne": "🟠",
    "Faible": "🟡",
}


def render_contradiction_radar() -> None:
    st.title(
        "Radar de contradictions"
    )

    st.caption(
        "Détection automatique des valeurs divergentes, "
        "unités incompatibles et anomalies statistiques."
    )

    facts = fetch_business_facts(
        limit=20000
    )

    if not facts:
        st.warning(
            "Aucun fait économique n’est disponible."
        )
        return

    contradictions = detect_contradictions(
        facts
    )

    outliers = detect_outliers(
        facts
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Contradictions",
        len(contradictions),
    )

    col2.metric(
        "Gravité élevée",
        sum(
            item.severity == "Élevée"
            for item in contradictions
        ),
    )

    col3.metric(
        "Anomalies statistiques",
        len(outliers),
    )

    col4.metric(
        "Faits analysés",
        len(facts),
    )

    st.divider()

    tab_contradictions, tab_outliers, tab_method = st.tabs(
        [
            "Contradictions entre articles",
            "Anomalies statistiques",
            "Méthode",
        ]
    )

    with tab_contradictions:
        if not contradictions:
            st.success(
                "Aucune contradiction significative "
                "n’a été détectée pour le moment."
            )
        else:
            contradiction_df = pd.DataFrame(
                [
                    item.to_dict()
                    for item in contradictions
                ]
            )

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                severity_options = sorted(
                    contradiction_df["severity"]
                    .dropna()
                    .unique()
                )

                selected_severity = st.multiselect(
                    "Gravité",
                    options=severity_options,
                    default=severity_options,
                )

            with filter_col2:
                indicator_options = sorted(
                    contradiction_df["indicator"]
                    .dropna()
                    .unique()
                )

                selected_indicators = st.multiselect(
                    "Indicateurs",
                    options=indicator_options,
                    default=indicator_options,
                )

            filtered = contradiction_df[
                contradiction_df["severity"].isin(
                    selected_severity
                )
                & contradiction_df["indicator"].isin(
                    selected_indicators
                )
            ].copy()

            if filtered.empty:
                st.info(
                    "Aucune contradiction ne correspond "
                    "aux filtres sélectionnés."
                )
            else:
                severity_counts = (
                    filtered["severity"]
                    .value_counts()
                    .reset_index()
                )

                severity_counts.columns = [
                    "Gravité",
                    "Nombre",
                ]

                fig = px.bar(
                    severity_counts,
                    x="Gravité",
                    y="Nombre",
                    title=(
                        "Contradictions par niveau "
                        "de gravité"
                    ),
                )

                fig.update_layout(
                    height=330
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                )

                compact = filtered[
                    [
                        "country",
                        "indicator",
                        "period_key",
                        "value_a",
                        "unit_a",
                        "value_b",
                        "unit_b",
                        "absolute_gap",
                        "relative_gap_percent",
                        "severity",
                        "contradiction_type",
                    ]
                ].rename(
                    columns={
                        "country": "Pays",
                        "indicator": "Indicateur",
                        "period_key": "Période",
                        "value_a": "Valeur A",
                        "unit_a": "Unité A",
                        "value_b": "Valeur B",
                        "unit_b": "Unité B",
                        "absolute_gap": "Écart absolu",
                        "relative_gap_percent": (
                            "Écart relatif (%)"
                        ),
                        "severity": "Gravité",
                        "contradiction_type": "Type",
                    }
                )

                st.dataframe(
                    compact,
                    width="stretch",
                    hide_index=True,
                )

                st.subheader(
                    "Analyse détaillée"
                )

                for _, row in filtered.iterrows():
                    icon = SEVERITY_ICONS.get(
                        row["severity"],
                        "⚪",
                    )

                    title = (
                        f"{icon} {row['indicator']} — "
                        f"{row['country']} — "
                        f"{row['period_key']}"
                    )

                    with st.expander(title):
                        st.warning(
                            row["explanation"]
                        )

                        left, right = st.columns(2)

                        with left:
                            st.markdown(
                                "### Source A"
                            )
                            st.write(
                                f"**Source :** "
                                f"{row['source_a'] or 'Non détectée'}"
                            )
                            st.write(
                                f"**Valeur :** "
                                f"{row['value_a']} "
                                f"{row['unit_a'] or ''}"
                            )
                            st.info(
                                row["sentence_a"]
                            )

                        with right:
                            st.markdown(
                                "### Source B"
                            )
                            st.write(
                                f"**Source :** "
                                f"{row['source_b'] or 'Non détectée'}"
                            )
                            st.write(
                                f"**Valeur :** "
                                f"{row['value_b']} "
                                f"{row['unit_b'] or ''}"
                            )
                            st.info(
                                row["sentence_b"]
                            )

                if has_permission(st.session_state.get("user"), "export"):
                    st.download_button(
                        "Exporter les contradictions",
                    data=filtered.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="contradictions_economiques.csv",
                    mime="text/csv",
                    width="stretch",
                )

    with tab_outliers:
        if outliers.empty:
            st.info(
                "Aucune anomalie statistique n’a été "
                "détectée. Au moins quatre observations "
                "homogènes sont nécessaires par série."
            )
        else:
            st.dataframe(
                outliers,
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

            fig_outliers = px.scatter(
                outliers,
                x="Année",
                y="Valeur",
                color="Indicateur",
                symbol="Pays",
                hover_data=[
                    "Source",
                    "Unité",
                    "Phrase justificative",
                ],
                title=(
                    "Valeurs atypiques détectées "
                    "dans les séries"
                ),
            )

            fig_outliers.update_layout(
                height=430
            )

            st.plotly_chart(
                fig_outliers,
                width="stretch",
            )

            if has_permission(st.session_state.get("user"), "export"):
                st.download_button(
                    "Exporter les anomalies",
                data=outliers.to_csv(
                    index=False
                ).encode("utf-8-sig"),
                file_name="anomalies_economiques.csv",
                mime="text/csv",
                width="stretch",
            )

    with tab_method:
        st.markdown(
            """
            ### Contradictions entre articles

            Les faits sont regroupés selon :

            - le pays ;
            - l’indicateur normalisé ;
            - la période exacte ;
            - le type de valeur `niveau`.

            Deux faits du même groupe sont comparés. Les
            différences dues à un simple arrondi sont ignorées.

            ### Gravité

            Pour les pourcentages :

            - moins de 0,5 point : faible ;
            - entre 0,5 et 2 points : moyenne ;
            - au moins 2 points : élevée.

            Pour les autres unités, la gravité dépend de
            l’écart relatif entre les deux valeurs.

            ### Anomalies statistiques

            Le radar utilise la règle robuste de l’intervalle
            interquartile. Une observation est atypique si elle
            se situe en dehors de :

            `Q1 - 1,5 × IQR` ou `Q3 + 1,5 × IQR`.

            Ce système n’affirme pas automatiquement qu’un article
            est faux : il signale les cas qui doivent être vérifiés.
            """
        )
