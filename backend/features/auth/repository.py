"""Acceso a datos del Vertical Slice de Autenticación."""

from datetime import datetime
from typing import Optional

from backend.shared.database import get_connection


def find_user_by_username_or_email(identifier: str) -> Optional[dict]:
    ident_clean = identifier.strip()
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, username, nombre_completo, email, rol, password_hash, creado_en
            FROM usuarios
            WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)
            """,
            (ident_clean, ident_clean),
        ).fetchone()
        return dict(row) if row else None


def username_exists(username: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM usuarios WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        ).fetchone()
        return row is not None


def email_exists(email: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM usuarios WHERE LOWER(email) = LOWER(?)",
            (email.strip(),),
        ).fetchone()
        return row is not None


def insert_user(
    username: str,
    nombre_completo: str,
    email: str,
    rol: str,
    password_hash: str,
) -> dict:
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO usuarios (username, nombre_completo, email, rol, password_hash, creado_en)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, nombre_completo.strip(), email, rol.strip() or "Docente", password_hash, now_iso),
        )
        user_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, username, nombre_completo, email, rol, creado_en FROM usuarios WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row)

