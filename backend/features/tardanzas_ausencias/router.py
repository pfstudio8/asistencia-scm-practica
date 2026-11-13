"""Endpoints HTTP del Vertical Slice de Tardanzas, Ausencias y Justificaciones."""

from fastapi import APIRouter, status

from backend.features.tardanzas_ausencias import service
from backend.features.tardanzas_ausencias.schemas import (
    IncidenciaOperacionResponse,
    RegistrarAusenteRequest,
    RegistrarTardanzaRequest,
    RevisarJustificacionRequest,
)

router = APIRouter(prefix="/api/asistencias", tags=["Tardanzas y Ausencias"])


@router.post(
    "/tardanza",
    response_model=IncidenciaOperacionResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_tardanza_endpoint(payload: RegistrarTardanzaRequest) -> IncidenciaOperacionResponse:
    """Registra una tardanza por DNI con minutos de retraso y estado de justificación."""
    return service.registrar_tardanza(payload)


@router.post(
    "/ausente",
    response_model=IncidenciaOperacionResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_ausente_endpoint(payload: RegistrarAusenteRequest) -> IncidenciaOperacionResponse:
    """Registra una inasistencia/falta por DNI (injustificada, pendiente o justificada)."""
    return service.registrar_ausente(payload)


@router.patch(
    "/{asistencia_id}/justificacion",
    response_model=IncidenciaOperacionResponse,
)
def revisar_justificacion_endpoint(
    asistencia_id: int,
    payload: RevisarJustificacionRequest,
) -> IncidenciaOperacionResponse:
    """Actualiza el estado de revisión de una justificación (PENDIENTE / JUSTIFICADA / INJUSTIFICADA)."""
    return service.actualizar_estado_justificacion(asistencia_id, payload)

