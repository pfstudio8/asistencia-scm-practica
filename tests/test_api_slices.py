"""Pruebas de integración de los Vertical Slices del backend FastAPI y del Frontend estático."""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app import create_app


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Crea una instancia aislada de FastAPI con base SQLite temporal por cada test."""
    test_db = tmp_path / "test_asistencia.db"
    monkeypatch.setenv("ASISTENCIA_DB_PATH", str(test_db))
    application = create_app()
    with TestClient(application) as test_client:
        yield test_client


def test_health_and_frontend_serving(client: TestClient):
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    body = res_health.json()
    assert body["arquitectura"] == "Vertical Slicing"
    assert "registrar_asistencia" in body["slices"]
    assert "tardanzas_ausencias" in body["slices"]
    assert "informe_alumno" in body["slices"]

    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "SICA Institucional" in res_index.text

    res_css = client.get("/css/styles.css")
    assert res_css.status_code == 200
    assert "#0284C7" in res_css.text
    assert "#10B981" in res_css.text


def test_slice_auth_register_and_login(client: TestClient):
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "prof.lopez",
            "nombre_completo": "Ing. Laura López",
            "email": "llopez@instituto-scm.edu.ar",
            "rol": "Docente Titular",
            "password": "claveSegura123",
        },
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["usuario"]["username"] == "prof.lopez"

    login_res = client.post(
        "/api/auth/login",
        json={"username": "prof.lopez", "password": "claveSegura123"},
    )
    assert login_res.status_code == 200
    assert login_res.json()["usuario"]["email"] == "llopez@instituto-scm.edu.ar"

    bad_login = client.post(
        "/api/auth/login",
        json={"username": "prof.lopez", "password": "incorrecta"},
    )
    assert bad_login.status_code == 401


def test_slice_registrar_asistencia_y_salida_por_dni(client: TestClient):
    # Registro con espacios alrededor del DNI (compatible con reglas v2.1.0)
    pres_res = client.post(
        "/api/asistencias/presente",
        json={
            "dni": "  45999888  ",
            "materia": "Programación III",
            "nombre_alumno": "Sofía Benítez",
            "observaciones": "Ingreso puntual",
        },
    )
    assert pres_res.status_code == 201
    registro = pres_res.json()["registro"]
    assert registro["dni"] == "45999888"
    assert registro["estado"] == "PRESENTE"
    assert registro["hora_entrada"] is not None
    assert registro["hora_salida"] is None

    # Marcar salida por DNI
    salida_res = client.post(
        "/api/asistencias/salida",
        json={"dni": "45999888", "hora_salida": "21:30:00"},
    )
    assert salida_res.status_code == 200
    assert salida_res.json()["registro"]["hora_salida"] == "21:30:00"

    # DNI inválido (< 7 dígitos) debe ser rechazado con 422
    invalid_res = client.post(
        "/api/asistencias/presente",
        json={"dni": "12345", "materia": "Programación III"},
    )
    assert invalid_res.status_code == 422


def test_slice_tardanza_ausente_e_informe_por_alumno(client: TestClient):
    dni_test = "46111222"

    # 1. Presente
    r1 = client.post(
        "/api/asistencias/presente",
        json={"dni": dni_test, "materia": "Programación III", "nombre_alumno": "Tomás Silva"},
    )
    assert r1.status_code == 201

    # 2. Tardanza con justificación pendiente
    r2 = client.post(
        "/api/asistencias/tardanza",
        json={
            "dni": dni_test,
            "materia": "Programación III",
            "minutos_retraso": 20,
            "justificacion_estado": "PENDIENTE",
            "observaciones": "Demora en tren",
        },
    )
    assert r2.status_code == 201
    tardanza_id = r2.json()["registro"]["id"]
    assert r2.json()["registro"]["estado"] == "TARDANZA"

    # 3. Ausente injustificado
    r3 = client.post(
        "/api/asistencias/ausente",
        json={
            "dni": dni_test,
            "materia": "Bases de Datos II",
            "justificacion_estado": "INJUSTIFICADA",
            "observaciones": "Sin aviso",
        },
    )
    assert r3.status_code == 201
    assert r3.json()["registro"]["estado"] == "AUSENTE"

    # 4. Consultar Informe de Asistencia por Alumno
    inf_res = client.get(f"/api/informes/alumno/{dni_test}")
    assert inf_res.status_code == 200
    informe = inf_res.json()
    assert informe["alumno"]["dni"] == dni_test
    assert informe["metricas"]["total_registros"] == 3
    assert informe["metricas"]["presentes"] == 1
    assert informe["metricas"]["tardanzas"] == 1
    assert informe["metricas"]["ausentes"] == 1
    assert informe["metricas"]["faltas_injustificadas"] == 1
    assert informe["metricas"]["justificaciones_pendientes"] == 1
    # (1.0 + 0.5 + 0.0) / 3 = 50.0% -> LIBRE
    assert informe["metricas"]["porcentaje_asistencia"] == 50.0
    assert informe["metricas"]["condicion_academica"] == "LIBRE"
    assert len(informe["desglose_por_materia"]) == 2

    # 5. Aprobar la justificación pendiente
    patch_res = client.patch(
        f"/api/asistencias/{tardanza_id}/justificacion",
        json={"justificacion_estado": "JUSTIFICADA"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["registro"]["justificacion_estado"] == "JUSTIFICADA"

