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


def find_open_attendance(
    dni: str,
    fecha: Optional[str] = None,
    materia: Optional[str] = None,
    asistencia_id: Optional[int] = None,
) -> Optional[dict]:
    """Busca una entrada abierta (sin hora_salida registrada) para un alumno."""
    with get_connection() as conn:
        if asistencia_id:
            row = conn.execute(
                f"{SELECT_ASISTENCIA_JOIN} WHERE a.id = ? AND a.hora_salida IS NULL",
                (asistencia_id,),
            ).fetchone()
            return dict(row) if row else None

        clauses = ["a.dni = ?", "a.estado IN ('PRESENTE', 'TARDANZA')", "a.hora_salida IS NULL"]
        params = [dni.strip()]
        if fecha:
            clauses.append("a.fecha = ?")
            params.append(fecha.strip())
        if materia and materia.strip():
            clauses.append("LOWER(a.materia) = LOWER(?)")
            params.append(materia.strip())

        query = f"{SELECT_ASISTENCIA_JOIN} WHERE {' AND '.join(clauses)} ORDER BY a.fecha DESC, a.id DESC LIMIT 1"
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def update_hora_salida_by_id(
    asistencia_id: int,
    hora_salida: str,
    observaciones: Optional[str] = None,
) -> Optional[dict]:
    """Actualiza la hora de salida de un registro específico."""
    with get_connection() as conn:
        target = conn.execute(
            "SELECT id, observaciones FROM asistencias WHERE id = ?",
            (asistencia_id,),
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
            (hora_salida, nueva_obs, asistencia_id),
        )
        row = conn.execute(f"{SELECT_ASISTENCIA_JOIN} WHERE a.id = ?", (asistencia_id,)).fetchone()
        return dict(row) if row else None


def update_hora_salida(
    dni: str,
    hora_salida: str,
    materia: Optional[str] = None,
    observaciones: Optional[str] = None,
    fecha: Optional[str] = None,
    asistencia_id: Optional[int] = None,
) -> Optional[dict]:
    target = find_open_attendance(
        dni=dni,
        fecha=fecha,
        materia=materia,
        asistencia_id=asistencia_id,
    )
    if not target:
        return None
    return update_hora_salida_by_id(
        asistencia_id=target["id"],
        hora_salida=hora_salida,
        observaciones=observaciones,
    )


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

