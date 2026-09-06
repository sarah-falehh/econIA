from pathlib import Path

import pandas as pd

from app.views.professional_views import (
    _apply_year_choices,
    _default_year_choice,
    _display_observations,
    _format_number,
    _geography_label,
)


def test_number_display_removes_only_meaningless_zeroes():
    assert _format_number(4.400000) == "4.4"
    assert _format_number(-2.100000) == "-2.1"
    assert _format_number(80.0) == "80"
    assert _format_number(0.0) == "0"
    assert _format_number(2.25) == "2.25"


def test_observation_table_uses_compact_value_display():
    frame = pd.DataFrame([{
        "country": "Tunisie", "indicator": "Inflation", "current_value": 4.4,
        "current_unit": "%", "current_year": 2024, "fact_type": "observed",
        "source": "Rapport", "sentence": "L'inflation a atteint 4,4 %.",
        "confidence": .98, "validation_status": "Validé",
    }])
    assert _display_observations(frame).loc[0, "Valeur"] == "4.4"


def test_duplicate_year_selector_keeps_exactly_the_user_choice():
    frame = pd.DataFrame([
        {"Année": 2024, "Valeur numérique": 23.0, "confidence": .80,
         "validation_status": "À vérifier", "fact_type": "observed"},
        {"Année": 2024, "Valeur numérique": 80.0, "confidence": .98,
         "validation_status": "Validé", "fact_type": "observed"},
        {"Année": 2025, "Valeur numérique": 75.0, "confidence": .90,
         "validation_status": "Validé", "fact_type": "forecast"},
    ])
    selected = _apply_year_choices(frame, {2024: 0})
    assert selected.groupby("Année").size().max() == 1
    assert selected.loc[selected["Année"].eq(2024), "Valeur numérique"].iloc[0] == 23.0
    assert _default_year_choice(frame[frame["Année"].eq(2024)]) == 1


def test_geography_labels_make_groups_and_countries_explicit():
    assert _geography_label(pd.Series({"country": "Tunisie", "geography_type": "country"})) == "🇹🇳  Tunisie · Pays"
    assert _geography_label(pd.Series({"country": "PECO", "geography_type": "economic_group"})) == "🌐  PECO · Groupe économique"


def test_v590_observation_table_adds_flags_and_translates_geography_type():
    frame = pd.DataFrame([{
        "country": "Algérie", "geography_type": "country", "indicator": "Inflation",
        "current_value": 4.2, "current_unit": "%", "current_year": 2024,
        "fact_type": "observed", "source": "Rapport", "sentence": "Preuve.",
        "confidence": .95, "validation_status": "Validé",
    }])
    shown = _display_observations(frame)
    assert shown.loc[0, "Pays"] == "🇩🇿  Algérie"
    assert shown.loc[0, "Type géographique"] == "Pays"


def test_sidebar_navigation_has_a_stable_widget_key_and_no_competing_index():
    source = (Path(__file__).parents[1] / "app" / "dashboard.py").read_text(encoding="utf-8")
    radio = source[source.index("page = st.radio"):source.index("st.session_state.page = page")]
    assert 'key="navigation_page"' in radio
    assert "index=" not in radio


def test_compare_indicator_filters_geographies_without_previous_selection_leakage():
    source = (Path(__file__).parents[1] / "app" / "views" / "professional_views.py").read_text(encoding="utf-8")
    compare = source[source.index("def render_compare"):source.index("def render_exports")]
    indicator_selector = compare.index('st.selectbox("Indicateur"')
    geography_selector = compare.index('st.multiselect("Pays, régions et groupes économiques"')
    assert indicator_selector < geography_selector
    assert 'pool=dated[dated["indicator"]==indicator]' in compare
    assert 'geographies=sorted(all_geo["geography_label"]' in compare
    assert "selected_pool" not in compare


def test_duplicate_value_control_is_compact_and_graph_linked():
    source = (Path(__file__).parents[1] / "app" / "views" / "professional_views.py").read_text(encoding="utf-8")
    series = source[source.index("def render_series"):source.index("def render_visualizations")]
    assert "st.segmented_control(" in series
    assert "Choisir la valeur finale pour les années en double" not in series
    assert "chart_slot.plotly_chart" in series


def test_tables_and_charts_use_readable_font_sizes():
    root = Path(__file__).parents[1]
    theme = (root / "app" / "ui" / "theme.py").read_text(encoding="utf-8")
    views = (root / "app" / "views" / "professional_views.py").read_text(encoding="utf-8")
    assert 'font-size:16px!important' in theme
    assert 'tickfont=dict(color="#000000",size=14)' in views


def test_v580_installs_shared_chart_theme_and_smooth_series():
    root = Path(__file__).parents[1]
    dashboard = (root / "app" / "dashboard.py").read_text(encoding="utf-8")
    theme = (root / "app" / "ui" / "theme.py").read_text(encoding="utf-8")
    views = (root / "app" / "views" / "professional_views.py").read_text(encoding="utf-8")
    assert "configure_plotly_theme()" in dashboard
    assert 'pio.templates.default = "econia"' in theme
    assert 'shape="spline"' in views


def test_v580_sidebar_icons_do_not_change_route_values():
    source = (Path(__file__).parents[1] / "app" / "dashboard.py").read_text(encoding="utf-8")
    assert "PAGE_ICONS =" in source
    assert 'format_func=lambda name: f"{PAGE_ICONS.get(name' in source
    assert "ROUTES[page]()" in source


def test_v601_brand_lockups_are_aligned_and_typography_is_bold():
    theme = (Path(__file__).parents[1] / "app" / "ui" / "theme.py").read_text(encoding="utf-8")
    assert ".institution-lockup:after{width:82px!important" in theme
    assert "left:7px!important" in theme
    assert ".brand-lockup{min-height:88px!important" in theme
    assert '[data-testid="stDataFrame"] [role="gridcell"]{font-weight:600!important' in theme
    assert '[data-testid="stSidebar"] .stRadio label,[data-testid="stSidebar"] .stRadio label p{font-weight:700!important}' in theme
