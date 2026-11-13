"""Endpoints HTTP del Vertical Slice de Alumnos."""

from typing import Optional

from fastapi import APIRouter, Query, status

from backend.features.alumnos import service
from backend.features.alumnos.schemas import AlumnoCreateRequest, AlumnoResponse

router = APIRouter(prefix="/api/alumnos", tags=["Padrón de Alumnos"])


@router.get("", response_model=list[AlumnoResponse])
def listar_alumnos_endpoint(
    q: Optional[str] = Query(default=None, description="Filtrar por DNI, nombre, apellido o legajo"),
) -> list[AlumnoResponse]:
    """Devuelve el padrón de alumnos con búsqueda opcional."""
    return service.listar_alumnos(q=q)


@router.get("/{dni}", response_model=AlumnoResponse)
def obtener_alumno_endpoint(dni: str) -> AlumnoResponse:
    """Consulta los datos de un alumno específico por su DNI."""
    return service.obtener_alumno_por_dni(dni)


@router.post("", response_model=AlumnoResponse, status_code=status.HTTP_201_CREATED)
def crear_alumno_endpoint(payload: AlumnoCreateRequest) -> AlumnoResponse:
    """Da de alta o actualiza un alumno en el padrón institucional."""
    return service.registrar_o_actualizar_alumno(payload)

