"""Acceso a datos del Vertical Slice de Informe de Asistencia por Alumno."""

from typing import Optional

from backend.shared.database import get_connection


def fetch_alumno_by_dni(dni: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM alumnos WHERE dni = ?", (dni,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["nombre_completo"] = f"{d['nombre']} {d['apellido']}".strip()
        return d


def fetch_historial_by_dni(dni: str) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT
                a.id,
                a.dni,
                (al.nombre || ' ' || al.apellido) AS nombre_completo,
                al.legajo,
                a.materia,
                a.estado,
                a.fecha,
                a.hora_entrada,
                a.hora_salida,
                a.minutos_retraso,
                a.justificacion_estado,
                a.observaciones,
                a.registrado_por
            FROM asistencias a
            JOIN alumnos al ON al.dni = a.dni
            WHERE a.dni = ?
            ORDER BY a.fecha DESC, a.id DESC
            """,
            (dni,),
        ).fetchall()
        return [dict(r) for r in rows]


def fetch_dashboard_raw_data() -> dict:
    with get_connection() as conn:
        total_alumnos = conn.execute("SELECT COUNT(*) AS c FROM alumnos").fetchone()["c"]
        all_rows = conn.execute(
            """
            SELECT
                a.id,
                a.dni,
                (al.nombre || ' ' || al.apellido) AS nombre_completo,
                al.legajo,
                a.materia,
                a.estado,
                a.fecha,
                a.hora_entrada,
                a.hora_salida,
                a.minutos_retraso,
                a.justificacion_estado,
                a.observaciones,
                a.registrado_por
            FROM asistencias a
            JOIN alumnos al ON al.dni = a.dni
            ORDER BY a.fecha DESC, a.id DESC
            """
        ).fetchall()
        return {
            "total_alumnos": total_alumnos,
            "registros": [dict(r) for r in all_rows],
        }

