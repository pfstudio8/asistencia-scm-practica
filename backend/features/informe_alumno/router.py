"""Endpoints HTTP del Vertical Slice de Informe de Asistencia por Alumno."""

from fastapi import APIRouter

from backend.features.informe_alumno import service
from backend.features.informe_alumno.schemas import (
    DashboardResumenResponse,
    InformeAlumnoResponse,
)

router = APIRouter(prefix="/api/informes", tags=["Informes y Métricas de Asistencia"])


@router.get("/alumno/{dni}", response_model=InformeAlumnoResponse)
def informe_por_alumno_endpoint(dni: str) -> InformeAlumnoResponse:
    """Genera el informe integral de asistencia, condición académica e historial de un alumno por su DNI."""
    return service.generar_informe_por_alumno(dni)


@router.get("/dashboard", response_model=DashboardResumenResponse)
def resumen_dashboard_endpoint() -> DashboardResumenResponse:
    """Obtiene los KPIs consolidados, distribución por materia y actividad reciente para la Dashboard."""
    return service.obtener_resumen_dashboard()


@router.get("/estadistico")
def reporte_estadistico_endpoint() -> dict:
    """Endpoint compatible con obtener_reporte_estadistico() del módulo original."""
    return service.obtener_reporte_estadistico_compatible()

