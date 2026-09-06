from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone
from typing import Any

from app.services.database import get_connection

ROLES = ("admin", "analyst", "viewer")
ROLE_LABELS = {
    "admin": "Administrateur",
    "analyst": "Analyste",
    "viewer": "Lecteur",
}

PERMISSIONS = {
    "admin": {
        "view_dashboard", "view_contradictions", "view_rag", "ingest",
        "extract", "validate", "train_model", "export", "manage_users",
    },
    "analyst": {
        "view_dashboard", "view_contradictions", "view_rag", "ingest",
        "extract", "validate", "export",
    },
    "viewer": {"view_dashboard", "view_contradictions", "view_rag"},
}

# Precomputed PBKDF2-SHA256 material for the required bootstrap credential.
# The plaintext password is deliberately not stored in source code.
_BOOTSTRAP_ADMIN_EMAIL = "admin@itceq.tn"
_BOOTSTRAP_ADMIN_SALT = "8f1c5e4c950e6e98bf05551bd94f3ca1f1c4cf8b3a882815752256dc37ddaf10"
_BOOTSTRAP_ADMIN_HASH = "b9653278cb7ce9ba6e9cca2c38acbbaa0ea7ddde8770eb58795e6f1c0018b696"


def init_auth_tables() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                company TEXT,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (_BOOTSTRAP_ADMIN_EMAIL,)).fetchone()
        if not exists:
            conn.execute(
                """INSERT INTO users(first_name,last_name,company,email,password_hash,password_salt,role,is_active)
                   VALUES (?,?,?,?,?,?, 'admin', 1)""",
                ("Administrateur", "ITCEQ", "ITCEQ", _BOOTSTRAP_ADMIN_EMAIL, _BOOTSTRAP_ADMIN_HASH, _BOOTSTRAP_ADMIN_SALT),
            )
        conn.commit()


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", _normalize_email(email)))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    if not re.search(r"[A-Z]", password):
        return False, "Ajoutez au moins une lettre majuscule."
    if not re.search(r"[a-z]", password):
        return False, "Ajoutez au moins une lettre minuscule."
    if not re.search(r"\d", password):
        return False, "Ajoutez au moins un chiffre."
    return True, ""


def _hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(32)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000)
    return digest.hex(), salt.hex()


def create_user(
    first_name: str,
    last_name: str,
    company: str,
    email: str,
    password: str,
    role: str = "viewer",
    is_active: bool = True,
    acting_user: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """Create an account. Only an authenticated admin may call this public service."""
    init_auth_tables()
    if not has_permission(acting_user, "manage_users"):
        return False, "Action réservée à un administrateur."
    email = _normalize_email(email)
    if role not in ROLES:
        return False, "Rôle invalide."
    if not first_name.strip() or not last_name.strip():
        return False, "Le prénom et le nom sont obligatoires."
    if not validate_email(email):
        return False, "L’adresse e-mail n’est pas valide."
    valid, message = validate_password(password)
    if not valid:
        return False, message
    password_hash, salt = _hash_password(password)
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users(first_name,last_name,company,email,password_hash,password_salt,role,is_active)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (first_name.strip(), last_name.strip(), company.strip(), email, password_hash, salt, role, int(is_active)),
            )
            conn.commit()
        log_action((acting_user or {}).get("id"), (acting_user or {}).get("email"), "user_created", f"user_id={cursor.lastrowid};email={email};role={role}")
        return True, "Utilisateur créé avec succès."
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            return False, "Un compte existe déjà avec cette adresse e-mail."
        return False, "La création du compte a échoué."


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    init_auth_tables()
    email = _normalize_email(email)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not row or not row["is_active"]:
            return None
        candidate, _ = _hash_password(password, row["password_salt"])
        if not hmac.compare_digest(candidate, row["password_hash"]):
            return None
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
        conn.commit()
        user = dict(row)
        user["last_login"] = now
        log_action(user["id"], user["email"], "login")
        return user


def has_permission(user: dict[str, Any] | None, permission: str) -> bool:
    return bool(user and user.get("is_active", 1) and permission in PERMISSIONS.get(user.get("role", "viewer"), set()))


def require_admin(user: dict[str, Any] | None) -> None:
    if not has_permission(user, "manage_users"):
        raise PermissionError("Action réservée à un administrateur.")


def list_users(acting_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    require_admin(acting_user)
    init_auth_tables()
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, first_name, last_name, company, email, role, is_active, created_at, last_login
               FROM users ORDER BY created_at DESC"""
        ).fetchall()
    return [dict(row) for row in rows]


def update_user(user_id: int, role: str, is_active: bool, acting_user: dict[str, Any] | None = None) -> None:
    require_admin(acting_user)
    if role not in ROLES:
        raise ValueError("Rôle invalide")
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ?, is_active = ? WHERE id = ?", (role, int(is_active), user_id))
        conn.commit()
    log_action((acting_user or {}).get("id"), (acting_user or {}).get("email"), "user_updated", f"user_id={user_id};role={role};active={int(is_active)}")


def reset_password(user_id: int, password: str, acting_user: dict[str, Any] | None = None) -> tuple[bool, str]:
    require_admin(acting_user)
    valid, message = validate_password(password)
    if not valid:
        return False, message
    password_hash, salt = _hash_password(password)
    with get_connection() as conn:
        row = conn.execute("SELECT email FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return False, "Utilisateur introuvable."
        conn.execute("UPDATE users SET password_hash=?, password_salt=? WHERE id=?", (password_hash, salt, user_id))
        conn.commit()
    log_action((acting_user or {}).get("id"), (acting_user or {}).get("email"), "password_reset", f"user_id={user_id}")
    return True, "Mot de passe réinitialisé."


def log_action(user_id: int | None, email: str | None, action: str, details: str = "") -> None:
    init_auth_tables()
    with get_connection() as conn:
        conn.execute("INSERT INTO audit_logs(user_id, email, action, details) VALUES (?, ?, ?, ?)", (user_id, email, action, details))
        conn.commit()


def list_audit_logs(limit: int = 200, acting_user: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    require_admin(acting_user)
    init_auth_tables()
    with get_connection() as conn:
        rows = conn.execute("SELECT email, action, details, created_at FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]
