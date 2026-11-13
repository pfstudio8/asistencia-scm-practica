"""Aplicación principal FastAPI ensamblando los Vertical Slices y el Frontend estático."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.features.alumnos.router import router as alumnos_router
from backend.features.auth.router import router as auth_router
from backend.features.informe_alumno.router import router as informes_router
from backend.features.registrar_asistencia.router import router as asistencia_router
from backend.features.tardanzas_ausencias.router import router as incidencias_router
from backend.shared.database import init_database

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Inicializa el esquema SQLite y datos semilla al levantar FastAPI."""
    init_database(seed=True)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Sistema Institucional de Control de Asistencia",
        description=(
            "API REST construida con FastAPI bajo arquitectura Vertical Slicing. "
            "Permite registrar asistencia por DNI (Presente / Entrada / Salida), "
            "registrar tardanzas y ausencias, gestionar justificaciones y emitir "
            "informes integrales de asistencia por alumno."
        ),
        version="3.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registro de Vertical Slices
    application.include_router(auth_router)
    application.include_router(alumnos_router)
    application.include_router(asistencia_router)
    application.include_router(incidencias_router)
    application.include_router(informes_router)

    @application.get("/api/health", tags=["Sistema"])
    def health_check() -> dict:
        return {
            "status": "ok",
            "version": "3.0.0",
            "arquitectura": "Vertical Slicing",
            "slices": [
                "auth",
                "alumnos",
                "registrar_asistencia",
                "tardanzas_ausencias",
                "informe_alumno",
            ],
        }

    # Montaje de recursos estáticos del Frontend (HTML, CSS, JS)
    if FRONTEND_DIR.exists():
        css_dir = FRONTEND_DIR / "css"
        js_dir = FRONTEND_DIR / "js"
        if css_dir.exists():
            application.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
        if js_dir.exists():
            application.mount("/js", StaticFiles(directory=str(js_dir)), name="js")

        @application.get("/", include_in_schema=False)
        def serve_index():
            return FileResponse(str(FRONTEND_DIR / "index.html"))

    return application


app = create_app()

