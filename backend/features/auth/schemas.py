"""Esquemas Pydantic del Vertical Slice de Autenticación."""

from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    nombre_completo: str = Field(..., min_length=3, max_length=80)
    email: str = Field(..., min_length=5, max_length=100)
    rol: str = Field(default="Docente", max_length=50)
    password: str = Field(..., min_length=4, max_length=72)

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, value: str) -> str:
        clean = value.strip()
        if " " in clean:
            raise ValueError("El nombre de usuario no puede contener espacios.")
        return clean

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, value: str) -> str:
        clean = value.strip().lower()
        if "@" not in clean or "." not in clean.split("@")[-1]:
            raise ValueError("Ingresá un correo electrónico institucional válido.")
        return clean


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=4, max_length=72)


class UserProfile(BaseModel):
    id: int
    username: str
    nombre_completo: str
    email: str
    rol: str
    creado_en: str


class AuthResponse(BaseModel):
    mensaje: str
    usuario: UserProfile

