"""Acceso a datos del Vertical Slice de Alumnos."""

from datetime import datetime
from typing import Optional

from backend.shared.database import get_connection


def _map_alumno(row) -> dict:
    d = dict(row)
    d["activo"] = bool(d.get("activo", 1))
    d["nombre_completo"] = f"{d['nombre']} {d['apellido']}".strip()
    return d


def list_all_alumnos(search: Optional[str] = None) -> list[dict]:
    with get_connection() as conn:
        if search and search.strip():
            term = f"%{search.strip()}%"
            rows = conn.execute(
                """
                SELECT * FROM alumnos
                WHERE dni LIKE ?
                   OR LOWER(nombre) LIKE LOWER(?)
                   OR LOWER(apellido) LIKE LOWER(?)
                   OR LOWER(legajo) LIKE LOWER(?)
                ORDER BY apellido ASC, nombre ASC
                """,
                (term, term, term, term),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alumnos ORDER BY apellido ASC, nombre ASC"
            ).fetchall()
        return [_map_alumno(r) for r in rows]


def get_by_dni(dni: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM alumnos WHERE dni = ?", (dni,)).fetchone()
        return _map_alumno(row) if row else None


def upsert_alumno(
    dni: str,
    nombre: str,
    apellido: str,
    legajo: str,
    email: str,
    curso: str,
) -> dict:
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        existing = conn.execute("SELECT dni FROM alumnos WHERE dni = ?", (dni,)).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE alumnos
                SET nombre = ?, apellido = ?, legajo = ?, email = ?, curso = ?
                WHERE dni = ?
                """,
                (nombre, apellido, legajo, email, curso, dni),
            )
        else:
            conn.execute(
                """
                INSERT INTO alumnos (dni, nombre, apellido, legajo, email, curso, activo, creado_en)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (dni, nombre, apellido, legajo, email, curso, now_iso),
            )
        row = conn.execute("SELECT * FROM alumnos WHERE dni = ?", (dni,)).fetchone()
        return _map_alumno(row)

