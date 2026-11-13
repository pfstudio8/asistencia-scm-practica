# Changelog
## [1.1.0] - 2026-09-03
### Added
- Acumulador y contador global de asistencias en tiempo de ejecucion.
## [1.0.1] - 2026-08-20
### Fixed
- Eliminacion de espacios en blanco en el DNI escaneado.
## [1.0.0] - 2026-08-01
### Added
- Lanzamiento inicial con validacion basica de DNI.
## [2.0.1] - 2026-09-10
### Fixed
- Manejo de excepciones y validación de tipos nulos para el campo DNI en `registrar_asistencia`.
## [2.1.0] - 2026-09-10
### Added
- Función `obtener_reporte_estadistico` para extraer resumen de métricas e historial de asistencias.
## [3.0.0] - 2026-11-05
### Added
- Sistema Web completo de Asistencia con Backend **FastAPI** estructurado bajo **Vertical Slicing** (`auth`, `alumnos`, `registrar_asistencia`, `tardanzas_ausencias`, `informe_alumno`) y persistencia SQLite.
- Endpoints REST para registrar entrada/salida por DNI, tardanzas, ausencias, revisión de justificaciones e informe integral por alumno.
- Frontend en HTML, CSS y JS con paleta institucional WCAG AAA, tipografías `Sora` y `Plus Jakarta Sans`, Dashboard interactiva, Login/Register con loaders sólidos de ~0.7s, persistencia de `username` en `localStorage` y notificaciones sólidas animadas con Framer Motion DOM (sin glassmorphism ni fades).
## [3.0.1] - 2026-11-13
### Fixed
- Corrección de cálculo académico: las incidencias con justificación aprobada (`JUSTIFICADA`) computan efectivamente en la regularidad y porcentaje de asistencia.
- Validación de unicidad: bloqueo de registros duplicados o estados contradictorios (Presente y Ausente) para un mismo alumno en la misma materia y fecha (HTTP 409 Conflict).
- Control de horario y fecha de salida: validación cronológica estricta (`hora_salida > hora_entrada`) y vinculación directa al registro del día o ID específico.