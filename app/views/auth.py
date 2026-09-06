from __future__ import annotations

import streamlit as st
from app.services.auth_service import authenticate
from app.ui.branding import APP_NAME, APP_SUBTITLE, APP_MARK, APP_TAGLINE_FR, APP_PITCH


def _render_brand_panel() -> None:
    st.markdown(
        f"""
        <section class="auth-brand-card">
          <div class="auth-institution-lockup">
            <div class="auth-itceq-symbol"><i></i><b></b></div>
            <div><strong>ITCEQ</strong><span>INSTITUT TUNISIEN</span></div>
          </div>
          <div class="auth-econia-lockup"><i></i><div><strong>{APP_NAME}</strong><span>{APP_SUBTITLE.upper()}</span></div></div>
          <div class="auth-brand-copy">
            <div class="brand-kicker">INTELLIGENCE ÉCONOMIQUE MULTILINGUE</div>
            <h1>Du document brut à la décision éclairée.</h1>
            <p class="brand-lead">{APP_PITCH}</p>
          </div>
          <div class="auth-benefits">
            <div><span>01</span><p><b>Analyse multiformat</b><br>PDF, CSV et texte libre.</p></div>
            <div><span>02</span><p><b>Preuves traçables</b><br>Chaque observation reste reliée à sa source.</p></div>
            <div><span>03</span><p><b>Décision assistée</b><br>Validation, séries, comparaisons et exports.</p></div>
          </div>
          <div class="brand-footer-note">Français · Arabe · Anglais</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_login() -> None:
    st.markdown(f'<div class="auth-title-block"><span class="secure-pill">Espace sécurisé</span><h2>Connexion</h2><p>Connectez-vous pour accéder à {APP_NAME}.</p></div>', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Adresse e-mail", placeholder="prenom.nom@itceq.tn")
        password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
        submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
    if submitted:
        if not email.strip() or not password:
            st.error("Veuillez renseigner votre adresse e-mail et votre mot de passe.")
        else:
            user = authenticate(email, password)
            if user:
                st.session_state.user = user
                st.session_state.page = "Vue d’ensemble"
                st.rerun()
            else:
                st.error("Adresse e-mail ou mot de passe incorrect, ou compte désactivé.")
    st.markdown('<div class="auth-help"><b>Besoin d’un accès ?</b><br>Contactez un administrateur de la plateforme.</div>', unsafe_allow_html=True)


def render_auth_page() -> None:
    st.markdown(f'<div class="auth-page-heading"><span>ITCEQ · ECONOMIC INTELLIGENCE</span><h1>{APP_NAME}</h1><p>Analyse documentaire économique · Extraction multilingue · Validation humaine</p></div>', unsafe_allow_html=True)
    left, right = st.columns([1.02, 0.98], gap="large", vertical_alignment="top")
    with left:
        _render_brand_panel()
    with right:
        st.markdown('<div class="auth-form-card-marker"></div>', unsafe_allow_html=True)
        _render_login()
    st.markdown('<div class="auth-bottom-note">Accès sécurisé · Données locales · Comptes gérés par les administrateurs</div>', unsafe_allow_html=True)
