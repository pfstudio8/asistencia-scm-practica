# SICA · Sistema Institucional de Control de Asistencia (v3.0.0)

Sistema web integral de gestión de asistencia académica desarrollado con **Python + FastAPI** bajo arquitectura **Vertical Slicing** en el backend, y **HTML5 + CSS3 + JavaScript (ES Modules) + Framer Motion DOM** en el frontend.

---

## Estructura de Carpetas (Vertical Slicing)

```text
asistencia-scm-practica/
├── backend/
│   ├── app.py                            # Ensamblaje FastAPI, CORS y montaje estático del Frontend
│   ├── shared/                           # Infraestructura transversal mínima
│   │   ├── database.py                   # Conexión SQLite, esquema relacional y datos semilla
│   │   └── validators.py                 # Validación estricta de DNI (heredada de v2.1.0)
│   └── features/                         # VERTICAL SLICES (organizados por capacidad de negocio)
│       ├── auth/                         # Slice 1: Login y Registro de usuarios docentes
│       ├── alumnos/                      # Slice 2: Padrón y alta/edición de alumnos
│       ├── registrar_asistencia/         # Slice 3: Registro por DNI (Presente: Entrada y Salida)
│       ├── tardanzas_ausencias/          # Slice 4: Tardanzas, Ausencias y Justificaciones
│       └── informe_alumno/               # Slice 5: Informe integral por alumno y KPIs de Dashboard
├── frontend/
│   ├── index.html                        # Login/Register, Loader 0.7s, Sidebar y Vistas SPA
│   ├── css/
│   │   └── styles.css                    # Paleta institucional WCAG AAA, colores sólidos puros
│   └── js/
│       ├── motion-engine.js              # Notificaciones sólidas y loaders (~0.7s) con Framer Motion DOM
│       ├── api.js                        # Cliente HTTP hacia los endpoints FastAPI
│       ├── auth.js                       # Flujo Login/Register, bienvenida y localStorage ('username')
│       └── app.js                        # Controlador de Dashboard, Marcación por DNI e Informes
├── tests/
│   ├── test_main.py                      # Pruebas unitarias de compatibilidad v2.1.0
│   └── test_api_slices.py                # Pruebas de integración de todos los Vertical Slices
├── main.py                               # Punto de entrada compatible con uvicorn y CI/CD
├── pytest.ini
├── requirements.txt
└── CHANGELOG.md
```

---

## Ejecución Rápida

1. Activar el entorno virtual o usar directamente el binario en `.venv`:

```powershell
# Iniciar servidor web completo (Frontend + API FastAPI en http://127.0.0.1:8000)
.\.venv\Scripts\python.exe main.py

# O mediante Uvicorn directamente:
.\.venv\Scripts\uvicorn.exe main:app --reload
```

2. Abrir en el navegador:
   - **Aplicación Web**: http://127.0.0.1:8000
   - **Documentación Interactiva Swagger (FastAPI)**: http://127.0.0.1:8000/docs

3. Credenciales de demostración pre-cargadas (o podés crear una cuenta nueva desde **Crear Cuenta**):
   - **Usuario**: `docente.scm`
   - **Contraseña**: `admin123`

4. Ejecutar pruebas automatizadas:

```powershell
.\.venv\Scripts\pytest.exe -v
```

