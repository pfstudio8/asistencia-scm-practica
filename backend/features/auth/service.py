"""Lógica de negocio del Vertical Slice de Autenticación."""

from fastapi import HTTPException, status

from backend.features.auth import repository
from backend.features.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserProfile
from backend.shared.database import hash_password, verify_password


def registrar_usuario(payload: RegisterRequest) -> AuthResponse:
    if repository.username_exists(payload.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El usuario '{payload.username}' ya se encuentra registrado.",
        )

    if repository.email_exists(payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo '{payload.email}' ya está asociado a otra cuenta.",
        )

    pwd_hash = hash_password(payload.password)
    created = repository.insert_user(
        username=payload.username,
        nombre_completo=payload.nombre_completo,
        email=payload.email,
        rol=payload.rol,
        password_hash=pwd_hash,
    )
    return AuthResponse(
        mensaje="Cuenta creada exitosamente.",
        usuario=UserProfile(**created),
    )


def iniciar_sesion(payload: LoginRequest) -> AuthResponse:
    user = repository.find_user_by_username_or_email(payload.username)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas. Verificá tu usuario y contraseña.",
        )

    user_public = {k: v for k, v in user.items() if k != "password_hash"}
    return AuthResponse(
        mensaje="Sesión iniciada correctamente.",
        usuario=UserProfile(**user_public),
    )

