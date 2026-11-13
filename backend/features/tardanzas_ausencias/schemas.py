"""Esquemas Pydantic del Vertical Slice de Tardanzas y Ausencias."""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from backend.shared.validators import validar_dni_estricto


class RegistrarTardanzaRequest(BaseModel):
    dni: str = Field(..., description="DNI del alumno (7 a 10 dígitos)")
    materia: str = Field(default="Programación III", min_length=2, max_length=80)
    minutos_retraso: int = Field(default=15, ge=1, le=240)
    justificacion_estado: Literal["PENDIENTE", "JUSTIFICADA", "INJUSTIFICADA", "NO_APLICA"] = Field(
        default="PENDIENTE"
    )
    observaciones: str = Field(default="Ingreso con retraso registrado", max_length=240)
    nombre_alumno: Optional[str] = Field(default=None, max_length=100)
    curso: str = Field(default="3° Año - Comisión A", max_length=60)
    registrado_por: str = Field(default="Docente", max_length=60)
    fecha: Optional[str] = Field(default=None)
    hora_entrada: Optional[str] = Field(default=None)

    @field_validator("dni")
    @classmethod
    def check_dni(cls, value: str) -> str:
        return validar_dni_estricto(value)


class RegistrarAusenteRequest(BaseModel):
    dni: str = Field(..., description="DNI del alumno ausente (7 a 10 dígitos)")
    materia: str = Field(default="Programación III", min_length=2, max_length=80)
    justificacion_estado: Literal["INJUSTIFICADA", "PENDIENTE", "JUSTIFICADA"] = Field(
        default="INJUSTIFICADA"
    )
    observaciones: str = Field(default="Ausencia sin aviso previo", max_length=240)
    nombre_alumno: Optional[str] = Field(default=None, max_length=100)
    curso: str = Field(default="3° Año - Comisión A", max_length=60)
    registrado_por: str = Field(default="Docente", max_length=60)
    fecha: Optional[str] = Field(default=None)

    @field_validator("dni")
    @classmethod
    def check_dni(cls, value: str) -> str:
        return validar_dni_estricto(value)


class RevisarJustificacionRequest(BaseModel):
    justificacion_estado: Literal["PENDIENTE", "JUSTIFICADA", "INJUSTIFICADA"]
    observaciones: Optional[str] = Field(default=None, max_length=240)


class IncidenciaRecordResponse(BaseModel):
    id: int
    dni: str
    nombre_completo: str
    legajo: str
    curso: str
    materia: str
    estado: str
    fecha: str
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    minutos_retraso: int
    justificacion_estado: str
    observaciones: str
    registrado_por: str
    creado_en: str


class IncidenciaOperacionResponse(BaseModel):
    mensaje: str
    registro: IncidenciaRecordResponse

