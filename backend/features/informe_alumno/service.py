"""Lógica de negocio del Vertical Slice de Informe de Asistencia por Alumno."""

from collections import defaultdict

from fastapi import HTTPException, status

from backend.features.informe_alumno import repository
from backend.features.informe_alumno.schemas import (
    AlumnoResumenInfo,
    DashboardResumenResponse,
    HistorialAlumnoItem,
    InformeAlumnoResponse,
    MateriaResumen,
    MetricasAlumno,
)
from backend.shared.validators import normalizar_dni


def _calcular_porcentaje_efectivo(presentes: int, tardanzas: int, total: int) -> float:
    """Cálculo académico estándar: Presente = 1.0, Tardanza = 0.5 (media falta), Ausente = 0.0."""
    if total == 0:
        return 100.0
    puntaje = presentes + (tardanzas * 0.5)
    return round((puntaje / total) * 100.0, 1)


def _determinar_condicion(porcentaje: float, total: int) -> str:
    if total == 0:
        return "SIN REGISTROS"
    if porcentaje >= 75.0:
        return "REGULAR"
    if porcentaje >= 60.0:
        return "EN RIESGO"
    return "LIBRE"


def _agrupar_por_materia(registros: list[dict]) -> list[MateriaResumen]:
    grupos: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "presentes": 0, "tardanzas": 0, "ausentes": 0}
    )
    for r in registros:
        mat = r["materia"]
        grupos[mat]["total"] += 1
        if r["estado"] == "PRESENTE":
            grupos[mat]["presentes"] += 1
        elif r["estado"] == "TARDANZA":
            grupos[mat]["tardanzas"] += 1
        elif r["estado"] == "AUSENTE":
            grupos[mat]["ausentes"] += 1

    resultado = []
    for materia, stats in sorted(grupos.items(), key=lambda x: x[0]):
        pct = _calcular_porcentaje_efectivo(stats["presentes"], stats["tardanzas"], stats["total"])
        resultado.append(
            MateriaResumen(
                materia=materia,
                total=stats["total"],
                presentes=stats["presentes"],
                tardanzas=stats["tardanzas"],
                ausentes=stats["ausentes"],
                porcentaje_asistencia=pct,
            )
        )
    return resultado


def generar_informe_por_alumno(dni_raw: str) -> InformeAlumnoResponse:
    dni = normalizar_dni(dni_raw)
    if not dni:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El DNI ingresado no es válido. Debe contener entre 7 y 10 dígitos numéricos.",
        )

    alumno = repository.fetch_alumno_by_dni(dni)
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existen registros para el alumno con DNI {dni}.",
        )

    historial_raw = repository.fetch_historial_by_dni(dni)
    total = len(historial_raw)
    presentes = sum(1 for r in historial_raw if r["estado"] == "PRESENTE")
    tardanzas = sum(1 for r in historial_raw if r["estado"] == "TARDANZA")
    ausentes = sum(1 for r in historial_raw if r["estado"] == "AUSENTE")
    faltas_injust = sum(
        1
        for r in historial_raw
        if r["estado"] == "AUSENTE" and r["justificacion_estado"] == "INJUSTIFICADA"
    )
    justif_pend = sum(1 for r in historial_raw if r["justificacion_estado"] == "PENDIENTE")
    salidas = sum(1 for r in historial_raw if r.get("hora_salida"))

    porcentaje = _calcular_porcentaje_efectivo(presentes, tardanzas, total)
    condicion = _determinar_condicion(porcentaje, total)

    return InformeAlumnoResponse(
        alumno=AlumnoResumenInfo(
            dni=alumno["dni"],
            nombre=alumno["nombre"],
            apellido=alumno["apellido"],
            nombre_completo=alumno["nombre_completo"],
            legajo=alumno["legajo"],
            email=alumno.get("email", ""),
            curso=alumno["curso"],
        ),
        metricas=MetricasAlumno(
            total_registros=total,
            presentes=presentes,
            tardanzas=tardanzas,
            ausentes=ausentes,
            faltas_injustificadas=faltas_injust,
            justificaciones_pendientes=justif_pend,
            salidas_registradas=salidas,
            porcentaje_asistencia=porcentaje,
            condicion_academica=condicion,
        ),
        desglose_por_materia=_agrupar_por_materia(historial_raw),
        historial=[HistorialAlumnoItem(**r) for r in historial_raw],
    )


def obtener_resumen_dashboard() -> DashboardResumenResponse:
    raw = repository.fetch_dashboard_raw_data()
    registros = raw["registros"]
    total = len(registros)
    presentes = sum(1 for r in registros if r["estado"] == "PRESENTE")
    tardanzas = sum(1 for r in registros if r["estado"] == "TARDANZA")
    ausentes = sum(1 for r in registros if r["estado"] == "AUSENTE")
    pendientes_list = [r for r in registros if r["justificacion_estado"] == "PENDIENTE"]
    faltas_injust = sum(
        1
        for r in registros
        if r["estado"] == "AUSENTE" and r["justificacion_estado"] == "INJUSTIFICADA"
    )
    tasa_global = _calcular_porcentaje_efectivo(presentes, tardanzas, total)

    return DashboardResumenResponse(
        total_registros=total,
        presentes=presentes,
        tardanzas=tardanzas,
        ausentes=ausentes,
        justificaciones_pendientes=len(pendientes_list),
        faltas_injustificadas=faltas_injust,
        total_alumnos=raw["total_alumnos"],
        tasa_asistencia_global=tasa_global,
        por_materia=_agrupar_por_materia(registros),
        pendientes_revision=[HistorialAlumnoItem(**r) for r in pendientes_list[:15]],
        actividad_reciente=[HistorialAlumnoItem(**r) for r in registros[:25]],
    )


def obtener_reporte_estadistico_compatible() -> dict:
    """Mantiene compatibilidad estructural con obtener_reporte_estadistico() de v2.1.0."""
    raw = repository.fetch_dashboard_raw_data()
    registros = raw["registros"]
    return {
        "total_asistencias": len(registros),
        "detalle": registros,
    }

