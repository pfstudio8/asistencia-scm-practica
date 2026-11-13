"""Lógica de negocio del Vertical Slice de Alumnos."""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from backend.features.alumnos import repository
from backend.features.alumnos.schemas import AlumnoCreateRequest, AlumnoResponse
from backend.shared.validators import normalizar_dni


def listar_alumnos(q: Optional[str] = None) -> list[AlumnoResponse]:
    items = repository.list_all_alumnos(search=q)
    return [AlumnoResponse(**item) for item in items]


def obtener_alumno_por_dni(dni_raw: str) -> AlumnoResponse:
    dni = normalizar_dni(dni_raw)
    if not dni:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="El DNI debe contener entre 7 y 10 dígitos numéricos.",
        )
    alumno = repository.get_by_dni(dni)
    if not alumno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró un alumno registrado con DNI {dni}.",
        )
    return AlumnoResponse(**alumno)


def registrar_o_actualizar_alumno(payload: AlumnoCreateRequest) -> AlumnoResponse:
    legajo = (payload.legajo or "").strip() or f"LEG-{datetime.now().year}-{payload.dni[-4:]}"
    email = (payload.email or "").strip() or f"alu.{payload.dni}@scm.edu.ar"
    saved = repository.upsert_alumno(
        dni=payload.dni,
        nombre=payload.nombre.strip(),
        apellido=payload.apellido.strip(),
        legajo=legajo,
        email=email,
        curso=payload.curso.strip() or "3° Año - Comisión A",
    )
    return AlumnoResponse(**saved)

