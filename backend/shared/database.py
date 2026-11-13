"""Gestión de conexión SQLite, inicialización de esquema y datos semilla institucionales."""

import hashlib
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "asistencia.db"


def get_db_path() -> Path:
    """Obtiene la ruta de la base de datos SQLite (configurable vía ASISTENCIA_DB_PATH para tests)."""
    env_path = os.environ.get("ASISTENCIA_DB_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def hash_password(password: str, salt: str | None = None) -> str:
    """Genera un hash seguro PBKDF2-HMAC-SHA256 sin dependencias externas."""
    salt_hex = salt or secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_hex.encode("utf-8"),
        120_000,
    ).hex()
    return f"{salt_hex}${derived}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifica una contraseña contra el hash almacenado."""
    if "$" not in stored_hash:
        return False
    salt_hex, _ = stored_hash.split("$", 1)
    expected = hash_password(password, salt=salt_hex)
    return secrets.compare_digest(expected, stored_hash)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Context manager transaccional para SQLite con soporte de claves foráneas."""
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(seed: bool = True) -> None:
    """Crea las tablas del sistema si no existen y carga datos iniciales de demostración."""
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                nombre_completo TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                rol TEXT NOT NULL DEFAULT 'Docente',
                password_hash TEXT NOT NULL,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alumnos (
                dni TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                legajo TEXT NOT NULL,
                email TEXT DEFAULT '',
                curso TEXT NOT NULL DEFAULT '3° Año - Ing. Software',
                activo INTEGER NOT NULL DEFAULT 1,
                creado_en TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dni TEXT NOT NULL,
                materia TEXT NOT NULL DEFAULT 'Programación III',
                estado TEXT NOT NULL CHECK(estado IN ('PRESENTE', 'TARDANZA', 'AUSENTE')),
                fecha TEXT NOT NULL,
                hora_entrada TEXT,
                hora_salida TEXT,
                minutos_retraso INTEGER NOT NULL DEFAULT 0,
                justificacion_estado TEXT NOT NULL DEFAULT 'NO_APLICA'
                    CHECK(justificacion_estado IN ('NO_APLICA', 'PENDIENTE', 'JUSTIFICADA', 'INJUSTIFICADA')),
                observaciones TEXT NOT NULL DEFAULT '',
                registrado_por TEXT NOT NULL DEFAULT 'Sistema',
                creado_en TEXT NOT NULL,
                FOREIGN KEY (dni) REFERENCES alumnos(dni)
            );

            CREATE INDEX IF NOT EXISTS idx_asistencias_dni ON asistencias(dni);
            CREATE INDEX IF NOT EXISTS idx_asistencias_fecha ON asistencias(fecha);
            CREATE INDEX IF NOT EXISTS idx_asistencias_estado ON asistencias(estado);
            """
        )

        if seed:
            _seed_if_empty(conn)


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Inserta usuario docente inicial, padrón de alumnos y registros base si la BD está vacía."""
    now_iso = datetime.now().isoformat(timespec="seconds")
    today = datetime.now().date()

    user_count = conn.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"]
    if user_count == 0:
        conn.execute(
            """
            INSERT INTO usuarios (username, nombre_completo, email, rol, password_hash, creado_en)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "docente.scm",
                "Prof. Facundo Morales",
                "docente@instituto-scm.edu.ar",
                "Coordinador de Cátedra",
                hash_password("admin123"),
                now_iso,
            ),
        )

    student_count = conn.execute("SELECT COUNT(*) AS total FROM alumnos").fetchone()["total"]
    if student_count == 0:
        alumnos_demo = [
            ("40123456", "Valentina", "Gómez", "LEG-2024-014", "vgomez@alu.scm.edu.ar", "3° Año - Comisión A"),
            ("42876543", "Mateo", "Rodríguez", "LEG-2024-028", "mrodriguez@alu.scm.edu.ar", "3° Año - Comisión A"),
            ("41555890", "Camila", "Fernández", "LEG-2024-031", "cfernandez@alu.scm.edu.ar", "3° Año - Comisión A"),
            ("43910234", "Santiago", "López", "LEG-2024-045", "slopez@alu.scm.edu.ar", "3° Año - Comisión B"),
            ("44102938", "Lucía", "Martínez", "LEG-2024-052", "lmartinez@alu.scm.edu.ar", "3° Año - Comisión B"),
            ("39887654", "Nicolás", "Pereyra", "LEG-2024-067", "npereyra@alu.scm.edu.ar", "3° Año - Comisión B"),
        ]
        conn.executemany(
            """
            INSERT INTO alumnos (dni, nombre, apellido, legajo, email, curso, activo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            [(*al, now_iso) for al in alumnos_demo],
        )

    attendance_count = conn.execute("SELECT COUNT(*) AS total FROM asistencias").fetchone()["total"]
    if attendance_count == 0:
        d0 = today.isoformat()
        d1 = (today - timedelta(days=1)).isoformat()
        d2 = (today - timedelta(days=2)).isoformat()
        d3 = (today - timedelta(days=3)).isoformat()

        registros_demo = [
            ("40123456", "Programación III", "PRESENTE", d3, "18:02:10", "21:30:00", 0, "NO_APLICA", "Ingreso puntual", "docente.scm"),
            ("40123456", "Gestión de Configuración (SCM)", "PRESENTE", d2, "18:00:45", "21:25:12", 0, "NO_APLICA", "Asistencia completa", "docente.scm"),
            ("40123456", "Programación III", "TARDANZA", d1, "18:22:00", "21:30:00", 22, "PENDIENTE", "Demora en transporte público", "docente.scm"),
            ("40123456", "Bases de Datos II", "PRESENTE", d0, "18:04:15", None, 0, "NO_APLICA", "En aula - cursando", "docente.scm"),
            ("42876543", "Programación III", "PRESENTE", d2, "17:58:30", "21:28:00", 0, "NO_APLICA", "Ingreso puntual", "docente.scm"),
            ("42876543", "Bases de Datos II", "PRESENTE", d0, "18:01:20", None, 0, "NO_APLICA", "En laboratorio", "docente.scm"),
            ("41555890", "Programación III", "TARDANZA", d0, "18:19:40", None, 19, "PENDIENTE", "Presentó constancia laboral a revisar", "docente.scm"),
            ("43910234", "Programación III", "AUSENTE", d1, None, None, 0, "INJUSTIFICADA", "Sin aviso previo", "docente.scm"),
            ("43910234", "Bases de Datos II", "AUSENTE", d0, None, None, 0, "INJUSTIFICADA", "Inasistencia sin certificado", "docente.scm"),
            ("44102938", "Gestión de Configuración (SCM)", "PRESENTE", d1, "18:03:11", "21:20:00", 0, "NO_APLICA", "Práctica aprobada", "docente.scm"),
            ("39887654", "Bases de Datos II", "TARDANZA", d1, "18:27:00", "21:15:00", 27, "JUSTIFICADA", "Certificado médico validado", "docente.scm"),
        ]
        conn.executemany(
            """
            INSERT INTO asistencias (
                dni, materia, estado, fecha, hora_entrada, hora_salida,
                minutos_retraso, justificacion_estado, observaciones, registrado_por, creado_en
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [(*reg, now_iso) for reg in registros_demo],
        )


def ensure_alumno_exists(
    conn: sqlite3.Connection,
    dni: str,
    nombre_completo: str | None = None,
    curso: str = "3° Año - Comisión A",
) -> dict:
    """
    Garantiza que exista un registro en `alumnos` para el DNI indicado.
    Si el DNI es nuevo y válido, lo registra automáticamente en el padrón para permitir
    la marcación directa por DNI sin fricción.
    """
    row = conn.execute("SELECT * FROM alumnos WHERE dni = ?", (dni,)).fetchone()
    if row:
        return dict(row)

    if nombre_completo and nombre_completo.strip():
        partes = nombre_completo.strip().split(" ", 1)
        nombre = partes[0]
        apellido = partes[1] if len(partes) > 1 else "(Registrado por DNI)"
    else:
        nombre = "Alumno"
        apellido = f"DNI {dni}"

    legajo = f"LEG-{datetime.now().year}-{dni[-4:]}"
    now_iso = datetime.now().isoformat(timespec="seconds")

    conn.execute(
        """
        INSERT INTO alumnos (dni, nombre, apellido, legajo, email, curso, activo, creado_en)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (dni, nombre, apellido, legajo, f"alu.{dni}@scm.edu.ar", curso, now_iso),
    )
    created = conn.execute("SELECT * FROM alumnos WHERE dni = ?", (dni,)).fetchone()
    return dict(created)

