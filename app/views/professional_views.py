from __future__ import annotations

import json
from io import BytesIO
import re
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.services.auth_service import has_permission
from app.services.database import (canonical_series_observations, detect_observation_conflicts, fetch_analyses, fetch_observation_history, fetch_observations, update_observation)
from app.services.series_analytics import (
    build_indicator_series, indicator_statistics, observations_export,
    simple_series_export, simple_statistics_export,
)
from app.ui.theme import hero, metric_cards, intel_strip
from app.ui.branding import APP_NAME
from app.ui.geography import GEOGRAPHY_LABELS, geography_display
from app.ui.observation_cards import render_observation_cards
from app.views.extraction import prepare_dataframe

STATUS_COLORS = {"Validé": "#16865C", "À vérifier": "#D97706", "Rejeté": "#C2413A"}
TYPE_COLORS = {"Observé": "#667085", "Estimé": "#7C3AED", "Prévision": "#2457D6"}
TYPE_LABELS = {"observed": "Observé", "estimate": "Estimé", "forecast": "Prévision"}

def _geography_display(name, kind="country") -> str:
    return geography_display(name, kind)


def _format_number(value) -> str:
    """Human-readable number without meaningless trailing zeroes."""
    if value is None:
        return "—"
    try:
        if pd.isna(value):
            return "—"
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) < 5e-13:
        number = 0.0
    return format(number, ".12g")


def _geography_label(row: pd.Series) -> str:
    name = str(row.get("country") or row.get("geography") or "Géographie inconnue")
    kind = str(row.get("geography_type") or "country")
    return f"{_geography_display(name, kind)} · {GEOGRAPHY_LABELS.get(kind, kind.replace('_', ' ').title())}"


def _default_year_choice(group: pd.DataFrame):
    """Choose a safe default while leaving the final decision to the user."""
    ranked = group.copy()
    status_rank = _status(ranked).map({"Validé": 0, "À vérifier": 1, "Rejeté": 2}).fillna(3)
    type_rank = _type(ranked).map({"Observé": 0, "Estimé": 1, "Prévision": 2}).fillna(3)
    confidence = pd.to_numeric(
        ranked.get("confidence", pd.Series(0, index=ranked.index)), errors="coerce"
    ).fillna(0)
    ranked = ranked.assign(_status_rank=status_rank, _type_rank=type_rank, _confidence=-confidence)
    return ranked.sort_values(["_status_rank", "_type_rank", "_confidence"], kind="stable").index[0]


def _apply_year_choices(series: pd.DataFrame, choices: dict[int, object]) -> pd.DataFrame:
    """Return at most one point per year using explicit row-index choices."""
    if series.empty or "Année" not in series:
        return series.copy()
    selected = []
    for year, group in series.groupby("Année", sort=True, dropna=False):
        key = int(year) if pd.notna(year) else year
        chosen = choices.get(key, _default_year_choice(group))
        selected.append(chosen if chosen in group.index else _default_year_choice(group))
    return series.loc[selected].sort_values("Année", kind="stable").copy()


def _facts() -> list[dict]:
    """Global source of truth: all persisted observations, never the last session DataFrame."""
    try:
        return fetch_observations(limit=50000)
    except Exception:
        return []


def _series_facts() -> list[dict]:
    try:
        return canonical_series_observations()
    except Exception:
        return _facts()


def _df() -> pd.DataFrame:
    facts = _facts()
    return prepare_dataframe(facts) if facts else pd.DataFrame()


def _empty() -> bool:
    if _facts():
        return False
    st.markdown('<div class="empty-state"><b>Aucune analyse active</b><span>Lancez une nouvelle analyse pour construire votre espace d’intelligence économique.</span></div>', unsafe_allow_html=True)
    return True


def _status(df: pd.DataFrame) -> pd.Series:
    if "validation_status" in df.columns:
        raw = df["validation_status"].fillna("").replace({"pending":"À vérifier", "validated":"Validé", "rejected":"Rejeté", "Validable":"Validé"})
        fallback = df.get("needs_review", pd.Series(True, index=df.index)).fillna(True).astype(bool).map({False:"Validé", True:"À vérifier"})
        return raw.where(raw.isin(STATUS_COLORS), fallback)
    return df.get("needs_review", pd.Series(True, index=df.index)).fillna(True).astype(bool).map({False:"Validé", True:"À vérifier"})


def _type(df: pd.DataFrame) -> pd.Series:
    raw = df.get("observation_type", df.get("fact_type", pd.Series("observed", index=df.index))).fillna("observed")
    return raw.map(TYPE_LABELS).fillna(raw)


def _decode_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except Exception:
            return [x.strip() for x in value.split(";") if x.strip()]
    return []


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


def _display_observations(df: pd.DataFrame) -> pd.DataFrame:
    out = observations_export(df).rename(columns={"Phrase":"Phrase source"})
    if "Pays" in out:
        kinds = df.get("geography_type", pd.Series("country", index=df.index)).fillna("country")
        out["Pays"] = [_geography_display(name, kind) for name, kind in zip(out["Pays"], kinds)]
        if "Type géographique" not in out:
            out.insert(out.columns.get_loc("Pays") + 1, "Type géographique", kinds.map(GEOGRAPHY_LABELS).fillna(kinds).values)
    if "Type géographique" in out:
        out["Type géographique"] = out["Type géographique"].map(GEOGRAPHY_LABELS).fillna(out["Type géographique"])
    if "Valeur" in out:
        out["Valeur"] = out["Valeur"].map(_format_number)
    out["Conflit"] = df.get("conflict_status", pd.Series(False, index=df.index)).fillna(False).astype(bool).map({True:"CONFLIT", False:""}).values
    return out


def _style_status(value: str) -> str:
    color = STATUS_COLORS.get(str(value))
    return f"color:{color};font-weight:850;background-color:{color}16;border-left:4px solid {color}" if color else ""


def _style_type(value: str) -> str:
    color = TYPE_COLORS.get(str(value))
    return f"color:{color};font-weight:800;background-color:{color}0D" if color else ""


def _table_style(frame: pd.DataFrame):
    styler = frame.style
    if "Statut" in frame.columns:
        styler = styler.map(_style_status, subset=["Statut"])
    if "Type" in frame.columns:
        styler = styler.map(_style_type, subset=["Type"])
    if "Conflit" in frame.columns:
        styler = styler.map(lambda v: "color:#8B1E2D;font-weight:900;background:#FCE8EA" if v else "", subset=["Conflit"])
    return styler


def _status_badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#667085")
    return f'<span class="validation-badge" style="color:{color};border-color:{color}40;background:{color}12"><span style="background:{color}" class="validation-dot"></span>{status}</span>'


def _type_badge(kind: str) -> str:
    color = TYPE_COLORS.get(kind, "#667085")
    return f'<span class="type-badge" style="color:{color};border-color:{color}28;background:{color}0D">{kind}</span>'


def render_overview() -> None:
    hero("INTELLIGENCE DESK / LIVE", "Vue d’ensemble", "Un briefing opérationnel : ce qui a été extrait, ce qui mérite votre attention et ce que le document raconte réellement.")
    if _empty(): return
    df = _df(); statuses = _status(df)
    validated = int((statuses == "Validé").sum()); review = int((statuses == "À vérifier").sum()); rejected = int((statuses == "Rejeté").sum())
    metric_cards([
        ("Observations", str(len(df)), "événements atomiques"),
        ("Indicateurs", str(int(df["indicator"].nunique()) if "indicator" in df else 0), "concepts économiques"),
        ("Validées", str(validated), "prêtes à exploiter"),
        ("À examiner", str(review), "file de revue humaine"),
    ])
    st.markdown("### Morning brief")
    c1,c2=st.columns([1.55,1], gap="large")
    with c1:
        st.markdown(f'<div class="brief-panel"><span class="desk-label">SIGNAL PRIORITAIRE</span><h3>La revue humaine doit rester ciblée.</h3><p>{APP_NAME} sépare l’extraction de la décision métier : les observations ambiguës restent visibles sans polluer les séries validées.</p></div>', unsafe_allow_html=True)
        review_rows=_display_observations(df.loc[statuses.eq("À vérifier")]).drop(columns=["Phrase source"],errors="ignore").head(6)
        if not review_rows.empty:
            st.markdown("#### À examiner maintenant")
            st.dataframe(_table_style(review_rows), hide_index=True, width="stretch", column_config={"Confiance":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%d %%")})
        else: st.success("Aucune observation en attente de revue.")
    with c2:
        st.markdown('<div class="brief-panel dark"><span class="desk-label">ANALYSIS PULSE</span><h3>Qualité de l’analyse active</h3></div>', unsafe_allow_html=True)
        quality=pd.DataFrame({"Statut":["Validé","À vérifier","Rejeté"],"Observations":[validated,review,rejected]})
        fig=px.pie(quality,names="Statut",values="Observations",hole=.76,color="Statut",color_discrete_map=STATUS_COLORS)
        fig.update_layout(height=255,margin=dict(l=5,r=5,t=5,b=5),showlegend=True,paper_bgcolor="rgba(0,0,0,0)",font_color="#000000")
        st.plotly_chart(fig,width="stretch")
    _document_xray(df)

def render_observations() -> None:
    hero("Evidence-based extraction", "Observations", "Chaque chiffre reste relié à son type, son statut, sa phrase source et aux preuves qui justifient sa validation.")
    if _empty(): return
    df = _df().reset_index(drop=True); table = _display_observations(df).reset_index(drop=True)
    if "observation_id" in df.columns:
        table.insert(0, "ID", df["observation_id"].values)
    r1 = st.columns([1.05,1.25,1.05,1.0])
    countries = sorted(table["Pays"].dropna().astype(str).unique())
    inds = sorted(table["Indicateur"].dropna().astype(str).unique())
    types = sorted(table["Type"].dropna().astype(str).unique())
    statuses = [s for s in ["Validé","À vérifier","Rejeté"] if s in set(table["Statut"])]
    sc = r1[0].multiselect("Pays", countries, placeholder="Tous")
    si = r1[1].multiselect("Indicateur", inds, placeholder="Tous")
    stype = r1[2].multiselect("Type", types, placeholder="Tous")
    ss = r1[3].multiselect("Statut", statuses, placeholder="Tous")
    r2 = st.columns([1.6,1,1])
    q = r2[0].text_input("Recherche", placeholder="inflation, dette, 2024…")
    min_conf = r2[1].slider("Confiance minimale", 0, 100, 0, 5)
    conflicts_only = r2[2].toggle("Conflits uniquement", value=False)
    r3 = st.columns([1,1.2,1,1,1])
    analyses = sorted(df.get("analysis_id", pd.Series(dtype=str)).dropna().astype(str).unique())
    documents = sorted(df.get("source_name", df.get("document_id", pd.Series(dtype=str))).dropna().astype(str).unique())
    sectors = sorted(df.get("sector", pd.Series(dtype=str)).dropna().astype(str).unique())
    origins = sorted(df.get("validation_origin", pd.Series(dtype=str)).dropna().astype(str).unique())
    sa = r3[0].multiselect("Analyse", analyses, placeholder="Toutes")
    sd = r3[1].multiselect("Document", documents, placeholder="Tous")
    ssector = r3[2].multiselect("Secteur", sectors, placeholder="Tous")
    sorigin = r3[3].multiselect("Validation", origins, placeholder="Toutes")
    date_q = r3[4].text_input("Date", placeholder="2026-09")

    mask = pd.Series(True, index=table.index)
    if sc: mask &= table["Pays"].isin(sc)
    if si: mask &= table["Indicateur"].isin(si)
    if stype: mask &= table["Type"].isin(stype)
    if ss: mask &= table["Statut"].isin(ss)
    if sa: mask &= df.get("analysis_id", pd.Series("", index=df.index)).astype(str).isin(sa)
    if sd:
        doc_series = df.get("source_name", df.get("document_id", pd.Series("", index=df.index))).fillna("").astype(str)
        mask &= doc_series.isin(sd)
    if ssector: mask &= df.get("sector", pd.Series("", index=df.index)).fillna("").astype(str).isin(ssector)
    if sorigin: mask &= df.get("validation_origin", pd.Series("", index=df.index)).fillna("").astype(str).isin(sorigin)
    if date_q: mask &= df.get("created_at", pd.Series("", index=df.index)).fillna("").astype(str).str.contains(date_q, case=False, na=False)
    mask &= pd.to_numeric(table["Confiance"], errors="coerce").fillna(0) >= min_conf
    if conflicts_only: mask &= table["Conflit"].eq("CONFLIT")
    if q: mask &= table.astype(str).apply(lambda c: c.str.contains(q,case=False,na=False)).any(axis=1)
    shown = table.loc[mask].copy()

    compact = shown.drop(columns=["Phrase source"], errors="ignore")
    view_mode = st.segmented_control("Mode d’affichage", ["▦ Tableau analytique", "◫ Cartes visuelles"], default="▦ Tableau analytique", label_visibility="collapsed")
    if view_mode == "◫ Cartes visuelles":
        render_observation_cards(compact, limit=15)
    else:
        st.dataframe(_table_style(_prune_display_columns(compact)), hide_index=True, width="stretch", height=min(650,135+38*len(compact)), column_config={"Confiance":st.column_config.ProgressColumn(min_value=0,max_value=100,format="%d %%")})
    st.caption(f"{len(shown)} observation(s) affichée(s) sur {len(table)}.")

    st.markdown("### Détail & preuves")
    if shown.empty: return
    options = list(shown.index[:200])
    selected = st.selectbox("Observation", options, format_func=lambda i: f"{shown.loc[i,'Indicateur']} · {shown.loc[i,'Période']} · {shown.loc[i,'Valeur']}")
    row = shown.loc[selected]; raw = df.loc[selected]
    status = str(row["Statut"]); kind = str(row["Type"])
    st.markdown(f'''<div class="observation-detail"><div class="detail-kicker">OBSERVATION</div><h3>{row['Indicateur']}</h3><div class="detail-value">{row['Valeur']} <span>{row['Unité']}</span></div><div class="detail-meta">{row['Pays']} · {row['Période']}</div><div class="detail-badges">{_type_badge(kind)} {_status_badge(status)}</div></div>''', unsafe_allow_html=True)
    c1,c2 = st.columns([1.45,1])
    with c1:
        st.markdown("**Phrase source**")
        st.info(row.get("Phrase source") or "Phrase source indisponible")
        st.markdown("**Source**")
        st.write(row.get("Source") or "Non détectée")
    with c2:
        st.metric("Confiance", f"{int(row['Confiance'])} %")
        evidence = _decode_list(raw.get("confidence_evidence"))
        warnings = _decode_list(raw.get("confidence_warnings"))
        if evidence:
            st.markdown("**Pourquoi ce score ?**")
            for item in evidence: st.markdown(f"<div class='evidence-ok'>✓ {item}</div>", unsafe_allow_html=True)
        if warnings:
            st.markdown("**Points de vigilance**")
            for item in warnings: st.markdown(f"<div class='evidence-warning'>! {item}</div>", unsafe_allow_html=True)
        if bool(raw.get("conflict_status")):
            st.error("CONFLIT — plusieurs valeurs existent pour cette série et cette période.")
    st.caption("La confiance mesure la qualité des preuves d’extraction. Ce n’est pas une probabilité de vérité ni une métrique de benchmark.")



def _review_indices(df: pd.DataFrame) -> list[int]:
    # Retained for compatibility with older tests/callers; the editor now exposes all observations.
    return list(df.index)


def _review_decisions() -> dict:
    return st.session_state.setdefault("review_decisions", {})


def _norm_text(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value)


def _norm_number(value):
    if value in (None, ""):
        return None
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except Exception:
        return value


def render_review_desk() -> None:
    hero("Human-in-the-loop control", "Validation humaine", "Consultez et corrigez toute observation persistée. Chaque modification est historisée et répercutée dans les analyses globales.")
    if _empty(): return
    detect_observation_conflicts()
    rows = fetch_observations(limit=50000)
    if not rows:
        st.info("Aucune observation persistée.")
        return
    df = pd.DataFrame(rows).reset_index(drop=True)
    table = _display_observations(prepare_dataframe(rows)).reset_index(drop=True)
    table.insert(0, "ID", df.get("observation_id", pd.Series([f"OBS-{i+1:06d}" for i in range(len(df))])))

    filters = st.columns([1.4, 1, 1.2, 1, 1.2])
    query = filters[0].text_input("Recherche", placeholder="ID, phrase, valeur…")
    countries = sorted(table.get("Pays", pd.Series(dtype=str)).dropna().astype(str).unique())
    indicators = sorted(table.get("Indicateur", pd.Series(dtype=str)).dropna().astype(str).unique())
    statuses = sorted(table.get("Statut", pd.Series(dtype=str)).dropna().astype(str).unique())
    sources = sorted(table.get("Source", pd.Series(dtype=str)).dropna().astype(str).unique())
    fc = filters[1].multiselect("Pays", countries)
    fi = filters[2].multiselect("Indicateur", indicators)
    fs = filters[3].multiselect("Statut", statuses)
    fsrc = filters[4].multiselect("Source", sources)

    mask = pd.Series(True, index=table.index)
    if fc: mask &= table["Pays"].isin(fc)
    if fi: mask &= table["Indicateur"].isin(fi)
    if fs: mask &= table["Statut"].isin(fs)
    if fsrc: mask &= table["Source"].isin(fsrc)
    if query:
        mask &= table.astype(str).apply(lambda c: c.str.contains(query, case=False, na=False)).any(axis=1)
    shown = table.loc[mask].copy()
    st.dataframe(_table_style(_prune_display_columns(shown.drop(columns=["Phrase source"], errors="ignore"))), hide_index=True, width="stretch", height=min(520, 150 + 34 * len(shown)))
    st.caption(f"{len(shown)} observation(s) affichée(s) sur {len(table)}.")
    if shown.empty: return

    options = list(shown.index)
    selected = st.selectbox(
        "Observation sélectionnée",
        options,
        format_func=lambda i: f"{table.loc[i, 'ID']} · {table.loc[i, 'Pays']} · {table.loc[i, 'Indicateur']} · {table.loc[i, 'Période']}",
    )
    raw = df.loc[selected].to_dict()
    observation_id = raw.get("observation_id")
    st.markdown(f"### {observation_id}")
    st.markdown("**Preuve originale**")
    st.info(raw.get("original_evidence") or raw.get("sentence") or "Preuve indisponible")
    if raw.get("conflict_status"):
        st.error("Conflit détecté : au moins une autre observation de la même série/période porte une valeur différente.")

    # Common business fields are explicit; remaining payload fields are also editable below.
    with st.form(f"edit_{observation_id}"):
        c1, c2, c3 = st.columns(3)
        updates = {}
        updates["geography"] = c1.text_input("Géographie", value=_norm_text(raw.get("geography")))
        updates["country"] = c2.text_input("Pays", value=_norm_text(raw.get("country")))
        updates["geography_type"] = c3.text_input("Type de géographie", value=_norm_text(raw.get("geography_type")))
        c1, c2, c3 = st.columns(3)
        updates["indicator"] = c1.text_input("Indicateur", value=_norm_text(raw.get("indicator")))
        updates["current_value"] = c2.text_input("Valeur", value=_norm_text(raw.get("current_value")))
        updates["current_unit"] = c3.text_input("Unité", value=_norm_text(raw.get("current_unit")))
        c1, c2, c3 = st.columns(3)
        updates["current_currency"] = c1.text_input("Devise", value=_norm_text(raw.get("current_currency")))
        updates["current_scale"] = c2.text_input("Échelle", value=_norm_text(raw.get("current_scale")))
        updates["period_label"] = c3.text_input("Période", value=_norm_text(raw.get("period_label")))
        c1, c2, c3 = st.columns(3)
        updates["period_type"] = c1.text_input("period_type", value=_norm_text(raw.get("period_type")))
        updates["period_start"] = c2.text_input("period_start", value=_norm_text(raw.get("period_start")))
        updates["period_end"] = c3.text_input("period_end", value=_norm_text(raw.get("period_end")))
        c1, c2, c3 = st.columns(3)
        updates["current_year"] = c1.text_input("Année", value=_norm_text(raw.get("current_year")))
        updates["current_quarter"] = c2.text_input("Trimestre", value=_norm_text(raw.get("current_quarter")))
        updates["current_month"] = c3.text_input("Mois", value=_norm_text(raw.get("current_month")))
        c1, c2, c3 = st.columns(3)
        updates["frequency"] = c1.text_input("Fréquence", value=_norm_text(raw.get("frequency")))
        updates["reference_period"] = c2.text_input("reference_period", value=_norm_text(raw.get("reference_period")))
        updates["sector"] = c3.text_input("Secteur", value=_norm_text(raw.get("sector")))
        c1, c2, c3 = st.columns(3)
        updates["subsector"] = c1.text_input("Sous-secteur", value=_norm_text(raw.get("subsector")))
        updates["product_category"] = c2.text_input("Catégorie produit", value=_norm_text(raw.get("product_category")))
        updates["partner_country"] = c3.text_input("Partenaire", value=_norm_text(raw.get("partner_country")))
        c1, c2, c3 = st.columns(3)
        updates["exchange_rate_counterpart"] = c1.text_input("Contrepartie de change", value=_norm_text(raw.get("exchange_rate_counterpart")))
        updates["methodology"] = c2.text_input("Méthodologie", value=_norm_text(raw.get("methodology")))
        updates["scenario"] = c3.text_input("Scénario", value=_norm_text(raw.get("scenario")))
        c1, c2, c3 = st.columns(3)
        updates["revision_version"] = c1.text_input("Version / révision", value=_norm_text(raw.get("revision_version")))
        type_values = ["observed", "estimate", "forecast"]
        current_type = raw.get("observation_type") or raw.get("fact_type") or "observed"
        updates["observation_type"] = c2.selectbox("Type", type_values, index=type_values.index(current_type) if current_type in type_values else 0, format_func=lambda x: TYPE_LABELS.get(x, x))
        status_values = ["Validé", "À vérifier", "Rejeté"]
        current_status = str(_status(pd.DataFrame([raw])).iloc[0])
        updates["validation_status"] = c3.selectbox("Statut", status_values, index=status_values.index(current_status) if current_status in status_values else 1)
        c1, c2 = st.columns(2)
        conf = raw.get("confidence")
        conf_pct = float(conf or 0) * 100 if float(conf or 0) <= 1 else float(conf or 0)
        confidence_pct = c1.number_input("Confiance (%)", min_value=0.0, max_value=100.0, value=min(100.0, max(0.0, conf_pct)), step=1.0)
        updates["source"] = c2.text_input("Source", value=_norm_text(raw.get("source")))
        updates["sentence"] = st.text_area("Preuve / phrase structurée", value=_norm_text(raw.get("sentence")), height=100)
        updates["validation_warnings"] = st.text_area("Avertissements", value="; ".join(_decode_list(raw.get("validation_warnings") or raw.get("confidence_warnings"))))
        reason = st.text_area("Commentaire de validation humaine", value=_norm_text(raw.get("human_comment")), placeholder="Motif de la correction ou décision")

        # Expose every other business payload column without duplicating immutable/system metadata.
        excluded = set(updates) | {"id", "observation_id", "analysis_id", "created_at", "updated_at", "source_name", "source_type", "validation_origin", "human_validated", "original_evidence"}
        extras = [k for k in raw.keys() if k not in excluded]
        if extras:
            with st.expander("Autres colonnes métier"):
                for field in extras:
                    value = raw.get(field)
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    updates[field] = st.text_input(field, value=_norm_text(value), key=f"extra_{observation_id}_{field}")
        save = st.form_submit_button("Enregistrer les modifications", type="primary", use_container_width=True)

    if save:
        for numeric_field in ["current_value", "current_year", "current_quarter", "current_month", "reference_value", "reference_year", "reference_quarter", "reference_month", "variation_value", "absolute_change", "relative_change"]:
            if numeric_field in updates:
                updates[numeric_field] = _norm_number(updates[numeric_field])
        updates["confidence"] = confidence_pct / 100.0
        # Keep warning storage compatible with the existing JSON-aware UI.
        if isinstance(updates.get("validation_warnings"), str):
            updates["validation_warnings"] = [x.strip() for x in updates["validation_warnings"].split(";") if x.strip()]
        update_observation(observation_id, updates, st.session_state.get("user"), reason)
        detect_observation_conflicts()
        st.session_state.pop("business_latest", None)
        st.success("Observation mise à jour avec succès.")
        st.rerun()

    history = fetch_observation_history(observation_id=observation_id)
    if history:
        with st.expander("Historique des corrections humaines"):
            st.dataframe(pd.DataFrame(history), hide_index=True, width="stretch")

def _document_xray(df: pd.DataFrame) -> None:
    statuses=_status(df); kinds=_type(df)
    trace=st.session_state.get("last_analysis_trace", {}) or {}
    conflicts=int(df.get("conflict_status", pd.Series(False,index=df.index)).fillna(False).astype(bool).sum())
    countries=int(df.get("country", pd.Series(dtype=object)).dropna().nunique())
    periods=int(df.get("period_label", df.get("current_year", pd.Series(dtype=object))).dropna().nunique())
    forecast=int(kinds.eq("Prévision").sum())
    st.markdown(f'<div class="xray-head"><span>DOCUMENT X-RAY</span><b>Ce que {APP_NAME} a réellement retenu</b></div>', unsafe_allow_html=True)
    intel_strip([("Paragraphes", trace.get("paragraphs_total","—")), ("Pays",countries), ("Périodes",periods), ("Prévisions",forecast), ("Conflits",conflicts)])
    total=max(1,len(df)); val=int(statuses.eq("Validé").sum()); rev=int(statuses.eq("À vérifier").sum()); rej=int(statuses.eq("Rejeté").sum())
    st.markdown(f'''<div class="xray-spectrum"><div class="xr-valid" style="width:{100*val/total:.2f}%"></div><div class="xr-review" style="width:{100*rev/total:.2f}%"></div><div class="xr-reject" style="width:{100*rej/total:.2f}%"></div></div><div class="xray-legend"><span>Validé {val}</span><span>À vérifier {rev}</span><span>Rejeté {rej}</span></div>''', unsafe_allow_html=True)

def _safe_filename(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "serie")).strip("_")
    return text[:80] or "serie"


def _period_label(frame: pd.DataFrame) -> pd.Series:
    if "period_label" in frame.columns:
        p = frame["period_label"].fillna("").astype(str)
    else:
        p = pd.Series("", index=frame.index)
    year = pd.to_numeric(frame.get("current_year"), errors="coerce")
    q = pd.to_numeric(frame.get("current_quarter"), errors="coerce")
    m = pd.to_numeric(frame.get("current_month"), errors="coerce")
    out=[]
    for idx in frame.index:
        if p.loc[idx].strip(): out.append(p.loc[idx].strip()); continue
        y = year.loc[idx] if idx in year.index else None
        if pd.isna(y): out.append("—"); continue
        yy=int(y); qq=q.loc[idx] if idx in q.index else None; mm=m.loc[idx] if idx in m.index else None
        out.append(f"{yy}-Q{int(qq)}" if pd.notna(qq) else f"{yy}-M{int(mm):02d}" if pd.notna(mm) else str(yy))
    return pd.Series(out,index=frame.index)


def _series_business_table(series: pd.DataFrame) -> pd.DataFrame:
    out=pd.DataFrame(index=series.index)
    names = series.get("country", pd.Series("", index=series.index))
    kinds = series.get("geography_type", pd.Series("country", index=series.index)).fillna("country")
    out["Pays"]=[geography_display(name, kind) for name, kind in zip(names, kinds)]
    out["Indicateur"]=series.get("indicator")
    out["Période"]=_period_label(series)
    out["Valeur"]=pd.to_numeric(series.get("current_value"),errors="coerce").map(_format_number)
    unit=series.get("current_unit",pd.Series("",index=series.index)).fillna("").astype(str)
    scale=series.get("current_scale",pd.Series("",index=series.index)).fillna("").astype(str)
    curr=series.get("current_currency",pd.Series("",index=series.index)).fillna("").astype(str)
    out["Unité"]=[" ".join(x for x in (s,u,c) if x and x.lower() not in {"nan","none"}).strip() for s,u,c in zip(scale,unit,curr)]
    out["Type"]=_type(series).values
    out["Statut"]=_status(series).values
    out["Confiance"]=pd.to_numeric(series.get("confidence"),errors="coerce")
    out["Source"]=series.get("source")
    return out.reset_index(drop=True)


def _series_horizontal_table(series: pd.DataFrame) -> pd.DataFrame:
    table = _series_business_table(series)
    if table.empty:
        return table
    period_order = list(dict.fromkeys(table["Période"].astype(str).tolist()))
    pivot = (
        table.groupby(["Pays", "Indicateur", "Unité", "Période"], dropna=False)["Valeur"]
        .apply(lambda values: " | ".join(dict.fromkeys(values.astype(str))))
        .unstack("Période")
        .reset_index()
    )
    ordered_columns = [c for c in ["Pays", "Indicateur", "Unité"] if c in pivot.columns] + [c for c in period_order if c in pivot.columns]
    return pivot.reindex(columns=ordered_columns)


def _series_excel_bytes(table: pd.DataFrame, stats: dict, country: str, indicator: str) -> bytes:
    bio=BytesIO()
    summary=pd.DataFrame([
        ["Pays",country],["Indicateur",indicator],["Observations",len(table)],
        ["Première période",stats.get("premiere_annee","—")],["Dernière période",stats.get("derniere_annee","—")],
        ["Minimum",stats.get("minimum","—")],["Maximum",stats.get("maximum","—")],
        ["Évolution absolue",stats.get("evolution_absolue",stats.get("variation_absolue","—"))],
        ["Évolution %",stats.get("evolution_pct",stats.get("variation_pct","—"))],
    ],columns=["Mesure","Valeur"])
    with pd.ExcelWriter(bio,engine="openpyxl") as writer:
        table.to_excel(writer,index=False,sheet_name="Série")
        summary.to_excel(writer,index=False,sheet_name="Synthèse")
        for ws in writer.book.worksheets:
            ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
            for col in ws.columns:
                vals=[len(str(c.value or "")) for c in col]
                ws.column_dimensions[col[0].column_letter].width=min(45,max(12,max(vals,default=10)+2))
    return bio.getvalue()


def render_series() -> None:
    hero("Time-series intelligence", "Séries temporelles", "Explorez une série issue de toutes les analyses persistées, avec déduplication des points identiques.")
    if _empty(): return
    facts=_series_facts(); df=prepare_dataframe(facts) if facts else pd.DataFrame(); dated=df[pd.to_numeric(df.get("current_year"),errors="coerce").notna()].copy()
    dated=dated[_status(dated)!="Rejeté"]
    if dated.empty: st.info("Aucune observation datée détectée."); return
    countries=sorted(dated["country"].dropna().unique()) if "country" in dated else []
    c1,c2=st.columns(2); country=c1.selectbox("Pays",countries,key="series_country") if countries else None
    scoped=dated[dated["country"]==country] if country else dated
    indicators=sorted(scoped["indicator"].dropna().unique()); indicator=c2.selectbox("Indicateur",indicators,key="series_indicator")
    series=build_indicator_series(scoped,indicator)
    if series.empty: st.info("Aucune série exploitable pour cette sélection."); return
    series["Type"]=_type(series).values; series["Statut"]=_status(series).values
    duplicate_years = [int(year) for year, group in series.groupby("Année") if len(group) > 1]
    year_choices: dict[int, object] = {}
    choice_specs = []
    for year in duplicate_years:
        candidates = series[series["Année"] == year]
        labels_to_rows = {}
        for position, (row_index, row) in enumerate(candidates.iterrows(), start=1):
            label = f"{_format_number(row['Valeur numérique'])} {row.get('Unité') or ''}".strip()
            if label in labels_to_rows:
                label = f"{label} · option {position}"
            labels_to_rows[label] = row_index
        default_row = _default_year_choice(candidates)
        default_label = next(label for label, idx in labels_to_rows.items() if idx == default_row)
        widget_key = f"series_final_value_{country}_{indicator}_{year}"
        selected_label = st.session_state.get(widget_key, default_label)
        if selected_label not in labels_to_rows:
            selected_label = default_label
        year_choices[year] = labels_to_rows[selected_label]
        choice_specs.append((year, labels_to_rows, default_label, widget_key))
    series = _apply_year_choices(series, year_choices)
    hist=series[series["Type"]!="Prévision"].copy(); fc=series[series["Type"]=="Prévision"].copy()
    observed=series[(series["Type"]=="Observé")&(series["Statut"]!="Rejeté")].copy()
    stats=indicator_statistics(observed) if not observed.empty else {}
    latest=observed.sort_values("Année").tail(1)
    latest_txt=_format_number(latest['Valeur numérique'].iloc[0]) if not latest.empty else "—"
    review_n=int((series["Statut"]=="À vérifier").sum())
    metric_cards([("Points",str(len(series)),"série sélectionnée"),("Dernière valeur",latest_txt,"historique observé"),("À vérifier",str(review_n),"contrôle humain"),("Prévisions",str(int((series['Type']=='Prévision').sum())),"distinguées de l’historique")])
    chart_slot = st.empty()
    if choice_specs:
        with st.container(border=True):
            st.markdown("#### Valeur finale affichée dans le graphe")
            st.caption("Choisissez le point à conserver lorsqu’une année contient plusieurs valeurs.")
            controls = st.columns(min(3, len(choice_specs)))
            for position, (year, labels_to_rows, default_label, widget_key) in enumerate(choice_specs):
                with controls[position % len(controls)]:
                    selected_label = st.segmented_control(
                        str(year), list(labels_to_rows), default=default_label, key=widget_key,
                    )
                    if selected_label in labels_to_rows:
                        year_choices[year] = labels_to_rows[selected_label]
        series = _apply_year_choices(series, year_choices)
        hist=series[series["Type"]!="Prévision"].copy(); fc=series[series["Type"]=="Prévision"].copy()
    fig=go.Figure()
    if not hist.empty: fig.add_trace(go.Scatter(x=hist["Année"],y=hist["Valeur numérique"],mode="lines+markers",name="Historique / estimation",line=dict(color="#2563EB",width=4,shape="spline",smoothing=.65),marker=dict(size=10,color="#FFFFFF",line=dict(color="#2563EB",width=3)),fill="tozeroy",fillcolor="rgba(37,99,235,.07)",hovertemplate="<b>%{x}</b><br>%{y:,.4g}<extra>Historique</extra>"))
    if not fc.empty:
        bridge=pd.concat([hist.tail(1),fc]).drop_duplicates(subset=["Année","Valeur numérique"])
        fig.add_trace(go.Scatter(x=bridge["Année"],y=bridge["Valeur numérique"],mode="lines+markers",name="Prévision",line=dict(color="#7C3AED",width=4,dash="dot",shape="spline",smoothing=.65),marker=dict(size=10,color="#FFFFFF",line=dict(color="#7C3AED",width=3)),hovertemplate="<b>%{x}</b><br>%{y:,.4g}<extra>Prévision</extra>"))
    review=series[series["Statut"]=="À vérifier"]
    if not review.empty: fig.add_trace(go.Scatter(x=review["Année"],y=review["Valeur numérique"],mode="markers",name="À vérifier",marker=dict(size=15,symbol="circle-open",color="#D97706",line=dict(width=3))))
    fig.update_layout(height=500,hovermode="x unified",title=dict(text=f"{country or ''} · {indicator}"),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig.update_xaxes(tickfont=dict(color="#000000",size=14), title_font=dict(color="#000000",size=15), tickformat="d", dtick=1)
    fig.update_yaxes(tickfont=dict(color="#000000",size=14), title_font=dict(color="#000000",size=15))
    chart_slot.plotly_chart(fig,width="stretch")
    table=_series_business_table(series)
    horizontal=_series_horizontal_table(series)
    st.markdown("### Vue horizontale de la série")
    st.dataframe(horizontal,hide_index=True,width="stretch")
    with st.expander("Voir le détail période par période", expanded=False):
        st.dataframe(_table_style(_prune_display_columns(table)),hide_index=True,width="stretch")
    if has_permission(st.session_state.get("user"),"export"):
        st.markdown("### Exporter cette série")
        x1,x2=st.columns(2); stem=f"{_safe_filename(country)}_{_safe_filename(indicator)}"
        x1.download_button("Télécharger la série en CSV",horizontal.to_csv(index=False).encode("utf-8-sig"),f"{stem}.csv","text/csv",use_container_width=True)
        x2.download_button("Télécharger le classeur Excel",_series_excel_bytes(table,stats,country or "",indicator),f"{stem}.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True)
        st.caption("Le CSV reprend la vue horizontale affichée. Le classeur Excel conserve le détail de la série et la synthèse statistique.")


def render_visualizations() -> None:
    hero("Visual analytics", "Visualisations", "Structure du document, types d’observations et validation — sans transformer le dashboard en décoration.")
    if _empty(): return
    facts=_series_facts(); df=prepare_dataframe(facts) if facts else pd.DataFrame(); left,right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("### Observations par indicateur")
            counts=df["indicator"].value_counts().head(12).rename_axis("Indicateur").reset_index(name="Observations")
            fig=px.bar(counts,x="Observations",y="Indicateur",orientation="h",color_discrete_sequence=["#2457D6"])
            fig.update_layout(height=410,margin=dict(l=5,r=5,t=10,b=5),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#000000")
            st.plotly_chart(fig,width="stretch")
    with right:
        with st.container(border=True):
            st.markdown("### Observé · Estimé · Prévision")
            nature=_type(df).value_counts().rename_axis("Type").reset_index(name="Observations")
            fig=px.pie(nature,names="Type",values="Observations",hole=.62,color="Type",color_discrete_map=TYPE_COLORS)
            fig.update_layout(height=410,margin=dict(l=5,r=5,t=10,b=5),paper_bgcolor="rgba(0,0,0,0)",font_color="#000000")
            st.plotly_chart(fig,width="stretch")


def render_statistics() -> None:
    hero("Historical statistics", "Statistiques", "Les statistiques descriptives utilisent par défaut les observations historiques réalisées ; les prévisions sont exclues.")
    if _empty(): return
    facts=_series_facts(); df=prepare_dataframe(facts) if facts else pd.DataFrame(); stats=simple_statistics_export(df)
    if stats.empty: st.info("Pas assez d’observations historiques datées pour calculer les statistiques."); return
    st.dataframe(stats,hide_index=True,width="stretch")
    st.caption("Les prévisions et les observations rejetées ne sont pas mélangées aux statistiques historiques.")


def render_sources() -> None:
    hero("Traceability", "Sources", "Historique complet des documents et analyses persistés, avec le nombre d’observations associées.")
    analyses = fetch_analyses(limit=5000)
    if not analyses:
        st.info("Aucune analyse enregistrée."); return
    table = pd.DataFrame(analyses).rename(columns={
        "analysis_id":"Analyse", "source_id":"Source ID", "source_name":"Document",
        "source_type":"Type", "created_at":"Date d’import", "number_of_events":"Observations"
    })
    st.dataframe(table[[c for c in ["Analyse","Document","Type","Date d’import","Observations","Source ID"] if c in table.columns]], hide_index=True, width="stretch")
    df=_df()
    if not df.empty:
        with st.container(border=True):
            st.markdown("### Répartition des statuts")
            summary = pd.DataFrame({"Analyse": df.get("analysis_id"), "Statut": _status(df)}).groupby(["Analyse","Statut"]).size().unstack(fill_value=0).reset_index()
            st.dataframe(summary, hide_index=True, width="stretch")


def render_compare() -> None:
    hero("Comparative analysis", "Comparer", "Comparez jusqu’à trois géographies — pays, régions ou groupes économiques — pour un indicateur, ou plusieurs indicateurs pour une même géographie.")
    if _empty(): return
    facts=_series_facts(); df=prepare_dataframe(facts) if facts else pd.DataFrame(); all_geo=df[_status(df)!="Rejeté"].copy(); all_geo["geography_label"] = all_geo.apply(_geography_label, axis=1); dated=all_geo[pd.to_numeric(all_geo.get("current_year"),errors="coerce").notna()].copy()
    dated["geography_label"] = dated.apply(_geography_label, axis=1)
    mode=st.radio("Mode de comparaison",["Même indicateur · plusieurs géographies","Même géographie · plusieurs indicateurs"],horizontal=True)
    if mode.startswith("Même indicateur"):
        # Indicator first: a previously selected country must never hide groups from the selector.
        indicators = sorted(dated["indicator"].dropna().unique())
        if not indicators:
            st.info("Aucun indicateur daté n’est disponible pour la comparaison."); return
        indicator=st.selectbox("Indicateur",indicators,key="compare_indicator_v590")
        pool=dated[dated["indicator"]==indicator]
        # The catalogue is global: PECO, Asian competitors and other groups stay visible
        # even when the current indicator has no point for them.
        geographies=sorted(all_geo["geography_label"].dropna().unique())
        chosen=st.multiselect("Pays, régions et groupes économiques",geographies,default=geographies[:min(3,len(geographies))],max_selections=3,key="compare_geographies_v590")
        plot=pool[pool["geography_label"].isin(chosen)].copy(); legend="geography_label"
    else:
        geographies=sorted(dated["geography_label"].dropna().unique()); country=st.selectbox("Géographie",geographies)
        pool=dated[dated["geography_label"]==country]; inds=sorted(pool["indicator"].dropna().unique()); chosen=st.multiselect("Indicateurs",inds,default=inds[:min(3,len(inds))],max_selections=3)
        plot=pool[pool["indicator"].isin(chosen)].copy(); legend="indicator"
    if plot.empty: st.info("Sélectionnez au moins une série."); return
    plot["Année"]=pd.to_numeric(plot["current_year"],errors="coerce"); plot["Valeur"]=pd.to_numeric(plot["current_value"],errors="coerce")
    fig=px.line(plot,x="Année",y="Valeur",color=legend,markers=True,template="econia")
    fig.update_traces(line=dict(width=4,shape="spline",smoothing=.6),marker=dict(size=9,line=dict(width=2,color="#FFFFFF")),hovertemplate="<b>%{x}</b><br>%{y:,.4g}<extra>%{fullData.name}</extra>")
    fig.update_layout(height=510,hovermode="x unified",legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    fig.update_xaxes(tickfont=dict(color="#000000",size=14),title_font=dict(color="#000000",size=15),tickformat="d",dtick=1)
    fig.update_yaxes(tickfont=dict(color="#000000",size=14),title_font=dict(color="#000000",size=15))
    st.plotly_chart(fig,width="stretch")
    geography_types = plot.get("geography_type", pd.Series("country", index=plot.index)).fillna("country")
    export=pd.DataFrame({"Géographie":[geography_display(n, k) for n, k in zip(plot.get("country"), geography_types)],"Type géographique":geography_types.map(GEOGRAPHY_LABELS).fillna(geography_types),"Indicateur":plot.get("indicator"),"Période":_period_label(plot),"Valeur":plot["Valeur"].map(_format_number),"Type":_type(plot),"Statut":_status(plot),"Source":plot.get("source")})
    st.dataframe(_table_style(export),hide_index=True,width="stretch")
    if has_permission(st.session_state.get("user"),"export"):
        st.download_button("Télécharger cette comparaison",export.to_csv(index=False).encode("utf-8-sig"),"comparaison_series.csv","text/csv",use_container_width=True)
    st.caption("Avant d’interpréter un écart, vérifiez que les unités et définitions économiques sont comparables.")


def render_exports() -> None:
    hero("Delivery", "Exporter", "Exportez l’analyse courante, la base complète, une sélection filtrée, les séries, les statistiques ou l’historique de validation humaine.")
    if _empty(): return
    if not has_permission(st.session_state.get("user"),"export"):
        st.info("Votre profil ne permet pas l’export."); return
    from app.services.series_analytics import auditable_observations_export
    all_rows = _facts()
    all_df = prepare_dataframe(all_rows) if all_rows else pd.DataFrame()
    scope = st.radio("Périmètre des observations", ["Toutes les observations", "Analyse courante", "Sélection filtrée"], horizontal=True)
    selected_df = all_df.copy()
    if scope == "Analyse courante":
        current_id = st.session_state.get("current_analysis_id")
        if current_id and "analysis_id" in selected_df:
            selected_df = selected_df[selected_df["analysis_id"] == current_id].copy()
        else:
            st.info("Aucune analyse courante identifiée ; toutes les observations sont affichées.")
    elif scope == "Sélection filtrée":
        c1,c2,c3 = st.columns(3)
        countries = sorted(selected_df.get("country",pd.Series(dtype=str)).dropna().astype(str).unique())
        indicators = sorted(selected_df.get("indicator",pd.Series(dtype=str)).dropna().astype(str).unique())
        statuses = sorted(_status(selected_df).dropna().astype(str).unique())
        countries_sel = c1.multiselect("Pays", countries)
        indicators_sel = c2.multiselect("Indicateur", indicators)
        statuses_sel = c3.multiselect("Statut", statuses)
        mask = pd.Series(True,index=selected_df.index)
        if countries_sel: mask &= selected_df.get("country").isin(countries_sel)
        if indicators_sel: mask &= selected_df.get("indicator").isin(indicators_sel)
        if statuses_sel: mask &= _status(selected_df).isin(statuses_sel)
        selected_df = selected_df.loc[mask].copy()

    obs=auditable_observations_export(selected_df) if not selected_df.empty else pd.DataFrame()
    series_rows = _series_facts()
    series_df = prepare_dataframe(series_rows) if series_rows else pd.DataFrame()
    ser=simple_series_export(series_df) if not series_df.empty else pd.DataFrame()
    sta=simple_statistics_export(series_df) if not series_df.empty else pd.DataFrame()
    history=pd.DataFrame(fetch_observation_history(limit=50000))
    payloads=[
        ("Observations","Valeurs officielles du périmètre choisi.",obs,"observations.csv"),
        ("Séries temporelles","Points dédupliqués, rejets exclus.",ser,"series.csv"),
        ("Statistiques","Historique observé uniquement par défaut.",sta,"statistics.csv"),
        ("Historique humain","Corrections champ par champ et auteur.",history,"validation_history.csv"),
    ]
    cols=st.columns(2)
    for idx,(title,desc,data,name) in enumerate(payloads):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"### {title}"); st.caption(desc); st.metric("Lignes",len(data)); st.download_button(f"Télécharger {name}",data.to_csv(index=False).encode("utf-8-sig"),name,"text/csv",use_container_width=True,key=f"dl_{name}")
