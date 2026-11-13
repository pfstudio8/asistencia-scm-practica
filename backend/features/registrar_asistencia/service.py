"""Lógica de negocio del Vertical Slice de Registro de Asistencia por DNI."""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from backend.features.registrar_asistencia import repository
from backend.features.registrar_asistencia.schemas import (
    AsistenciaItemResponse,
    MarcarSalidaRequest,
    RegistrarPresenteRequest,
    RegistroOperacionResponse,
)


def registrar_entrada_presente(payload: RegistrarPresenteRequest) -> RegistroOperacionResponse:
    now = datetime.now()
    fecha = payload.fecha or now.date().isoformat()
    hora_entrada = payload.hora_entrada or now.strftime("%H:%M:%S")
    materia = payload.materia.strip() or "Programación III"

    created = repository.insert_presente(
        dni=payload.dni,
        materia=materia,
        fecha=fecha,
        hora_entrada=hora_entrada,
        observaciones=payload.observaciones.strip(),
        registrado_por=payload.registrado_por.strip() or "Docente",
        nombre_alumno=payload.nombre_alumno,
        curso=payload.curso,
    )
    return RegistroOperacionResponse(
        mensaje=f"Entrada registrada exitosamente para DNI {payload.dni} ({created['nombre_completo']}).",
        registro=AsistenciaItemResponse(**created),
    )


def marcar_salida_por_dni(payload: MarcarSalidaRequest) -> RegistroOperacionResponse:
    hora_salida = payload.hora_salida or datetime.now().strftime("%H:%M:%S")
    updated = repository.update_hora_salida(
        dni=payload.dni,
        hora_salida=hora_salida,
        materia=payload.materia,
        observaciones=payload.observaciones,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No existe una entrada abierta (sin salida marcada) para el DNI {payload.dni}. "
                "Registrá primero el ingreso del alumno."
            ),
        )
    return RegistroOperacionResponse(
        mensaje=f"Salida marcada a las {hora_salida} para DNI {payload.dni}.",
        registro=AsistenciaItemResponse(**updated),
    )


def consultar_asistencias(
    dni: Optional[str] = None,
    materia: Optional[str] = None,
    estado: Optional[str] = None,
    fecha: Optional[str] = None,
    limit: int = 100,
) -> list[AsistenciaItemResponse]:
    items = repository.list_asistencias(
        dni=dni,
        materia=materia,
        estado=estado,
        fecha=fecha,
        limit=limit,
    )
    return [AsistenciaItemResponse(**item) for item in items]

