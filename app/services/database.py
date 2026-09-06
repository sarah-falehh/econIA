from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Iterable

from app.models.article_document import ArticleDocument


DB_PATH = Path("data/ecolinguatn.db")


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS imported_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                input_type TEXT NOT NULL,
                title TEXT,
                text TEXT NOT NULL,
                source TEXT,
                publication_date TEXT,
                language TEXT,
                filename TEXT,
                page_number INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_documents(documents: Iterable[ArticleDocument]) -> int:
    init_database()
    inserted = 0

    with get_connection() as conn:
        for doc in documents:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO imported_documents (
                    document_id,
                    input_type,
                    title,
                    text,
                    source,
                    publication_date,
                    language,
                    filename,
                    page_number
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.document_id,
                    doc.input_type,
                    doc.title,
                    doc.text,
                    doc.source,
                    doc.publication_date,
                    doc.language,
                    doc.filename,
                    doc.page_number,
                ),
            )
            inserted += cursor.rowcount

        conn.commit()

    return inserted


def fetch_documents(limit: int = 200) -> list[dict]:
    init_database()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                document_id,
                input_type,
                title,
                source,
                publication_date,
                language,
                filename,
                page_number,
                created_at,
                LENGTH(text) AS text_length
            FROM imported_documents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]



def fetch_full_documents(limit: int = 500) -> list[dict]:
    init_database()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                document_id,
                input_type,
                title,
                text,
                source,
                publication_date,
                language,
                filename,
                page_number,
                created_at
            FROM imported_documents
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def init_extraction_table() -> None:
    init_database()

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS economic_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                title TEXT,
                language TEXT,
                country TEXT,
                indicator_code TEXT NOT NULL,
                indicator TEXT NOT NULL,
                indicator_raw TEXT,
                value REAL,
                value_raw TEXT,
                unit TEXT,
                month INTEGER,
                quarter INTEGER,
                year INTEGER,
                source TEXT,
                trend TEXT,
                comparison_detected INTEGER DEFAULT 0,
                sentence TEXT NOT NULL,
                confidence REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def replace_facts_for_document(document_id: str, facts: list[dict]) -> int:
    init_extraction_table()

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM economic_facts WHERE document_id = ?",
            (document_id,),
        )

        inserted = 0

        for fact in facts:
            cursor = conn.execute(
                """
                INSERT INTO economic_facts (
                    document_id,
                    title,
                    language,
                    country,
                    indicator_code,
                    indicator,
                    indicator_raw,
                    value,
                    value_raw,
                    unit,
                    month,
                    quarter,
                    year,
                    source,
                    trend,
                    comparison_detected,
                    sentence,
                    confidence
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fact.get("document_id"),
                    fact.get("title"),
                    fact.get("language"),
                    fact.get("country"),
                    fact.get("indicator_code"),
                    fact.get("indicator"),
                    fact.get("indicator_raw"),
                    fact.get("value"),
                    fact.get("value_raw"),
                    fact.get("unit"),
                    fact.get("month"),
                    fact.get("quarter"),
                    fact.get("year"),
                    fact.get("source"),
                    fact.get("trend"),
                    int(bool(fact.get("comparison_detected"))),
                    fact.get("sentence"),
                    fact.get("confidence"),
                ),
            )
            inserted += cursor.rowcount

        conn.commit()

    return inserted


def fetch_economic_facts(limit: int = 2000) -> list[dict]:
    init_extraction_table()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM economic_facts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]



def init_structured_facts_table() -> None:
    init_database()
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS structured_economic_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                language TEXT,
                country TEXT,
                indicator_code TEXT,
                indicator TEXT,
                indicator_raw TEXT,

                current_value REAL,
                current_value_raw TEXT,
                current_unit TEXT,
                current_month INTEGER,
                current_quarter INTEGER,
                current_year INTEGER,

                reference_value REAL,
                reference_value_raw TEXT,
                reference_unit TEXT,
                reference_month INTEGER,
                reference_quarter INTEGER,
                reference_year INTEGER,

                absolute_change REAL,
                relative_change REAL,
                direction TEXT,
                comparison_type TEXT,

                source TEXT,
                sentence TEXT,
                confidence REAL,
                needs_review INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def replace_structured_facts(document_id: str, facts: list[dict]) -> int:
    init_structured_facts_table()

    columns = [
        "document_id", "language", "country", "indicator_code",
        "indicator", "indicator_raw",
        "current_value", "current_value_raw", "current_unit",
        "current_month", "current_quarter", "current_year",
        "reference_value", "reference_value_raw", "reference_unit",
        "reference_month", "reference_quarter", "reference_year",
        "absolute_change", "relative_change", "direction",
        "comparison_type", "source", "sentence", "confidence",
        "needs_review",
    ]

    placeholders = ", ".join(["?"] * len(columns))

    with get_connection() as conn:
        conn.execute(
            "DELETE FROM structured_economic_facts WHERE document_id = ?",
            (document_id,),
        )

        inserted = 0
        for fact in facts:
            values = [
                int(bool(fact.get(col))) if col == "needs_review"
                else fact.get(col)
                for col in columns
            ]
            cursor = conn.execute(
                f"""
                INSERT INTO structured_economic_facts
                ({", ".join(columns)})
                VALUES ({placeholders})
                """,
                values,
            )
            inserted += cursor.rowcount

        conn.commit()

    return inserted


def fetch_structured_facts(limit: int = 5000) -> list[dict]:
    init_structured_facts_table()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM structured_economic_facts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]



def init_business_facts_table() -> None:
    init_database()

    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS business_economic_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT NOT NULL,
                language TEXT,
                country TEXT,
                indicator_code TEXT,
                indicator TEXT,
                indicator_raw TEXT,
                topic TEXT,
                fact_type TEXT,

                value_type TEXT,

                current_value REAL,
                current_value_raw TEXT,
                current_unit TEXT,
                current_scale TEXT,
                current_currency TEXT,

                variation_value REAL,
                variation_unit TEXT,

                current_month INTEGER,
                current_quarter INTEGER,
                current_year INTEGER,

                reference_value REAL,
                reference_value_raw TEXT,
                reference_unit TEXT,
                reference_scale TEXT,
                reference_currency TEXT,

                reference_month INTEGER,
                reference_quarter INTEGER,
                reference_year INTEGER,

                absolute_change REAL,
                relative_change REAL,
                direction TEXT,
                comparison_type TEXT,

                source TEXT,
                sentence TEXT,
                confidence REAL,
                needs_review INTEGER DEFAULT 0,
                review_reason TEXT,
                validation_status TEXT DEFAULT 'pending',
                observation_type TEXT,
                validation_evidence TEXT,
                validation_warnings TEXT,
                conflict_status INTEGER DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        existing_columns = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(business_economic_facts)"
            ).fetchall()
        }

        migration_columns = {
            "topic": "TEXT",
            "fact_type": "TEXT",
            "current_scale": "TEXT",
            "current_currency": "TEXT",
            "reference_scale": "TEXT",
            "reference_currency": "TEXT",
            "validation_status": "TEXT",
            "observation_type": "TEXT",
            "validation_evidence": "TEXT",
            "validation_warnings": "TEXT",
            "conflict_status": "INTEGER DEFAULT 0",
        }

        for column_name, column_type in migration_columns.items():
            if column_name not in existing_columns:
                conn.execute(
                    f"ALTER TABLE business_economic_facts "
                    f"ADD COLUMN {column_name} {column_type}"
                )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fact_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                original_value TEXT,
                corrected_value TEXT,
                validation_status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (fact_id)
                    REFERENCES business_economic_facts(id)
            )
            """
        )

        conn.commit()


def replace_business_facts(
    document_id: str,
    facts: list[dict],
) -> int:
    init_business_facts_table()

    columns = [
        "document_id",
        "language",
        "country",
        "indicator_code",
        "indicator",
        "indicator_raw",
        "topic",
        "fact_type",
        "value_type",
        "current_value",
        "current_value_raw",
        "current_unit",
        "current_scale",
        "current_currency",
        "variation_value",
        "variation_unit",
        "current_month",
        "current_quarter",
        "current_year",
        "reference_value",
        "reference_value_raw",
        "reference_unit",
        "reference_scale",
        "reference_currency",
        "reference_month",
        "reference_quarter",
        "reference_year",
        "absolute_change",
        "relative_change",
        "direction",
        "comparison_type",
        "source",
        "sentence",
        "confidence",
        "needs_review",
        "review_reason",
        "validation_status",
        "observation_type",
        "validation_evidence",
        "validation_warnings",
        "conflict_status",
    ]

    placeholders = ", ".join(["?"] * len(columns))

    with get_connection() as conn:
        previous_rows = conn.execute(
            """
            SELECT id
            FROM business_economic_facts
            WHERE document_id = ?
            """,
            (document_id,),
        ).fetchall()

        for row in previous_rows:
            conn.execute(
                """
                DELETE FROM fact_annotations
                WHERE fact_id = ?
                """,
                (row["id"],),
            )

        conn.execute(
            """
            DELETE FROM business_economic_facts
            WHERE document_id = ?
            """,
            (document_id,),
        )

        inserted = 0

        for fact in facts:
            values = []
            for column in columns:
                value = fact.get(column)
                if column in {"needs_review", "conflict_status"}:
                    value = int(bool(value))
                elif column in {"validation_evidence", "validation_warnings"} and isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                values.append(value)

            cursor = conn.execute(
                f"""
                INSERT INTO business_economic_facts
                ({", ".join(columns)})
                VALUES ({placeholders})
                """,
                values,
            )

            inserted += cursor.rowcount

        conn.commit()

    return inserted


def fetch_business_facts(
    limit: int = 5000,
    only_pending: bool = False,
) -> list[dict]:
    init_business_facts_table()

    query = """
        SELECT *
        FROM business_economic_facts
    """

    if only_pending:
        query += """
            WHERE needs_review = 1
               OR validation_status = 'pending'
        """

    query += """
        ORDER BY id DESC
        LIMIT ?
    """

    with get_connection() as conn:
        rows = conn.execute(
            query,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]


def update_business_fact(
    fact_id: int,
    updates: dict,
    validation_status: str,
) -> None:
    init_business_facts_table()

    allowed_fields = {
        "country",
        "indicator_code",
        "indicator",
        "value_type",
        "current_value",
        "current_unit",
        "current_scale",
        "current_currency",
        "variation_value",
        "variation_unit",
        "current_month",
        "current_quarter",
        "current_year",
        "reference_value",
        "reference_unit",
        "reference_scale",
        "reference_currency",
        "reference_month",
        "reference_quarter",
        "reference_year",
        "direction",
        "comparison_type",
        "source",
    }

    cleaned_updates = {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }

    with get_connection() as conn:
        original = conn.execute(
            """
            SELECT *
            FROM business_economic_facts
            WHERE id = ?
            """,
            (fact_id,),
        ).fetchone()

        if original is None:
            raise ValueError(
                "Le fait économique demandé n'existe pas."
            )

        for field_name, corrected_value in cleaned_updates.items():
            original_value = original[field_name]

            if str(original_value) != str(corrected_value):
                conn.execute(
                    """
                    INSERT INTO fact_annotations (
                        fact_id,
                        field_name,
                        original_value,
                        corrected_value,
                        validation_status
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        fact_id,
                        field_name,
                        (
                            None
                            if original_value is None
                            else str(original_value)
                        ),
                        (
                            None
                            if corrected_value is None
                            else str(corrected_value)
                        ),
                        validation_status,
                    ),
                )

        if cleaned_updates:
            assignments = ", ".join(
                f"{field_name} = ?"
                for field_name in cleaned_updates
            )

            values = list(cleaned_updates.values())
            values.extend(
                [
                    validation_status,
                    fact_id,
                ]
            )

            conn.execute(
                f"""
                UPDATE business_economic_facts
                SET {assignments},
                    validation_status = ?,
                    needs_review = 0
                WHERE id = ?
                """,
                values,
            )
        else:
            conn.execute(
                """
                UPDATE business_economic_facts
                SET validation_status = ?,
                    needs_review = 0
                WHERE id = ?
                """,
                (
                    validation_status,
                    fact_id,
                ),
            )

        conn.commit()


def fetch_annotations(
    limit: int = 5000,
) -> list[dict]:
    init_business_facts_table()

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.*,
                f.document_id,
                f.language,
                f.sentence
            FROM fact_annotations a
            JOIN business_economic_facts f
              ON f.id = a.fact_id
            ORDER BY a.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(row) for row in rows]

# ---------------------------------------------------------------------------
# v5.6 — Central persistent observation repository
# ---------------------------------------------------------------------------

def init_observation_repository() -> None:
    """Create the append-only analysis registry and canonical observation store."""
    init_database()
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT UNIQUE,
                source_id TEXT,
                source_name TEXT,
                source_type TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                number_of_events INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_id TEXT UNIQUE,
                analysis_id TEXT NOT NULL,
                document_id TEXT,
                source_name TEXT,
                source_type TEXT,
                country TEXT,
                indicator TEXT,
                current_value REAL,
                current_unit TEXT,
                current_year INTEGER,
                validation_status TEXT,
                observation_type TEXT,
                confidence REAL,
                conflict_status INTEGER NOT NULL DEFAULT 0,
                validation_origin TEXT NOT NULL DEFAULT 'automatic',
                human_validated INTEGER NOT NULL DEFAULT 0,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(analysis_id) REFERENCES analyses(analysis_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observation_id TEXT NOT NULL,
                modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                modified_by_user_id INTEGER,
                modified_by_email TEXT,
                field TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                FOREIGN KEY(modified_by_user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_obs_analysis ON observations(analysis_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_obs_series ON observations(country, indicator, current_year)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_obs_document ON observations(document_id)")
        conn.commit()


def _next_prefixed_id(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 AS n FROM {table}").fetchone()
    return f"{prefix}-{int(row['n']):06d}"


def create_analysis(source_id: str | None, source_name: str | None, source_type: str | None, facts: list[dict]) -> str:
    """Persist one analysis run without replacing earlier runs."""
    init_observation_repository()
    with get_connection() as conn:
        analysis_id = _next_prefixed_id(conn, "analyses", "ANL")
        conn.execute(
            "INSERT INTO analyses(analysis_id, source_id, source_name, source_type, number_of_events) VALUES (?, ?, ?, ?, ?)",
            (analysis_id, source_id, source_name, source_type, len(facts)),
        )
        for fact in facts:
            observation_id = _next_prefixed_id(conn, "observations", "OBS")
            payload = dict(fact)
            payload.update({
                "observation_id": observation_id,
                "analysis_id": analysis_id,
                "source_name": source_name or payload.get("source") or payload.get("title"),
                "source_type": source_type,
                "validation_origin": "automatic",
                "human_validated": False,
                "original_evidence": payload.get("sentence") or payload.get("evidence"),
            })
            conn.execute(
                """
                INSERT INTO observations(
                    observation_id, analysis_id, document_id, source_name, source_type,
                    country, indicator, current_value, current_unit, current_year,
                    validation_status, observation_type, confidence, conflict_status,
                    validation_origin, human_validated, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'automatic', 0, ?)
                """,
                (
                    observation_id, analysis_id, payload.get("document_id") or source_id,
                    payload.get("source_name"), source_type, payload.get("country"), payload.get("indicator"),
                    payload.get("current_value"), payload.get("current_unit"), payload.get("current_year"),
                    payload.get("validation_status"), payload.get("observation_type") or payload.get("fact_type"),
                    payload.get("confidence"), int(bool(payload.get("conflict_status"))),
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )
        conn.commit()
    return analysis_id


def fetch_observations(limit: int = 50000, analysis_id: str | None = None) -> list[dict]:
    init_observation_repository()
    query = "SELECT * FROM observations"
    params: list = []
    if analysis_id:
        query += " WHERE analysis_id = ?"
        params.append(analysis_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    result = []
    for row in rows:
        base = dict(row)
        try:
            payload = json.loads(base.pop("payload_json") or "{}")
        except Exception:
            payload = {}
        payload.update({k: v for k, v in base.items() if k not in {"id"}})
        result.append(payload)
    return result


def fetch_analyses(limit: int = 5000) -> list[dict]:
    init_observation_repository()
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def update_observation(observation_id: str, updates: dict, user: dict | None, reason: str = "") -> None:
    """Persist human corrections while retaining a per-field immutable audit trail."""
    init_observation_repository()
    protected = {"id", "observation_id", "analysis_id", "created_at", "modified_by_user_id", "modified_by_email"}
    cleaned = {k: v for k, v in updates.items() if k not in protected}
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM observations WHERE observation_id = ?", (observation_id,)).fetchone()
        if row is None:
            raise ValueError("L’observation demandée n’existe pas.")
        payload = json.loads(row["payload_json"] or "{}")
        for field, new_value in cleaned.items():
            old_value = payload.get(field)
            # Normalize Streamlit/pandas NA-ish values for stable comparison/storage.
            if hasattr(new_value, "item"):
                try: new_value = new_value.item()
                except Exception: pass
            if str(old_value) != str(new_value):
                conn.execute(
                    """INSERT INTO observation_history(
                        observation_id, modified_by_user_id, modified_by_email, field,
                        old_value, new_value, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (observation_id, (user or {}).get("id"), (user or {}).get("email"), field,
                     None if old_value is None else str(old_value),
                     None if new_value is None else str(new_value), reason),
                )
                payload[field] = new_value
        payload["validation_origin"] = "human"
        payload["human_validated"] = True
        payload["human_comment"] = reason
        indexed = {
            "country": payload.get("country"), "indicator": payload.get("indicator"),
            "current_value": payload.get("current_value"), "current_unit": payload.get("current_unit"),
            "current_year": payload.get("current_year"), "validation_status": payload.get("validation_status"),
            "observation_type": payload.get("observation_type") or payload.get("fact_type"),
            "confidence": payload.get("confidence"), "conflict_status": int(bool(payload.get("conflict_status"))),
        }
        conn.execute(
            """UPDATE observations SET country=?, indicator=?, current_value=?, current_unit=?, current_year=?,
               validation_status=?, observation_type=?, confidence=?, conflict_status=?, validation_origin='human',
               human_validated=1, payload_json=?, updated_at=CURRENT_TIMESTAMP WHERE observation_id=?""",
            (*indexed.values(), json.dumps(payload, ensure_ascii=False, default=str), observation_id),
        )
        conn.commit()


def fetch_observation_history(limit: int = 10000, observation_id: str | None = None) -> list[dict]:
    init_observation_repository()
    query = "SELECT * FROM observation_history"
    params: list = []
    if observation_id:
        query += " WHERE observation_id = ?"
        params.append(observation_id)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def detect_observation_conflicts() -> None:
    """Flag competing values for the same semantic series/period; identical duplicates are not conflicts."""
    init_observation_repository()
    with get_connection() as conn:
        conn.execute("UPDATE observations SET conflict_status = 0")
        groups = conn.execute(
            """SELECT country, indicator, current_year, current_unit
               FROM observations
               WHERE country IS NOT NULL AND indicator IS NOT NULL AND current_year IS NOT NULL
                 AND COALESCE(validation_status,'') NOT IN ('Rejeté','rejected')
               GROUP BY country, indicator, current_year, current_unit
               HAVING COUNT(DISTINCT current_value) > 1"""
        ).fetchall()
        for g in groups:
            conn.execute(
                """UPDATE observations SET conflict_status=1
                   WHERE country IS ? AND indicator IS ? AND current_year IS ? AND current_unit IS ?""",
                (g["country"], g["indicator"], g["current_year"], g["current_unit"]),
            )
        # Keep JSON payloads synchronized with the indexed conflict flag.
        rows = conn.execute("SELECT observation_id, conflict_status, payload_json FROM observations").fetchall()
        for r in rows:
            p = json.loads(r["payload_json"] or "{}")
            p["conflict_status"] = bool(r["conflict_status"])
            conn.execute("UPDATE observations SET payload_json=? WHERE observation_id=?", (json.dumps(p, ensure_ascii=False, default=str), r["observation_id"]))
        conn.commit()


def canonical_series_observations() -> list[dict]:
    """Return official analytics rows with human decisions taking precedence.

    Provenance is never deleted from storage. If a human-validated row and an
    automatic row represent the same source evidence, the human version is the
    only one exposed to analytics. Exact semantic duplicates across different
    sources are also collapsed to one series point.
    """
    rows = fetch_observations()
    rows.sort(key=lambda r: (0 if r.get("validation_origin") == "human" or bool(r.get("human_validated")) else 1, str(r.get("created_at") or "")))
    human_origins = set()
    for r in rows:
        if r.get("validation_origin") == "human" or bool(r.get("human_validated")):
            human_origins.add((r.get("document_id"), r.get("original_evidence") or r.get("sentence")))
    seen = set(); out = []
    for r in rows:
        if str(r.get("validation_status") or "") in {"Rejeté", "rejected"}:
            continue
        origin = (r.get("document_id"), r.get("original_evidence") or r.get("sentence"))
        if origin in human_origins and not (r.get("validation_origin") == "human" or bool(r.get("human_validated"))):
            continue
        key = (
            r.get("country"), r.get("indicator"), r.get("current_year"), r.get("current_quarter"),
            r.get("current_month"), r.get("current_value"), r.get("current_unit"), r.get("current_scale"),
            r.get("current_currency"), r.get("observation_type") or r.get("fact_type"),
        )
        if key in seen:
            continue
        seen.add(key); out.append(r)
    return out
