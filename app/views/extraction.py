from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.auth_service import has_permission

from app.services.database import (
    create_analysis,
    detect_observation_conflicts,
    fetch_business_facts,
    fetch_full_documents,
    replace_business_facts,
)
from app.services.economic_extractor import (
    extract_facts_from_document,
)
from app.services.language_detector import language_label
from app.services.multi_agent_pipeline import get_last_trace
from app.services.series_analytics import observations_export, simple_series_export, simple_statistics_export


VALUE_TYPE_LABELS = {
    "level": "Niveau",
    "relative_change": "Variation relative",
    "absolute_change": "Variation absolue",
}

FACT_TYPE_LABELS = {
    "observed": "Observé",
    "estimate": "Estimation",
    "forecast": "Prévision",
}

DIRECTION_LABELS = {
    "increase": "Hausse",
    "decrease": "Baisse",
    "stable": "Stable",
    "unknown": "Non déterminable",
}


def period_label(
    month,
    quarter,
    year,
) -> str:
    parts = []

    if pd.notna(month) and month:
        parts.append(f"M{int(month):02d}")

    if pd.notna(quarter) and quarter:
        parts.append(f"T{int(quarter)}")

    if pd.notna(year) and year:
        parts.append(str(int(year)))

    return (
        " ".join(parts)
        if parts
        else "Non détectée"
    )


def value_label(
    value,
    unit,
    scale=None,
    currency=None,
) -> str:
    if pd.isna(value):
        return "Non disponible"

    number = f"{float(value):,.2f}"
    number = number.rstrip("0").rstrip(".")
    number = number.replace(",", " ")

    parts = [number]

    if pd.notna(scale) and scale:
        parts.append(str(scale))

    if pd.notna(currency) and currency:
        parts.append(str(currency))
    elif pd.notna(unit) and unit:
        parts.append(str(unit))

    return " ".join(parts)


def prepare_dataframe(
    facts: list[dict],
) -> pd.DataFrame:
    df = pd.DataFrame(facts)

    if df.empty:
        return df

    df["Type de valeur"] = (
        df["value_type"]
        .map(VALUE_TYPE_LABELS)
        .fillna(df["value_type"])
    )

    df["Type de fait"] = (
        df["fact_type"]
        .map(FACT_TYPE_LABELS)
        .fillna(df["fact_type"])
    )

    df["Thème"] = df["topic"].fillna("Autre")

    df["Valeur"] = df.apply(
        lambda row: (
            value_label(
                row["current_value"],
                row["current_unit"],
                row.get("current_scale"),
                row.get("current_currency"),
            )
            if row["value_type"] == "level"
            else value_label(
                row["variation_value"],
                row["variation_unit"],
            )
        ),
        axis=1,
    )

    df["Période"] = df.apply(
        lambda row: period_label(
            row["current_month"],
            row["current_quarter"],
            row["current_year"],
        ),
        axis=1,
    )

    df["Référence"] = df.apply(
        lambda row: value_label(
            row["reference_value"],
            row["reference_unit"],
            row.get("reference_scale"),
            row.get("reference_currency"),
        ),
        axis=1,
    )

    df["Période de référence"] = df.apply(
        lambda row: period_label(
            row["reference_month"],
            row["reference_quarter"],
            row["reference_year"],
        ),
        axis=1,
    )

    df["Direction"] = (
        df["direction"]
        .map(DIRECTION_LABELS)
        .fillna("Non déterminable")
    )

    df["Confiance"] = (
        pd.to_numeric(
            df["confidence"],
            errors="coerce",
        )
        .fillna(0)
        * 100
    )

    df["Statut"] = df.apply(
        lambda row: (
            "À vérifier"
            if bool(row["needs_review"])
            else "Validable"
        ),
        axis=1,
    )

    df["Pays"] = df["country"].fillna(
        "Non détecté"
    )

    df["Source"] = df["source"].fillna(
        "Non détectée"
    )

    return df


def business_export(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Canonical business table backed by the same serializer as CSV exports.

    Keeping one serialization path prevents UI/export drift (notably pandas NaN
    leaking into unit labels or validation statuses being remapped differently).
    """
    return observations_export(df).rename(columns={"Phrase": "Phrase source"})


def render_extraction_page() -> None:
    st.title("Analyse économique structurée")

    st.caption(
        "Extraction multilingue des niveaux, "
        "variations, périodes et comparaisons."
    )

    documents = fetch_full_documents(
        limit=5000
    )

    if not documents:
        st.warning(
            "Importez et enregistrez d'abord un article."
        )
        return

    labels = {
        index: (
            f"{document.get('title') or 'Sans titre'} "
            f"— {language_label(document.get('language'))}"
        )
        for index, document in enumerate(documents)
    }

    selected = st.multiselect(
        "Documents à analyser",
        options=list(labels),
        default=[0],
        format_func=lambda index: labels[index],
    )

    engine_label = st.radio(
        "Moteur de sélection du contenu",
        options=["multi_agent", "strict", "ollama"],
        format_func=lambda value: (
            "Moteur contextuel déterministe (recommandé)" if value == "multi_agent" else (
                "Filtre strict local (rapide)" if value == "strict" else "Ancien moteur Ollama (optionnel)"
            )
        ),
        horizontal=True,
        help=(
            "Le filtre intervient avant l'extraction et écarte annexes, "
            "bibliographie, équations, tableaux économétriques et légendes."
        ),
    )
    ollama_model = "qwen2.5:7b"
    if engine_label == "ollama":
        ollama_model = st.text_input("Modèle Ollama", value="qwen2.5:7b")
        st.caption("Mode historique optionnel. Le moteur recommandé ne nécessite ni Ollama, ni GPU, ni LLM local.")

    if st.button(
        "Lancer l'analyse",
        type="primary",
        width="stretch",
        disabled=not selected,
    ):
        progress = st.progress(0)
        all_facts = []

        for position, index in enumerate(selected):
            document = documents[index]

            facts = [
                fact.to_dict()
                for fact in extract_facts_from_document(
                    document,
                    selection_mode=engine_label,
                    ollama_model=ollama_model,
                )
            ]

            replace_business_facts(
                document_id=document["document_id"],
                facts=facts,
            )
            analysis_id = create_analysis(
                document["document_id"],
                document.get("filename") or document.get("title") or document["document_id"],
                document.get("input_type"),
                facts,
            )
            st.session_state["current_analysis_id"] = analysis_id

            all_facts.extend(facts)

            progress.progress(
                (position + 1) / len(selected)
            )

        detect_observation_conflicts()
        st.session_state["business_latest"] = all_facts

        st.success(
            f"{len(all_facts)} fait(s) économique(s) détecté(s)."
        )

        if engine_label == "multi_agent":
            st.session_state["multi_agent_trace"] = get_last_trace()

    trace = st.session_state.get("multi_agent_trace")
    if trace:
        st.divider()
        st.subheader("Traçabilité du pipeline multi-agents")
        c1, c2, c3 = st.columns(3)
        c1.metric("Passages analysés", trace.get("paragraphs_total", 0))
        c2.metric("Passages retenus", len(trace.get("kept", [])))
        c3.metric("Faits validés", trace.get("validated_count", 0))
        with st.expander("Agent 1 — passages retenus"):
            for item in trace.get("kept", []): st.write("•", item)
        with st.expander("Agent 1 — passages rejetés"):
            st.dataframe(pd.DataFrame(trace.get("rejected_structure", [])), width="stretch", hide_index=True)
        with st.expander("Agent 2 — contexte détecté"):
            st.json(trace.get("context", {}))
        with st.expander("Agent 3 — extraction brute"):
            st.json(trace.get("raw_facts", []))
        with st.expander("Agent 4 — rejets de validation"):
            st.json(trace.get("rejected_validation", []))

    latest = st.session_state.get(
        "business_latest",
        [],
    )

    if latest:
        df = prepare_dataframe(latest)

        st.divider()
        st.subheader("Résumé")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Faits extraits",
            len(df),
        )

        col2.metric(
            "Niveaux",
            int(
                (
                    df["value_type"] == "level"
                ).sum()
            ),
        )

        col3.metric(
            "Variations",
            int(
                (
                    df["value_type"] != "level"
                ).sum()
            ),
        )

        col4.metric(
            "À vérifier",
            int(
                df["needs_review"]
                .astype(bool)
                .sum()
            ),
        )

        st.subheader(
            "Tableau métier"
        )

        clean_df = business_export(df)

        st.dataframe(
            clean_df,
            width="stretch",
            hide_index=True,
            column_config={
                "Confiance": st.column_config.ProgressColumn(
                    "Confiance",
                    min_value=0,
                    max_value=100,
                    format="%.0f %%",
                ),
                "Phrase source": (
                    st.column_config.TextColumn(
                        "Phrase source",
                        width="large",
                    )
                ),
            },
        )

        if has_permission(st.session_state.get("user"), "export"):
            from app.services.series_analytics import auditable_observations_export
            observations_csv = auditable_observations_export(df)
            series_csv = simple_series_export(df)
            statistics_csv = simple_statistics_export(df)
            c1, c2, c3 = st.columns(3)
            c1.download_button(
                "Observations CSV",
                data=observations_csv.to_csv(index=False).encode("utf-8-sig"),
                file_name="observations.csv",
                mime="text/csv",
                width="stretch",
            )
            c2.download_button(
                "Séries CSV",
                data=series_csv.to_csv(index=False).encode("utf-8-sig"),
                file_name="series.csv",
                mime="text/csv",
                width="stretch",
            )
            c3.download_button(
                "Statistiques CSV",
                data=statistics_csv.to_csv(index=False).encode("utf-8-sig"),
                file_name="statistics.csv",
                mime="text/csv",
                width="stretch",
            )

        st.subheader(
            "Détails et preuves"
        )

        for index, row in df.iterrows():
            status_icon = (
                "⚠"
                if bool(row["needs_review"])
                else "✓"
            )

            with st.expander(
                f"{status_icon} "
                f"{row['indicator']} — "
                f"{row['Type de valeur']} — "
                f"{row['Valeur']}"
            ):
                st.markdown(
                    "**Phrase justificative**"
                )
                st.info(row["sentence"])

                col_left, col_right = st.columns(2)

                with col_left:
                    st.write(
                        f"**Pays :** {row['Pays']}"
                    )
                    st.write(
                        f"**Période :** {row['Période']}"
                    )
                    st.write(
                        f"**Source :** {row['Source']}"
                    )

                with col_right:
                    st.write(
                        f"**Référence :** {row['Référence']}"
                    )
                    st.write(
                        f"**Direction :** {row['Direction']}"
                    )
                    st.write(
                        f"**Confiance :** {row['Confiance']:.0f} %"
                    )

                if row.get("review_reason"):
                    st.warning(
                        f"Motif de vérification : "
                        f"{row['review_reason']}"
                    )

    st.divider()
    st.subheader(
        "Historique des analyses"
    )

    stored = fetch_business_facts()

    if stored:
        stored_df = prepare_dataframe(stored)
        st.dataframe(
            business_export(stored_df),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info(
            "Aucune analyse enregistrée."
        )
