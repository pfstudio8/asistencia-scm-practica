"""Endpoints HTTP del Vertical Slice de Registro de Asistencia por DNI."""

from typing import Optional

from fastapi import APIRouter, Query, status

from backend.features.registrar_asistencia import service
from backend.features.registrar_asistencia.schemas import (
    AsistenciaItemResponse,
    MarcarSalidaRequest,
    RegistrarPresenteRequest,
    RegistroOperacionResponse,
)

router = APIRouter(prefix="/api/asistencias", tags=["Registro de Asistencia por DNI"])


@router.post(
    "/presente",
    response_model=RegistroOperacionResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_presente_endpoint(payload: RegistrarPresenteRequest) -> RegistroOperacionResponse:
    """Registra la entrada (estado PRESENTE) de un alumno mediante su DNI."""
    return service.registrar_entrada_presente(payload)


@router.post("/salida", response_model=RegistroOperacionResponse)
def marcar_salida_endpoint(payload: MarcarSalidaRequest) -> RegistroOperacionResponse:
    """Marca la hora de salida sobre la última asistencia abierta del DNI indicado."""
    return service.marcar_salida_por_dni(payload)


@router.get("", response_model=list[AsistenciaItemResponse])
def listar_asistencias_endpoint(
    dni: Optional[str] = Query(default=None),
    materia: Optional[str] = Query(default=None),
    estado: Optional[str] = Query(default=None, description="PRESENTE | TARDANZA | AUSENTE"),
    fecha: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AsistenciaItemResponse]:
    """Obtiene el historial de asistencias filtrable por DNI, materia, estado o fecha."""
    return service.consultar_asistencias(
        dni=dni,
        materia=materia,
        estado=estado,
        fecha=fecha,
        limit=limit,
    )

