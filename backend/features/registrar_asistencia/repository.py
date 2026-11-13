"""Acceso a datos del Vertical Slice de Registro de Asistencia por DNI."""

from datetime import datetime
from typing import Optional

from backend.shared.database import ensure_alumno_exists, get_connection

SELECT_ASISTENCIA_JOIN = """
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


def insert_presente(
    dni: str,
    materia: str,
    fecha: str,
    hora_entrada: str,
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
            VALUES (?, ?, 'PRESENTE', ?, ?, NULL, 0, 'NO_APLICA', ?, ?, ?)
            """,
            (dni, materia, fecha, hora_entrada, observaciones, registrado_por, now_iso),
        )
        new_id = cursor.lastrowid
        row = conn.execute(f"{SELECT_ASISTENCIA_JOIN} WHERE a.id = ?", (new_id,)).fetchone()
        return dict(row)


def update_hora_salida(
    dni: str,
    hora_salida: str,
    materia: Optional[str] = None,
    observaciones: Optional[str] = None,
) -> Optional[dict]:
    with get_connection() as conn:
        if materia and materia.strip():
            target = conn.execute(
                """
                SELECT id, observaciones FROM asistencias
                WHERE dni = ? AND materia = ? AND estado IN ('PRESENTE', 'TARDANZA') AND hora_salida IS NULL
                ORDER BY id DESC LIMIT 1
                """,
                (dni, materia.strip()),
            ).fetchone()
        else:
            target = conn.execute(
                """
                SELECT id, observaciones FROM asistencias
                WHERE dni = ? AND estado IN ('PRESENTE', 'TARDANZA') AND hora_salida IS NULL
                ORDER BY id DESC LIMIT 1
                """,
                (dni,),
            ).fetchone()

        if not target:
            return None

        nueva_obs = target["observaciones"]
        if observaciones and observaciones.strip():
            nueva_obs = (
                f"{nueva_obs} | {observaciones.strip()}" if nueva_obs else observaciones.strip()
            )

        conn.execute(
            "UPDATE asistencias SET hora_salida = ?, observaciones = ? WHERE id = ?",
            (hora_salida, nueva_obs, target["id"]),
        )
        row = conn.execute(f"{SELECT_ASISTENCIA_JOIN} WHERE a.id = ?", (target["id"],)).fetchone()
        return dict(row)


def list_asistencias(
    dni: Optional[str] = None,
    materia: Optional[str] = None,
    estado: Optional[str] = None,
    fecha: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    clauses = []
    params: list = []

    if dni and dni.strip():
        clauses.append("a.dni = ?")
        params.append(dni.strip())
    if materia and materia.strip():
        clauses.append("LOWER(a.materia) = LOWER(?)")
        params.append(materia.strip())
    if estado and estado.strip():
        clauses.append("UPPER(a.estado) = UPPER(?)")
        params.append(estado.strip())
    if fecha and fecha.strip():
        clauses.append("a.fecha = ?")
        params.append(fecha.strip())

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"{SELECT_ASISTENCIA_JOIN} {where_sql} ORDER BY a.fecha DESC, a.id DESC LIMIT ?"
    params.append(max(1, min(limit, 500)))

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

