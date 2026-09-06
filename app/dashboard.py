from __future__ import annotations

from pathlib import Path
import sys
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.auth_service import ROLE_LABELS, has_permission, init_auth_tables, log_action
from app.services.database import init_database
from app.ui.theme import configure_plotly_theme, inject_theme
from app.ui.branding import APP_NAME, APP_SUBTITLE, APP_MARK, APP_VERSION
from app.views.admin_users import render_admin_users
from app.views.auth import render_auth_page
from app.views.workspace import render_workspace
from app.views.professional_views import (
    render_overview, render_observations, render_series, render_visualizations,
    render_statistics, render_sources, render_compare, render_exports, render_review_desk,
)

st.set_page_config(
    page_title=f"{APP_NAME} · {APP_SUBTITLE}",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()
configure_plotly_theme()
init_database()
init_auth_tables()

if "user" not in st.session_state:
    render_auth_page()
    st.stop()

user = st.session_state.user
pages = [
    ("Vue d’ensemble", "view_dashboard"),
    ("Nouvelle analyse", "extract"),
    ("Observations", "view_dashboard"),
    ("Validation humaine", "validate"),
    ("Séries temporelles", "view_dashboard"),
    ("Visualisations", "view_dashboard"),
    ("Statistiques", "view_dashboard"),
    ("Sources", "view_dashboard"),
    ("Comparer", "view_dashboard"),
    ("Exporter", "export"),
]
if has_permission(user, "manage_users"):
    pages.append(("Administration", "manage_users"))
available = [name for name, perm in pages if has_permission(user, perm)]
PAGE_ICONS = {
    "Vue d’ensemble": "◈", "Nouvelle analyse": "✦", "Observations": "▦",
    "Validation humaine": "✓", "Séries temporelles": "⌁", "Visualisations": "◉",
    "Statistiques": "∑", "Sources": "⌘", "Comparer": "⇄", "Exporter": "↗",
    "Administration": "⚙",
}
if "page" not in st.session_state or st.session_state.page not in available:
    st.session_state.page = available[0]
if "navigation_page" not in st.session_state or st.session_state.navigation_page not in available:
    st.session_state.navigation_page = st.session_state.page


with st.sidebar:
    st.markdown(
        f'''<div class="institution-lockup"><div class="itceq-symbol"><i></i><b></b></div><div><strong>ITCEQ</strong><span>Institut tunisien</span></div></div><div class="brand-lockup"><div class="brand-arc"></div><div><div class="brand-name">{APP_NAME.replace(' AI', ' <b>AI</b>')}</div><div class="brand-sub">{APP_SUBTITLE}</div></div></div>''',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="side-section">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        "Navigation",
        available,
        key="navigation_page",
        format_func=lambda name: f"{PAGE_ICONS.get(name, '•')}  {name}",
        label_visibility="collapsed",
    )
    st.session_state.page = page

    st.markdown('<div class="side-section">Profil</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="user-chip"><b>{user["first_name"]} {user["last_name"]}</b><br><span>{ROLE_LABELS.get(user["role"], user["role"])}</span></div>',
        unsafe_allow_html=True,
    )
    with st.popover("Compte", use_container_width=True):
        st.caption(user.get("email", ""))
        if st.button("Se déconnecter", use_container_width=True):
            log_action(user.get("id"), user.get("email"), "logout")
            st.session_state.clear()
            st.rerun()
    st.caption(f"{APP_NAME} · {APP_VERSION}")

ROUTES = {
    "Vue d’ensemble": render_overview,
    "Nouvelle analyse": render_workspace,
    "Observations": render_observations,
    "Validation humaine": render_review_desk,
    "Séries temporelles": render_series,
    "Visualisations": render_visualizations,
    "Statistiques": render_statistics,
    "Sources": render_sources,
    "Comparer": render_compare,
    "Exporter": render_exports,
    "Administration": render_admin_users,
}
ROUTES[page]()
