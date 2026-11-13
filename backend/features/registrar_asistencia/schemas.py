"""Esquemas Pydantic del Vertical Slice de Registro de Asistencia por DNI."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.shared.validators import validar_dni_estricto


class RegistrarPresenteRequest(BaseModel):
    dni: str = Field(..., description="DNI del alumno (7 a 10 dígitos numéricos)")
    materia: str = Field(default="Programación III", min_length=2, max_length=80)
    nombre_alumno: Optional[str] = Field(default=None, max_length=100)
    curso: str = Field(default="3° Año - Comisión A", max_length=60)
    observaciones: str = Field(default="Ingreso registrado en término", max_length=240)
    registrado_por: str = Field(default="Docente", max_length=60)
    fecha: Optional[str] = Field(default=None, description="Fecha ISO YYYY-MM-DD (opcional)")
    hora_entrada: Optional[str] = Field(default=None, description="Hora HH:MM:SS (opcional)")

    @field_validator("dni")
    @classmethod
    def check_dni(cls, value: str) -> str:
        return validar_dni_estricto(value)


class MarcarSalidaRequest(BaseModel):
    dni: str = Field(..., description="DNI del alumno para marcar su salida")
    materia: Optional[str] = Field(default=None, max_length=80)
    hora_salida: Optional[str] = Field(default=None, description="Hora HH:MM:SS (opcional)")
    observaciones: Optional[str] = Field(default=None, max_length=240)

    @field_validator("dni")
    @classmethod
    def check_dni(cls, value: str) -> str:
        return validar_dni_estricto(value)


class AsistenciaItemResponse(BaseModel):
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


class RegistroOperacionResponse(BaseModel):
    mensaje: str
    registro: AsistenciaItemResponse

