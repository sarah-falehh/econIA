from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from app.models.article_document import ArticleDocument
from app.services.auth_service import has_permission, log_action
from app.services.comparison_expander import expand_comparisons
from app.services.csv_reader import CSVReadError, dataframe_to_documents_auto, load_csv_dataframe
from app.services.database import create_analysis, detect_observation_conflicts, replace_business_facts, save_documents
from app.services.document_loader import create_manual_document
from app.services.multi_agent_pipeline import run_multi_agent, get_last_trace
from app.services.pdf_reader import PDFReadError, read_pdf
from app.views.extraction import business_export, prepare_dataframe
from app.services.series_analytics import build_indicator_series, indicator_statistics, all_series_export, statistics_export, to_excel_bytes, observations_export
from app.ui.geography import GEOGRAPHY_LABELS, geography_display
from app.ui.observation_cards import render_observation_cards


def _process_documents(documents: list[ArticleDocument]) -> list[dict]:
    save_documents(documents)
    all_facts: list[dict] = []
    status = st.status("Préparation de l’analyse…", expanded=True)
    live = st.empty()

    def update(message: str) -> None:
        status.write(message)

    def partial(rows: list[dict], batch_index: int, batch_count: int) -> None:
        live.info(f"Progression : lot {batch_index}/{batch_count} terminé · {len(rows)} ligne(s) validée(s). Les résultats déjà traités sont sauvegardés en cache.")

    for position, document in enumerate(documents, start=1):
        status.update(label=f"Document {position}/{len(documents)} · analyse en cours", state="running")
        payload = document.to_dict() if hasattr(document, "to_dict") else document.__dict__
        facts = run_multi_agent(
            payload,
            progress_callback=update,
            partial_callback=partial,
        )
        replace_business_facts(document.document_id, facts)
        analysis_id = create_analysis(
            document.document_id,
            getattr(document, "filename", None) or getattr(document, "title", None) or document.document_id,
            getattr(document, "input_type", None),
            facts,
        )
        st.session_state["current_analysis_id"] = analysis_id
        all_facts.extend(facts)

    detect_observation_conflicts()
    trace = get_last_trace()
    st.session_state["last_analysis_trace"] = trace
    elapsed = trace.get("elapsed_seconds")
    suffix = f" en {elapsed:.0f} s" if isinstance(elapsed, (int, float)) else ""
    live.empty()
    status.update(label=f"Analyse terminée{suffix}", state="complete", expanded=False)
    return all_facts


def _friendly_table(df: pd.DataFrame) -> pd.DataFrame:
    """Business-facing export generated from the canonical v4.7 schema.

    Do not reconstruct status from ``needs_review`` here: doing so collapses
    ``Rejeté`` into ``À vérifier`` and loses the observation type.
    """
    from app.services.series_analytics import auditable_observations_export
    clean = auditable_observations_export(df).copy()
    if "Pays" in clean:
        kinds = df.get("geography_type", pd.Series("country", index=df.index)).fillna("country")
        clean["Pays"] = [geography_display(name, kind) for name, kind in zip(clean["Pays"], kinds)]
    if "Type géographique" in clean:
        clean["Type géographique"] = clean["Type géographique"].map(GEOGRAPHY_LABELS).fillna(clean["Type géographique"])
    clean.insert(0, "N°", range(1, len(clean) + 1))
    clean = clean.rename(columns={"Phrase": "Phrase d’origine"})
    if "Valeur" in clean.columns:
        clean["Valeur"] = clean["Valeur"].map(
            lambda value: "—" if pd.isna(value) else format(float(value), ".12g")
        )
    return clean


def _is_emptyish_display(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip().lower() in {"", "none", "nan", "null", "<na>"}


def _prune_display_columns(frame: pd.DataFrame, force_drop: tuple[str, ...] = ("Source période", "Avertissements", "Page", "Tableau", "Ligne du tableau", "Colonne du tableau", "Secteur")) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    for column in force_drop:
        if column in out.columns:
            out = out.drop(columns=[column])
    empty_columns = [column for column in out.columns if out[column].map(_is_emptyish_display).all()]
    if empty_columns:
        out = out.drop(columns=empty_columns)
    return out


_STATUS_COLORS = {"Validé": "#16865C", "À vérifier": "#D97706", "Rejeté": "#C2413A"}
_TYPE_COLORS = {"Observé": "#667085", "Estimé": "#7C3AED", "Prévision": "#2457D6"}


def _style_business_table(frame: pd.DataFrame):
    """Color only business semantics; never encode confidence as validation."""
    styler = frame.style
    if "Statut" in frame.columns:
        styler = styler.map(
            lambda v: (
                f"color:{_STATUS_COLORS.get(str(v))};font-weight:850;"
                f"background-color:{_STATUS_COLORS.get(str(v))}16;"
                f"border-left:4px solid {_STATUS_COLORS.get(str(v))}"
            ) if str(v) in _STATUS_COLORS else "",
            subset=["Statut"],
        )
    if "Type" in frame.columns:
        styler = styler.map(
            lambda v: (
                f"color:{_TYPE_COLORS.get(str(v))};font-weight:700;"
                f"background-color:{_TYPE_COLORS.get(str(v))}10"
            ) if str(v) in _TYPE_COLORS else "",
            subset=["Type"],
        )
    return styler


def _indicator_series(df: pd.DataFrame, indicator: str) -> pd.DataFrame:
    return build_indicator_series(df, indicator)


def _fmt_metric(value, suffix="") -> str:
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):,.2f}".replace(",", " ") + suffix


def _render_indicator_tables(df: pd.DataFrame) -> None:
    dated = df[pd.to_numeric(df.get("current_year"), errors="coerce").notna()].copy()
    # Rejected events remain available in control views but must never create
    # a time-series selector entry or feed series/statistics/graphs.
    if "validation_status" in dated.columns:
        dated = dated[~dated["validation_status"].fillna("").isin(["Rejeté", "rejected"])].copy()
    elif "needs_review" in dated.columns and "rejected" in dated.columns:
        dated = dated[~dated["rejected"].fillna(False).astype(bool)].copy()
    if dated.empty:
        st.info("Aucune série annuelle complète n’a été détectée dans ce document.")
        return

    countries = sorted(dated["country"].dropna().unique().tolist()) if "country" in dated.columns else []
    selected_country = st.selectbox("Pays", countries) if len(countries) > 1 else (countries[0] if countries else None)
    scoped = dated[dated["country"] == selected_country].copy() if selected_country and "country" in dated.columns else dated
    indicators = sorted(scoped["indicator"].dropna().unique().tolist())
    selected = st.selectbox("Indicateur à visualiser", indicators)
    series = _indicator_series(scoped, selected)
    if series.empty:
        st.warning("Aucune valeur datée n’est disponible pour cet indicateur.")
        return

    stats = indicator_statistics(series)
    unit_text = series["current_unit"].dropna().astype(str).iloc[0] if series["current_unit"].notna().any() else ""
    scale_text = series["current_scale"].dropna().astype(str).iloc[0] if series["current_scale"].notna().any() else ""
    currency_text = series["current_currency"].dropna().astype(str).iloc[0] if series["current_currency"].notna().any() else ""
    unit_label = " ".join(x for x in [scale_text, currency_text, unit_text] if x).strip()

    st.markdown("### Synthèse statistique")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Observations", stats.get("observations", 0))
    c2.metric("Période", f"{stats.get('premiere_annee')} → {stats.get('derniere_annee')}")
    c3.metric("Évolution totale", _fmt_metric(stats.get("evolution_absolue")), _fmt_metric(stats.get("evolution_pct"), " %"))
    c4.metric("Croissance annuelle moyenne", _fmt_metric(stats.get("cagr_pct"), " %"))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Minimum", _fmt_metric(stats.get("minimum")), f"Année {stats.get('annee_minimum')}")
    c6.metric("Maximum", _fmt_metric(stats.get("maximum")), f"Année {stats.get('annee_maximum')}")
    c7.metric("Moyenne", _fmt_metric(stats.get("moyenne")))
    c8.metric("Médiane", _fmt_metric(stats.get("mediane")))

    display = series[["Année", "Valeur affichée", "Évolution absolue", "Évolution %", "Sens", "fact_type", "Source", "sentence"]].copy()
    display = display.rename(columns={"fact_type": "Nature", "sentence": "Phrase d’origine"})
    display["Évolution absolue"] = display["Évolution absolue"].round(3)
    display["Évolution %"] = display["Évolution %"].round(2)

    period_labels: list[str] = []
    for _, row in series.iterrows():
        year_value = int(row["Année"])
        quarter_value = row.get("current_quarter")
        month_value = row.get("current_month")
        if pd.notna(quarter_value) and quarter_value:
            period_labels.append(f"{year_value}-Q{int(quarter_value)}")
        elif pd.notna(month_value) and month_value:
            period_labels.append(f"{year_value}-M{int(month_value):02d}")
        else:
            period_labels.append(str(year_value))

    pivot_source = pd.DataFrame({
        "Pays": selected_country or (series["country"].dropna().iloc[0] if "country" in series.columns and series["country"].notna().any() else "—"),
        "Indicateur": selected,
        "Unité": unit_label or (series["current_unit"].dropna().astype(str).iloc[0] if "current_unit" in series.columns and series["current_unit"].notna().any() else ""),
        "Période": period_labels,
        "Valeur": series["Valeur affichée"].astype(str),
    })
    period_order = list(dict.fromkeys(pivot_source["Période"].tolist()))
    horizontal = (
        pivot_source.groupby(["Pays", "Indicateur", "Unité", "Période"], dropna=False)["Valeur"]
        .apply(lambda values: " | ".join(dict.fromkeys(values.astype(str))))
        .unstack("Période")
        .reset_index()
    )
    ordered_columns = [col for col in ["Pays", "Indicateur", "Unité"] if col in horizontal.columns] + [col for col in period_order if col in horizontal.columns]
    horizontal = horizontal.reindex(columns=ordered_columns)
    st.markdown("### Vue horizontale de la série")
    st.dataframe(horizontal, width="stretch", hide_index=True)

    with st.expander("Voir le détail période par période", expanded=False):
        st.dataframe(display, width="stretch", hide_index=True, column_config={
            "Évolution %": st.column_config.NumberColumn(format="%.2f %%"),
            "Phrase d’origine": st.column_config.TextColumn(width="large"),
        })

    fig = px.line(series, x="Année", y="Valeur numérique", markers=True, title=f"Évolution de {selected}" + (f" — {unit_label}" if unit_label else ""), labels={"Valeur numérique": selected})
    fig.update_layout(hovermode="x unified", margin=dict(l=10, r=10, t=55, b=10), font_color="#000000")
    fig.update_xaxes(tickfont=dict(color="#000000"), title_font=dict(color="#000000"), tickformat="d", dtick=1)
    fig.update_yaxes(tickfont=dict(color="#000000"), title_font=dict(color="#000000"))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Tous les indicateurs détectés")
    summary = statistics_export(scoped)
    if not summary.empty:
        st.dataframe(summary, width="stretch", hide_index=True)
    for indicator in indicators:
        indicator_series = _indicator_series(scoped, indicator)
        # A selector can legitimately point to no usable series after validation
        # filtering. Never let that business case crash the workspace.
        if indicator_series.empty:
            continue
        required = ["Année", "Valeur affichée", "Évolution absolue", "Évolution %", "Sens"]
        compact = indicator_series.reindex(columns=required).copy()
        with st.expander(f"{indicator} · {len(indicator_series)} point(s)"):
            compact["Évolution absolue"] = pd.to_numeric(compact["Évolution absolue"], errors="coerce").round(3)
            compact["Évolution %"] = pd.to_numeric(compact["Évolution %"], errors="coerce").round(2)
            st.dataframe(compact, width="stretch", hide_index=True)

    export_df = all_series_export(dated)
    if not export_df.empty:
        col_csv, col_xlsx = st.columns(2)
        col_csv.download_button("Télécharger toutes les séries (CSV)", export_df.to_csv(index=False).encode("utf-8-sig"), "series_economiques_par_indicateur.csv", "text/csv", use_container_width=True)
        col_xlsx.download_button("Télécharger le classeur d’analyse (Excel)", to_excel_bytes(dated), "analyse_series_economiques.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

def _result_block(facts: list[dict]) -> None:
    if not facts:
        st.warning("Aucune donnée économique exploitable n’a été validée.")
        try:
            from app.services.multi_agent_pipeline import get_last_trace
            trace = get_last_trace()
            with st.expander("Diagnostic de l’analyse", expanded=True):
                st.write({
                    "paragraphes détectés": trace.get("paragraphs_total", 0),
                    "passages envoyés à Qwen": len(trace.get("kept", [])),
                    "faits bruts proposés": len(trace.get("raw_facts", [])),
                    "faits rejetés par Python": len(trace.get("rejected_validation", [])),
                    "appels au LLM": trace.get("llm_calls", 0),
                    "durée totale (s)": trace.get("elapsed_seconds"),
                    "modèle": trace.get("model"),
                })
                if trace.get("pipeline_warning"):
                    st.warning(trace["pipeline_warning"])
                if trace.get("kept"):
                    st.caption("Exemples de passages transmis au modèle")
                    st.write(trace["kept"][:5])
                if trace.get("rejected_validation"):
                    st.caption("Exemples de résultats rejetés")
                    st.json(trace["rejected_validation"][:5])
        except Exception:
            pass
        return

    df = prepare_dataframe(facts)
    clean_df = _friendly_table(df)
    st.session_state["business_latest"] = facts

    st.markdown("## Analyse structurée")
    st.caption("Chaque ligne correspond à une information directement exploitable. Lorsqu’une phrase contient plusieurs comparaisons, elles apparaissent sur plusieurs lignes numérotées.")

    c1, c2, c3, c4 = st.columns(4)
    status_counts = clean_df["Statut"].value_counts() if "Statut" in clean_df else pd.Series(dtype=int)
    c1.metric("Observations", len(df), help="Événements économiques atomiques extraits")
    c2.metric("Indicateurs", int(df["indicator"].nunique()))
    c3.metric("Validées", int(status_counts.get("Validé", 0)), help="Observations dont les preuves sont suffisantes")
    c4.metric("À vérifier", int(status_counts.get("À vérifier", 0)), help="Observations nécessitant une revue humaine")
    rejected_count = int(status_counts.get("Rejeté", 0))
    if rejected_count:
        st.caption(f"{rejected_count} observation(s) rejetée(s) sont conservées pour audit mais exclues des séries et statistiques.")

    with st.expander("Comment lire le tableau ?", expanded=False):
        st.markdown("**Type** distingue Observé, Estimé et Prévision. **Confiance** est un score interne de qualité des preuves — ce n’est ni une accuracy ni un F1. **Statut** est la décision métier : Validé, À vérifier ou Rejeté.")

    filters = st.columns([1.1, 1.1, 1.1, 1.1, 1.5])
    indicators = sorted(clean_df["Indicateur"].dropna().unique().tolist())
    countries = sorted(clean_df["Pays"].dropna().unique().tolist())
    statuses = sorted(clean_df["Statut"].dropna().unique().tolist())
    types = sorted(clean_df["Type"].dropna().unique().tolist()) if "Type" in clean_df else []
    selected_indicators = filters[0].multiselect("Indicateur", indicators, placeholder="Tous")
    selected_countries = filters[1].multiselect("Pays", countries, placeholder="Tous")
    selected_statuses = filters[2].multiselect("Statut", statuses, placeholder="Tous")
    selected_types = filters[3].multiselect("Type", types, placeholder="Tous")
    search = filters[4].text_input("Rechercher dans les phrases", placeholder="inflation, exportations…")

    shown = clean_df.copy()
    if selected_indicators:
        shown = shown[shown["Indicateur"].isin(selected_indicators)]
    if selected_countries:
        shown = shown[shown["Pays"].isin(selected_countries)]
    if selected_statuses:
        shown = shown[shown["Statut"].isin(selected_statuses)]
    if selected_types:
        shown = shown[shown["Type"].isin(selected_types)]
    if search:
        shown = shown[shown["Phrase d’origine"].str.contains(search, case=False, na=False)]

    tab_details, tab_cards, tab_series = st.tabs(["▦ Tableau analytique", "◫ Cartes visuelles", "⌁ Évolution par indicateur"])
    with tab_details:
        st.dataframe(
            _style_business_table(_prune_display_columns(shown)),
            width="stretch",
            hide_index=True,
            height=min(650, 120 + 35 * len(shown)),
            column_config={
                "N°": st.column_config.NumberColumn(width="small"),
                "Confiance": st.column_config.ProgressColumn("Qualité", min_value=0, max_value=100, format="%.0f %%"),
                "Phrase d’origine": st.column_config.TextColumn("Phrase d’origine", width="large"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Statut": st.column_config.TextColumn("Statut", width="small"),
            },
        )

    with tab_cards:
        render_observation_cards(_prune_display_columns(shown), limit=18)

    with tab_series:
        st.caption("Vue synthétique : les périodes sont regroupées à l’horizontale pour faciliter la lecture, avec un détail disponible au besoin.")
        _render_indicator_tables(df)

    user = st.session_state.get("user")
    if has_permission(user, "export"):
        st.markdown("### Récupérer le résultat")
        col1, col2 = st.columns(2)
        col1.download_button("Télécharger le tableau prêt à l’emploi", _prune_display_columns(shown).to_csv(index=False).encode("utf-8-sig"), "tableau_economique.csv", "text/csv", use_container_width=True, type="primary")
        col2.download_button("Télécharger les données détaillées", df.to_csv(index=False).encode("utf-8-sig"), "donnees_techniques.csv", "text/csv", use_container_width=True)
    else:
        st.info("Votre accès permet de consulter le tableau, mais pas de le télécharger.")


def render_workspace() -> None:
    from app.ui.theme import hero, section_index
    hero("ANALYSE / PLATEFORME", "Déposez un rapport. Récupérez une intelligence exploitable.", "PDF, CSV ou texte : Econia transforme le contenu économique en événements atomiques, preuves, séries et signaux de contrôle.")
    st.markdown('''<div class="analysis-rail"><div><b>Document</b></div><i></i><div><b>Extraction</b></div><i></i><div><b>Validation humaine</b></div><i></i><div><b>Séries</b></div></div><div class="workspace-intro"><div class="workspace-note"><b>Deterministic first</b><br>Le moteur privilégie les preuves locales, le contexte contrôlé et l’ontologie économique.</div><div class="workspace-signal"><b>Reliability gate</b><br>Une association ambiguë reste à vérifier au lieu d’être inventée.</div></div>''', unsafe_allow_html=True)
    section_index("", "Choisir la source")

    if not has_permission(st.session_state.get("user"), "extract"):
        st.info("Votre profil Lecteur permet de consulter les résultats, sans lancer une nouvelle extraction.")
        if st.session_state.get("business_latest"):
            _result_block(st.session_state["business_latest"])
        return

    input_mode = st.segmented_control("Quel contenu souhaitez-vous analyser ?", ["Texte à copier", "Document PDF", "Fichier CSV"], default="Texte à copier")
    documents: list[ArticleDocument] = []
    ready = False

    with st.container(border=True):
        if input_mode == "Texte à copier":
            st.markdown("#### Collez votre article")
            text = st.text_area("Contenu", height=300, placeholder="Copiez ici le texte économique à transformer en tableau…", label_visibility="collapsed")
            with st.expander("Ajouter des informations sur le document (facultatif)"):
                col1, col2 = st.columns(2)
                title = col1.text_input("Titre")
                source = col2.text_input("Source")
                publication_date = st.text_input("Date de publication")
            if text.strip():
                try:
                    documents = [create_manual_document(text, title, source, publication_date)]
                    ready = True
                except ValueError:
                    pass
        elif input_mode == "Document PDF":
            st.markdown("#### Déposez votre PDF")
            uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
            if uploaded:
                try:
                    documents = read_pdf(uploaded)
                    ready = bool(documents)
                    if ready:
                        page_count = sum(getattr(doc, "page_count", 1) for doc in documents)
                        kept_count = sum(getattr(doc, "kept_page_count", getattr(doc, "page_count", 1)) for doc in documents)
                        st.success(f"Document reconnu · {page_count} page(s), {kept_count} page(s) narrative(s) prête(s)")
                except PDFReadError as exc:
                    st.error(str(exc))
        else:
            st.markdown("#### Déposez votre fichier CSV")
            uploaded = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")
            if uploaded:
                try:
                    dataframe = load_csv_dataframe(uploaded)
                    documents, schema = dataframe_to_documents_auto(dataframe, uploaded.name)
                    ready = bool(documents)
                    if ready:
                        st.success(f"{len(documents)} article(s) reconnus automatiquement")
                        with st.expander("Voir un aperçu du fichier"):
                            st.dataframe(dataframe.head(8), width="stretch", hide_index=True)
                except CSVReadError as exc:
                    st.error(str(exc))

    section_index("", "Contrôle du moteur")
    with st.expander("Voir le fonctionnement du moteur", expanded=False):
        st.success("Moteur événements & séries activé : extraction atomique, chronologies complètes, aucun LLM local et aucune API payante.")
        st.caption("Chaque valeur est rattachée à son indicateur et à sa période, puis regroupée automatiquement en séries annuelles avec calcul de l’évolution.")

    section_index("", "Lancer l’extraction")
    if ready:
        st.success("Source reconnue. Le document est prêt pour l’extraction.")
    analyze = st.button("Lancer l’analyse  →", type="primary", use_container_width=True, disabled=not ready)

    if analyze:
        try:
            with st.spinner("Analyse structurée et validation des données économiques…"):
                facts = _process_documents(documents)
            user = st.session_state.get("user", {})
            log_action(user.get("id"), user.get("email"), "complete_extraction", f"documents={len(documents)}; facts={len(facts)}")
            st.toast("Tableau créé avec succès", icon="✅")
            _result_block(facts)
        except Exception as exc:
            st.error(f"L’analyse n’a pas pu être terminée : {exc}")
    elif st.session_state.get("business_latest"):
        st.divider()
        _result_block(st.session_state["business_latest"])
