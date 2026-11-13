"""Esquemas Pydantic del Vertical Slice de Alumnos."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from backend.shared.validators import validar_dni_estricto


class AlumnoCreateRequest(BaseModel):
    dni: str = Field(..., description="DNI numérico de 7 a 10 dígitos")
    nombre: str = Field(..., min_length=2, max_length=60)
    apellido: str = Field(..., min_length=2, max_length=60)
    legajo: Optional[str] = Field(default=None, max_length=30)
    email: Optional[str] = Field(default="", max_length=100)
    curso: str = Field(default="3° Año - Comisión A", max_length=60)

    @field_validator("dni")
    @classmethod
    def check_dni(cls, value: str) -> str:
        return validar_dni_estricto(value)


class AlumnoResponse(BaseModel):
    dni: str
    nombre: str
    apellido: str
    nombre_completo: str
    legajo: str
    email: str
    curso: str
    activo: bool
    creado_en: str

