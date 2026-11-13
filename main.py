# main.py - Sistema Institucional de Asistencia (v3.0.0 - FastAPI + Vertical Slicing)

import os
import sys

from backend.app import app
from backend.shared.validators import normalizar_dni

# Estado en memoria preservado para compatibilidad hacia atrás con tests unitarios v2.1.0
total_asistencias = 0
historial_registros = []


def registrar_asistencia(datos_alumno: dict) -> bool:
    """
    Registra una asistencia validando el DNI (compatible con suite de pruebas v2.1.0).
    Para la API REST completa con persistencia SQLite y Vertical Slicing, usar los endpoints de `app`.
    """
    global total_asistencias, historial_registros

    if not isinstance(datos_alumno, dict):
        return False

    dni = normalizar_dni(datos_alumno.get("dni"))
    if not dni:
        print(f"[ERROR] Datos inválidos o faltantes para DNI: {datos_alumno.get('dni')}")
        return False

    materia = datos_alumno.get("materia", "Programación III")
    total_asistencias += 1
    registro = {"id": total_asistencias, "dni": dni, "materia": materia}
    historial_registros.append(registro)
    print(f"[OK] Asistencia N°{total_asistencias} | DNI: {dni} | Materia: {materia}")
    return True


# NUEVA FUNCIONALIDAD (Compatible hacia atrás con v2.1.0)
def obtener_reporte_estadistico() -> dict:
    return {
        "total_asistencias": total_asistencias,
        "detalle": historial_registros,
    }


if __name__ == "__main__":
    is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
    is_check = "--check" in sys.argv

    if is_ci or is_check:
        print("=== VERIFICACIÓN SISTEMA DE ASISTENCIA v3.0.0 ===")
        registrar_asistencia({"dni": "40123456", "materia": "Programación III"})
        print("Reporte:", obtener_reporte_estadistico())
    else:
        # pyrefly: ignore[missing-import]
        import uvicorn

        port = int(os.environ.get("PORT", "8000"))
        print("==============================================================")
        print("  SISTEMA INSTITUCIONAL DE ASISTENCIA v3.0.0 (FastAPI)")
        print(f"  Aplicación Web disponible en: http://127.0.0.1:{port}")
        print(f"  Documentación OpenAPI / Swagger: http://127.0.0.1:{port}/docs")
        print("==============================================================")
        uvicorn.run("backend.app:app", host="127.0.0.1", port=port, reload=True)
