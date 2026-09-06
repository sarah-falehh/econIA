from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from app.services.database import fetch_business_facts


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["current_value"] = pd.to_numeric(df.get("current_value"), errors="coerce")
    df["current_year"] = pd.to_numeric(df.get("current_year"), errors="coerce")
    df["current_month"] = pd.to_numeric(df.get("current_month"), errors="coerce").fillna(12)
    df = df.dropna(subset=["current_value", "current_year", "indicator"])
    if df.empty:
        return df
    df["date"] = pd.to_datetime(dict(year=df["current_year"].astype(int), month=df["current_month"].astype(int).clip(1, 12), day=1), errors="coerce")
    return df.dropna(subset=["date"]).sort_values("date")


def render_trends() -> None:
    st.title("Tendances et projections")
    st.caption("Visualisez l’évolution des indicateurs économiques et explorez une projection simple, sans réglage technique.")

    stored = pd.DataFrame(fetch_business_facts(limit=20000))
    source = st.segmented_control("Source des données", ["Données extraites", "Importer un CSV"], default="Données extraites")

    if source == "Importer un CSV":
        upload = st.file_uploader("Déposez un fichier contenant une date, un indicateur et une valeur", type=["csv"])
        if not upload:
            st.info("Ajoutez un fichier CSV pour commencer.")
            return
        raw = pd.read_csv(upload)
        cols = raw.columns.tolist()
        c1, c2, c3 = st.columns(3)
        date_col = c1.selectbox("Colonne date", cols)
        indicator_col = c2.selectbox("Colonne indicateur", cols)
        value_col = c3.selectbox("Colonne valeur", cols)
        data = raw[[date_col, indicator_col, value_col]].rename(columns={date_col:"date", indicator_col:"indicator", value_col:"current_value"})
        data["date"] = pd.to_datetime(data["date"], errors="coerce")
        data["current_value"] = pd.to_numeric(data["current_value"], errors="coerce")
        data = data.dropna()
    else:
        data = _prepare(stored)
        if data.empty:
            st.info("Aucune série exploitable n’est disponible. Lancez une extraction contenant des dates et des valeurs, ou importez un CSV.")
            return

    c1, c2 = st.columns([1.2, 1])
    indicator = c1.selectbox("Indicateur", sorted(data["indicator"].dropna().unique()))
    country_col = "country_label" if "country_label" in data.columns else "country"
    scoped = data[data["indicator"] == indicator].copy()
    if country_col in scoped.columns and scoped[country_col].notna().any():
        countries = ["Tous"] + sorted(scoped[country_col].dropna().astype(str).unique().tolist())
        country = c2.selectbox("Pays", countries)
        if country != "Tous":
            scoped = scoped[scoped[country_col].astype(str) == country]
    else:
        c2.empty()

    series = scoped.groupby("date", as_index=False)["current_value"].mean().sort_values("date")
    if series.empty:
        st.warning("Aucune valeur n’est disponible pour cette sélection.")
        return

    a, b, c = st.columns(3)
    a.metric("Observations", len(series))
    a_delta = None if len(series) < 2 else series["current_value"].iloc[-1] - series["current_value"].iloc[-2]
    b.metric("Dernière valeur", f"{series['current_value'].iloc[-1]:,.2f}", None if a_delta is None else f"{a_delta:+,.2f}")
    c.metric("Période couverte", f"{series['date'].min().date()} → {series['date'].max().date()}")

    fig = px.line(series, x="date", y="current_value", markers=True, labels={"date":"Période", "current_value":"Valeur"}, title=f"Évolution de {indicator}")
    fig.update_layout(hovermode="x unified", margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.markdown("### Projection exploratoire")
        st.caption("La plateforme prolonge la tendance observée. Cette estimation aide à explorer les données et ne remplace pas une prévision économétrique officielle.")
        horizon = st.slider("Nombre de périodes à projeter", 1, 12, 4)
        if len(series) < 3:
            st.warning("Au moins trois observations sont nécessaires pour afficher une projection.")
            return
        x = np.arange(len(series)).reshape(-1,1)
        y = series["current_value"].to_numpy()
        model = LinearRegression().fit(x,y)
        fitted = model.predict(x)
        future_x = np.arange(len(series), len(series)+horizon).reshape(-1,1)
        future_y = model.predict(future_x)
        inferred = pd.infer_freq(series["date"]) or "YS"
        try:
            future_dates = pd.date_range(series["date"].iloc[-1], periods=horizon+1, freq=inferred)[1:]
        except ValueError:
            future_dates = pd.date_range(series["date"].iloc[-1], periods=horizon+1, freq="YS")[1:]
        history = series.assign(Type="Historique")
        forecast = pd.DataFrame({"date":future_dates,"current_value":future_y,"Type":"Projection"})
        combined = pd.concat([history, forecast], ignore_index=True)
        fig2 = px.line(combined, x="date", y="current_value", color="Type", markers=True, labels={"date":"Période", "current_value":"Valeur"}, title="Historique et projection")
        fig2.update_layout(hovermode="x unified", margin=dict(l=10,r=10,t=55,b=10))
        st.plotly_chart(fig2, use_container_width=True)
        k1,k2,k3 = st.columns(3)
        k1.metric("Tendance par période", f"{model.coef_[0]:+,.2f}")
        k2.metric("Valeur projetée finale", f"{future_y[-1]:,.2f}")
        k3.metric("Erreur moyenne historique", f"{mean_absolute_error(y,fitted):,.2f}")
