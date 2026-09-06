from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services import database
from app.services import auth_service
from app.services.presentation_utils import prune_display_columns, horizontal_series_table


@pytest.fixture()
def isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "econintel_test.db"
    monkeypatch.setattr(database, "DB_PATH", db)
    # auth_service imports get_connection function, which reads database.DB_PATH dynamically.
    database.init_database()
    auth_service.init_auth_tables()
    database.init_observation_repository()
    return db


def _admin():
    return auth_service.authenticate("admin@itceq.tn", "Admin123!")


def test_bootstrap_admin_exists_authenticates_and_password_not_plaintext(isolated_db):
    admin = _admin()
    assert admin is not None
    assert admin["role"] == "admin"
    assert auth_service.authenticate("admin@itceq.tn", "wrong-password") is None
    with database.get_connection() as conn:
        row = conn.execute("SELECT password_hash, password_salt FROM users WHERE email=?", ("admin@itceq.tn",)).fetchone()
    assert row["password_hash"] != "Admin123!"
    assert row["password_salt"] != "Admin123!"


def test_public_user_creation_is_denied_but_admin_can_create_and_duplicate_is_rejected(isolated_db):
    ok, _ = auth_service.create_user("A", "User", "ITCEQ", "a@itceq.tn", "Strong123!", role="analyst")
    assert not ok
    admin = _admin()
    ok, _ = auth_service.create_user("A", "User", "ITCEQ", "a@itceq.tn", "Strong123!", role="analyst", acting_user=admin)
    assert ok
    ok2, _ = auth_service.create_user("A", "User", "ITCEQ", "a@itceq.tn", "Strong123!", role="analyst", acting_user=admin)
    assert not ok2
    assert auth_service.authenticate("a@itceq.tn", "Strong123!")["role"] == "analyst"


def test_standard_user_cannot_manage_users(isolated_db):
    admin = _admin()
    ok, _ = auth_service.create_user("V", "User", "ITCEQ", "viewer@itceq.tn", "Viewer123!", role="viewer", acting_user=admin)
    assert ok
    viewer = auth_service.authenticate("viewer@itceq.tn", "Viewer123!")
    assert not auth_service.has_permission(viewer, "manage_users")
    with pytest.raises(PermissionError):
        auth_service.list_users(acting_user=viewer)


def test_multiple_analyses_accumulate_and_exact_series_duplicates_are_deduplicated(isolated_db):
    f2022 = {"document_id":"d1","country":"Tunisie","indicator":"Inflation","current_value":8.3,"current_unit":"%","current_year":2022,"fact_type":"observed","validation_status":"Validé","sentence":"Inflation 8,3 % en 2022.","confidence":0.95}
    f2023 = {**f2022,"document_id":"d2","current_value":9.1,"current_year":2023,"sentence":"Inflation 9,1 % en 2023."}
    f2024 = {**f2022,"document_id":"d3","current_value":7.0,"current_year":2024,"sentence":"Inflation 7,0 % en 2024."}
    database.create_analysis("d1","one.pdf","pdf",[f2022])
    database.create_analysis("d2","two.pdf","pdf",[f2023])
    database.create_analysis("d3","three.csv","csv",[f2024])
    database.create_analysis("d4","duplicate.txt","text",[{**f2024,"document_id":"d4"}])
    all_rows = database.fetch_observations()
    series_rows = database.canonical_series_observations()
    assert len(all_rows) == 4
    assert sorted(r["current_year"] for r in series_rows) == [2022, 2023, 2024]
    assert len(database.fetch_analyses()) == 4


def test_conflicts_are_flagged_without_collapsing_provenance(isolated_db):
    base = {"country":"Tunisie","indicator":"Inflation","current_unit":"%","current_year":2024,"fact_type":"observed","validation_status":"Validé","confidence":0.9}
    database.create_analysis("d1","one.pdf","pdf",[{**base,"document_id":"d1","current_value":7.0,"sentence":"7.0"}])
    database.create_analysis("d2","two.pdf","pdf",[{**base,"document_id":"d2","current_value":7.2,"sentence":"7.2"}])
    database.detect_observation_conflicts()
    rows = database.fetch_observations()
    assert len(rows) == 2
    assert all(bool(r["conflict_status"]) for r in rows)


def test_human_edit_persists_same_observation_id_and_audits_user(isolated_db):
    fact = {"document_id":"d1","country":"Tunisie","indicator":"Croissance du PIB","current_value":7.5,"current_unit":"%","current_year":2018,"fact_type":"observed","validation_status":"À vérifier","sentence":"La valeur était de 7,5 % en 2018.","confidence":0.8}
    analysis_id = database.create_analysis("d1","report.pdf","pdf",[fact])
    row = database.fetch_observations()[0]
    obs_id = row["observation_id"]
    admin = _admin()
    database.update_observation(obs_id, {"indicator":"Inflation","validation_status":"Validé"}, admin, "Correction métier")
    updated = database.fetch_observations(analysis_id=analysis_id)[0]
    assert updated["observation_id"] == obs_id
    assert updated["indicator"] == "Inflation"
    assert updated["validation_origin"] == "human"
    assert bool(updated["human_validated"])
    hist = database.fetch_observation_history(observation_id=obs_id)
    indicator_change = next(x for x in hist if x["field"] == "indicator")
    assert indicator_change["old_value"] == "Croissance du PIB"
    assert indicator_change["new_value"] == "Inflation"
    assert indicator_change["modified_by_email"] == "admin@itceq.tn"
    assert indicator_change["reason"] == "Correction métier"


def test_rebrand_and_public_signup_removed_from_ui_sources():
    root = Path(__file__).resolve().parents[1]
    dashboard = (root / "app/dashboard.py").read_text(encoding="utf-8")
    auth = (root / "app/views/auth.py").read_text(encoding="utf-8")
    assert "Validation humaine" in dashboard
    assert "Review Desk" not in dashboard
    assert "nav_index" not in dashboard
    assert "EcoLingua-TN" not in dashboard
    assert "Créer un compte" not in auth
    assert "Sign up" not in auth
    assert "signup_form" not in auth
    branding = (root / "app/ui/branding.py").read_text(encoding="utf-8")
    assert "APP_NAME = \"Econia\"" in branding
    assert "APP_NAME" in auth



def test_display_tables_hide_empty_and_internal_columns():
    import pandas as pd

    raw = pd.DataFrame({
        "Pays": ["Tunisie"],
        "Indicateur": ["Inflation"],
        "Secteur": ["Industrie"],
        "Sous-secteur": ["None"],
        "Page": ["None"],
        "Tableau": ["None"],
        "Ligne du tableau": ["None"],
        "Colonne du tableau": ["None"],
        "Source période": ["explicit"],
        "Avertissements": ["country_inherited"],
        "Valeur": [7.0],
    })
    pruned = prune_display_columns(raw)
    assert list(pruned.columns) == ["Pays", "Indicateur", "Valeur"]


def test_series_view_is_horizontal_with_single_country_and_indicator_row():
    import pandas as pd

    series = pd.DataFrame({
        "country": ["Tunisie", "Tunisie", "Tunisie"],
        "indicator": ["Inflation", "Inflation", "Inflation"],
        "current_year": [2010, 2011, 2019],
        "current_quarter": [pd.NA, pd.NA, 1],
        "current_month": [pd.NA, pd.NA, pd.NA],
        "current_value": [4.4, 3.5, 7.2],
        "current_unit": ["%", "%", "%"],
        "current_scale": [None, None, None],
        "current_currency": [None, None, None],
        "observation_type": ["observed", "observed", "estimate"],
        "validation_status": ["Validé", "À vérifier", "Validé"],
        "confidence": [0.98, 0.89, 0.98],
        "source": ["report.pdf", "report.pdf", "report.pdf"],
    })
    horizontal = horizontal_series_table(series)
    assert horizontal.shape[0] == 1
    assert horizontal.loc[0, "Pays"] == "Tunisie"
    assert horizontal.loc[0, "Indicateur"] == "Inflation"
    assert horizontal.loc[0, "2010"] == "4.4"
    assert horizontal.loc[0, "2011"] == "3.5"
    assert horizontal.loc[0, "2019-Q1"] == "7.2"



def test_sidebar_quick_action_removed_and_series_csv_is_horizontal_export():
    root = Path(__file__).resolve().parents[1]
    dashboard = (root / "app/dashboard.py").read_text(encoding="utf-8")
    professional = (root / "app/views/professional_views.py").read_text(encoding="utf-8")
    assert 'st.button("Nouvelle analyse  →"' not in dashboard
    assert 'horizontal.to_csv(index=False)' in professional
