"""Endpoints HTTP del Vertical Slice de Autenticación."""

from fastapi import APIRouter, status

from backend.features.auth import service
from backend.features.auth.schemas import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_endpoint(payload: RegisterRequest) -> AuthResponse:
    """Registra un nuevo usuario institucional (Docente / Preceptor / Coordinador)."""
    return service.registrar_usuario(payload)


@router.post("/login", response_model=AuthResponse)
def login_endpoint(payload: LoginRequest) -> AuthResponse:
    """Autentica las credenciales del usuario y devuelve su perfil público."""
    return service.iniciar_sesion(payload)

