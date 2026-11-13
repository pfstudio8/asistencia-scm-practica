"""Lógica de negocio del Vertical Slice de Tardanzas y Ausencias."""

from datetime import datetime

from fastapi import HTTPException, status

from backend.features.tardanzas_ausencias import repository
from backend.features.tardanzas_ausencias.schemas import (
    IncidenciaOperacionResponse,
    IncidenciaRecordResponse,
    RegistrarAusenteRequest,
    RegistrarTardanzaRequest,
    RevisarJustificacionRequest,
)
from backend.shared.database import find_asistencia_duplicada


def registrar_tardanza(payload: RegistrarTardanzaRequest) -> IncidenciaOperacionResponse:
    now = datetime.now()
    fecha = payload.fecha or now.date().isoformat()
    hora_entrada = payload.hora_entrada or now.strftime("%H:%M:%S")
    materia = payload.materia.strip() or "Programación III"

    # Prevenir registros duplicados o contradictorios en el mismo día
    existente = find_asistencia_duplicada(payload.dni, materia, fecha)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El alumno con DNI {payload.dni} ya registra asistencia "
                f"({existente['estado']}) para '{materia}' en la fecha {fecha}."
            ),
        )

    created = repository.insert_tardanza(
        dni=payload.dni,
        materia=materia,
        fecha=fecha,
        hora_entrada=hora_entrada,
        minutos_retraso=payload.minutos_retraso,
        justificacion_estado=payload.justificacion_estado,
        observaciones=payload.observaciones.strip(),
        registrado_por=payload.registrado_por.strip() or "Docente",
        nombre_alumno=payload.nombre_alumno,
        curso=payload.curso,
    )
    return IncidenciaOperacionResponse(
        mensaje=(
            f"Tardanza (+{payload.minutos_retraso} min) registrada para DNI {payload.dni} "
            f"({created['nombre_completo']})."
        ),
        registro=IncidenciaRecordResponse(**created),
    )


def registrar_ausente(payload: RegistrarAusenteRequest) -> IncidenciaOperacionResponse:
    fecha = payload.fecha or datetime.now().date().isoformat()
    materia = payload.materia.strip() or "Programación III"

    # Prevenir registros duplicados o contradictorios en el mismo día
    existente = find_asistencia_duplicada(payload.dni, materia, fecha)
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"El alumno con DNI {payload.dni} ya registra asistencia "
                f"({existente['estado']}) para '{materia}' en la fecha {fecha}."
            ),
        )

    created = repository.insert_ausente(
        dni=payload.dni,
        materia=materia,
        fecha=fecha,
        justificacion_estado=payload.justificacion_estado,
        observaciones=payload.observaciones.strip(),
        registrado_por=payload.registrado_por.strip() or "Docente",
        nombre_alumno=payload.nombre_alumno,
        curso=payload.curso,
    )
    return IncidenciaOperacionResponse(
        mensaje=f"Ausencia ({payload.justificacion_estado.lower()}) registrada para DNI {payload.dni}.",
        registro=IncidenciaRecordResponse(**created),
    )


def actualizar_estado_justificacion(
    asistencia_id: int,
    payload: RevisarJustificacionRequest,
) -> IncidenciaOperacionResponse:
    updated = repository.update_justificacion(
        asistencia_id=asistencia_id,
        justificacion_estado=payload.justificacion_estado,
        observaciones=payload.observaciones,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró el registro de asistencia N°{asistencia_id}.",
        )
    return IncidenciaOperacionResponse(
        mensaje=f"Justificación actualizada a {payload.justificacion_estado}.",
        registro=IncidenciaRecordResponse(**updated),
    )

