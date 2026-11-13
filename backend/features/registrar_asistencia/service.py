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
from backend.shared.database import find_asistencia_duplicada


def registrar_entrada_presente(payload: RegistrarPresenteRequest) -> RegistroOperacionResponse:
    now = datetime.now()
    fecha = payload.fecha or now.date().isoformat()
    hora_entrada = payload.hora_entrada or now.strftime("%H:%M:%S")
    materia = payload.materia.strip() or "Programación III"

    # Validación 2: Prevenir registros duplicados o estados contradictorios en el mismo día
    existente = find_asistencia_duplicada(payload.dni, materia, fecha)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El alumno con DNI {payload.dni} ya registra asistencia "
                f"({existente['estado']}) para '{materia}' en la fecha {fecha}."
            ),
        )

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
    now = datetime.now()
    fecha = payload.fecha or now.date().isoformat()
    hora_salida = payload.hora_salida or now.strftime("%H:%M:%S")

    # Validación 3A: Buscar la entrada abierta correspondiente (priorizando la fecha o ID especificado)
    target = repository.find_open_attendance(
        dni=payload.dni,
        fecha=fecha,
        materia=payload.materia,
        asistencia_id=payload.asistencia_id,
    )
    if not target:
        # Verificar si hay una entrada abierta de otra fecha para informar claramente
        otra_fecha = repository.find_open_attendance(
            dni=payload.dni,
            fecha=None,
            materia=payload.materia,
            asistencia_id=payload.asistencia_id,
        )
        if otra_fecha:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No existe entrada abierta para DNI {payload.dni} en la fecha indicada ({fecha}). "
                    f"Existe un ingreso sin salida del día {otra_fecha['fecha']}."
                ),
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No existe una entrada abierta (sin salida marcada) para el DNI {payload.dni}. "
                "Registrá primero el ingreso del alumno."
            ),
        )

    # Validación 3B: Verificar que hora_salida sea estrictamente posterior a hora_entrada
    hora_entrada = target.get("hora_entrada")
    if hora_entrada and hora_salida <= hora_entrada:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Inconsistencia horaria: la hora de salida ({hora_salida}) no puede ser anterior "
                f"o igual a la hora de entrada ({hora_entrada})."
            ),
        )

    updated = repository.update_hora_salida_by_id(
        asistencia_id=target["id"],
        hora_salida=hora_salida,
        observaciones=payload.observaciones,
    )
    return RegistroOperacionResponse(
        mensaje=f"Salida marcada a las {hora_salida} para DNI {payload.dni} ({updated['materia']}).",
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

