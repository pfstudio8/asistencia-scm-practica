"""Acceso a datos del Vertical Slice de Tardanzas y Ausencias."""

from datetime import datetime
from typing import Optional

from backend.shared.database import ensure_alumno_exists, get_connection

SELECT_INCIDENCIA_SQL = """
SELECT
    a.id,
    a.dni,
    (al.nombre || ' ' || al.apellido) AS nombre_completo,
    al.legajo,
    al.curso,
    a.materia,
    a.estado,
    a.fecha,
    a.hora_entrada,
    a.hora_salida,
    a.minutos_retraso,
    a.justificacion_estado,
    a.observaciones,
    a.registrado_por,
    a.creado_en
FROM asistencias a
JOIN alumnos al ON al.dni = a.dni
"""


def insert_tardanza(
    dni: str,
    materia: str,
    fecha: str,
    hora_entrada: str,
    minutos_retraso: int,
    justificacion_estado: str,
    observaciones: str,
    registrado_por: str,
    nombre_alumno: Optional[str] = None,
    curso: str = "3° Año - Comisión A",
) -> dict:
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        ensure_alumno_exists(conn, dni=dni, nombre_completo=nombre_alumno, curso=curso)
        cursor = conn.execute(
            """
            INSERT INTO asistencias (
                dni, materia, estado, fecha, hora_entrada, hora_salida,
                minutos_retraso, justificacion_estado, observaciones, registrado_por, creado_en
            )
            VALUES (?, ?, 'TARDANZA', ?, ?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                dni,
                materia,
                fecha,
                hora_entrada,
                minutos_retraso,
                justificacion_estado,
                observaciones,
                registrado_por,
                now_iso,
            ),
        )
        row = conn.execute(f"{SELECT_INCIDENCIA_SQL} WHERE a.id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def insert_ausente(
    dni: str,
    materia: str,
    fecha: str,
    justificacion_estado: str,
    observaciones: str,
    registrado_por: str,
    nombre_alumno: Optional[str] = None,
    curso: str = "3° Año - Comisión A",
) -> dict:
    now_iso = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        ensure_alumno_exists(conn, dni=dni, nombre_completo=nombre_alumno, curso=curso)
        cursor = conn.execute(
            """
            INSERT INTO asistencias (
                dni, materia, estado, fecha, hora_entrada, hora_salida,
                minutos_retraso, justificacion_estado, observaciones, registrado_por, creado_en
            )
            VALUES (?, ?, 'AUSENTE', ?, NULL, NULL, 0, ?, ?, ?, ?)
            """,
            (dni, materia, fecha, justificacion_estado, observaciones, registrado_por, now_iso),
        )
        row = conn.execute(f"{SELECT_INCIDENCIA_SQL} WHERE a.id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)


def update_justificacion(
    asistencia_id: int,
    justificacion_estado: str,
    observaciones: Optional[str] = None,
) -> Optional[dict]:
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id, observaciones FROM asistencias WHERE id = ?",
            (asistencia_id,),
        ).fetchone()
        if not existing:
            return None

        obs_final = existing["observaciones"]
        if observaciones is not None and observaciones.strip():
            obs_final = observaciones.strip()

        conn.execute(
            "UPDATE asistencias SET justificacion_estado = ?, observaciones = ? WHERE id = ?",
            (justificacion_estado, obs_final, asistencia_id),
        )
        row = conn.execute(f"{SELECT_INCIDENCIA_SQL} WHERE a.id = ?", (asistencia_id,)).fetchone()
        return dict(row)

