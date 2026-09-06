from __future__ import annotations

import pandas as pd
import streamlit as st

from app.services.auth_service import has_permission

from app.services.database import (
    fetch_annotations,
    fetch_business_facts,
    update_business_fact,
)
from app.services.indicator_catalog import INDICATOR_LABELS


VALUE_TYPES = {
    "level": "Niveau",
    "relative_change": "Variation relative",
    "absolute_change": "Variation absolue",
}

DIRECTIONS = {
    "unknown": "Non déterminable",
    "increase": "Hausse",
    "decrease": "Baisse",
    "stable": "Stable",
}


def optional_float(value):
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def optional_int(value):
    if value in (None, ""):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def render_validation_page() -> None:
    st.title(
        "Validation humaine"
    )

    st.caption(
        "Corrigez les extractions pour créer "
        "progressivement le dataset d'entraînement."
    )

    facts = fetch_business_facts(
        only_pending=True
    )

    if not facts:
        st.success(
            "Aucun fait en attente de validation."
        )
    else:
        labels = {
            index: (
                f"#{fact['id']} — "
                f"{fact.get('indicator') or 'Sans indicateur'} — "
                f"{fact.get('country') or 'Pays inconnu'}"
            )
            for index, fact in enumerate(facts)
        }

        selected_index = st.selectbox(
            "Fait à valider",
            options=list(labels),
            format_func=lambda index: labels[index],
        )

        fact = facts[selected_index]

        st.info(
            fact.get("sentence", "")
        )

        if fact.get("review_reason"):
            st.warning(
                fact["review_reason"]
            )

        indicator_codes = list(
            INDICATOR_LABELS.keys()
        )

        default_indicator_index = (
            indicator_codes.index(
                fact["indicator_code"]
            )
            if fact.get("indicator_code")
            in indicator_codes
            else 0
        )

        with st.form(
            f"validation_form_{fact['id']}"
        ):
            col1, col2 = st.columns(2)

            with col1:
                country = st.text_input(
                    "Pays",
                    value=fact.get("country") or "",
                )

                indicator_code = st.selectbox(
                    "Indicateur normalisé",
                    options=indicator_codes,
                    index=default_indicator_index,
                )

                value_type = st.selectbox(
                    "Type de valeur",
                    options=list(VALUE_TYPES),
                    index=list(VALUE_TYPES).index(
                        fact.get("value_type", "level")
                    ),
                    format_func=lambda value: (
                        VALUE_TYPES[value]
                    ),
                )

                current_value = st.text_input(
                    "Valeur actuelle",
                    value=(
                        ""
                        if fact.get("current_value") is None
                        else str(fact["current_value"])
                    ),
                )

                current_unit = st.text_input(
                    "Unité actuelle",
                    value=fact.get("current_unit") or "",
                )

                variation_value = st.text_input(
                    "Valeur de variation",
                    value=(
                        ""
                        if fact.get("variation_value") is None
                        else str(fact["variation_value"])
                    ),
                )

                variation_unit = st.text_input(
                    "Unité de variation",
                    value=fact.get("variation_unit") or "",
                )

            with col2:
                current_month = st.number_input(
                    "Mois actuel",
                    min_value=0,
                    max_value=12,
                    value=int(
                        fact.get("current_month") or 0
                    ),
                )

                current_quarter = st.number_input(
                    "Trimestre actuel",
                    min_value=0,
                    max_value=4,
                    value=int(
                        fact.get("current_quarter") or 0
                    ),
                )

                current_year = st.number_input(
                    "Année actuelle",
                    min_value=0,
                    max_value=2100,
                    value=int(
                        fact.get("current_year") or 0
                    ),
                )

                reference_value = st.text_input(
                    "Valeur de référence",
                    value=(
                        ""
                        if fact.get("reference_value") is None
                        else str(fact["reference_value"])
                    ),
                )

                reference_year = st.number_input(
                    "Année de référence",
                    min_value=0,
                    max_value=2100,
                    value=int(
                        fact.get("reference_year") or 0
                    ),
                )

                direction = st.selectbox(
                    "Direction",
                    options=list(DIRECTIONS),
                    index=list(DIRECTIONS).index(
                        fact.get("direction", "unknown")
                    ),
                    format_func=lambda value: (
                        DIRECTIONS[value]
                    ),
                )

                source = st.text_input(
                    "Source",
                    value=fact.get("source") or "",
                )

            validate_button = st.form_submit_button(
                "Valider et enregistrer",
                type="primary",
                width="stretch",
            )

            reject_button = st.form_submit_button(
                "Marquer comme rejeté",
                width="stretch",
            )

        if validate_button:
            language = fact.get("language", "fr")
            label_language = (
                language
                if language in ("fr", "en", "ar")
                else "fr"
            )

            updates = {
                "country": country or None,
                "indicator_code": indicator_code,
                "indicator": INDICATOR_LABELS[
                    indicator_code
                ][label_language],
                "value_type": value_type,
                "current_value": optional_float(
                    current_value
                ),
                "current_unit": current_unit or None,
                "variation_value": optional_float(
                    variation_value
                ),
                "variation_unit": variation_unit or None,
                "current_month": (
                    None
                    if current_month == 0
                    else int(current_month)
                ),
                "current_quarter": (
                    None
                    if current_quarter == 0
                    else int(current_quarter)
                ),
                "current_year": (
                    None
                    if current_year == 0
                    else int(current_year)
                ),
                "reference_value": optional_float(
                    reference_value
                ),
                "reference_year": (
                    None
                    if reference_year == 0
                    else int(reference_year)
                ),
                "direction": direction,
                "source": source or None,
            }

            update_business_fact(
                fact_id=int(fact["id"]),
                updates=updates,
                validation_status="validated",
            )

            st.success(
                "Correction enregistrée. "
                "Elle pourra servir au futur entraînement."
            )
            st.rerun()

        if reject_button:
            update_business_fact(
                fact_id=int(fact["id"]),
                updates={},
                validation_status="rejected",
            )

            st.success(
                "Le fait a été marqué comme rejeté."
            )
            st.rerun()

    st.divider()
    st.subheader(
        "Corrections enregistrées"
    )

    annotations = fetch_annotations()

    if annotations:
        st.dataframe(
            pd.DataFrame(annotations),
            width="stretch",
            hide_index=True,
        )

        if has_permission(st.session_state.get("user"), "export"):
            st.download_button(
                "Exporter le dataset de corrections",
            data=pd.DataFrame(
                annotations
            ).to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="dataset_corrections.csv",
            mime="text/csv",
            width="stretch",
        )
    else:
        st.info(
            "Aucune correction enregistrée pour le moment."
        )
