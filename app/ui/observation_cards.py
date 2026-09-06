from __future__ import annotations

import html
import pandas as pd
import streamlit as st


def render_observation_cards(frame: pd.DataFrame, limit: int = 12) -> None:
    """Render a visual scan view alongside the dense analytical table."""
    if frame.empty:
        st.info("Aucune observation à afficher.")
        return
    cards = []
    for _, row in frame.head(limit).iterrows():
        status = str(row.get("Statut", "À vérifier"))
        status_class = {"Validé": "ok", "À vérifier": "review", "Rejeté": "bad"}.get(status, "review")
        value = html.escape(str(row.get("Valeur", "—")))
        unit = html.escape(str(row.get("Unité", "") or ""))
        cards.append(f'''<article class="event-card {status_class}">
          <div class="event-top"><span>{html.escape(str(row.get("Pays", "—")))}</span><i>{html.escape(status)}</i></div>
          <h4>{html.escape(str(row.get("Indicateur", "Indicateur non précisé")))}</h4>
          <div class="event-number">{value} <small>{unit}</small></div>
          <div class="event-meta"><b>{html.escape(str(row.get("Période", "—")))}</b><span>{html.escape(str(row.get("Type", "—")))}</span></div>
          <div class="event-source">{html.escape(str(row.get("Source", "Source non précisée")))}</div>
        </article>''')
    st.markdown(f'<div class="event-gallery">{"".join(cards)}</div>', unsafe_allow_html=True)
    if len(frame) > limit:
        st.caption(f"Aperçu des {limit} premières observations sur {len(frame)}. Le tableau conserve la vue exhaustive.")
