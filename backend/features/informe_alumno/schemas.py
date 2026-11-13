"""Esquemas Pydantic del Vertical Slice de Informe de Asistencia por Alumno."""

from typing import Optional

from pydantic import BaseModel


class AlumnoResumenInfo(BaseModel):
    dni: str
    nombre: str
    apellido: str
    nombre_completo: str
    legajo: str
    email: str
    curso: str


class MetricasAlumno(BaseModel):
    total_registros: int
    presentes: int
    tardanzas: int
    ausentes: int
    faltas_injustificadas: int
    justificaciones_pendientes: int
    salidas_registradas: int
    porcentaje_asistencia: float
    condicion_academica: str


class MateriaResumen(BaseModel):
    materia: str
    total: int
    presentes: int
    tardanzas: int
    ausentes: int
    porcentaje_asistencia: float


class HistorialAlumnoItem(BaseModel):
    id: int
    dni: str
    nombre_completo: str
    legajo: str
    materia: str
    estado: str
    fecha: str
    hora_entrada: Optional[str] = None
    hora_salida: Optional[str] = None
    minutos_retraso: int
    justificacion_estado: str
    observaciones: str
    registrado_por: str


class InformeAlumnoResponse(BaseModel):
    alumno: AlumnoResumenInfo
    metricas: MetricasAlumno
    desglose_por_materia: list[MateriaResumen]
    historial: list[HistorialAlumnoItem]


class DashboardResumenResponse(BaseModel):
    total_registros: int
    presentes: int
    tardanzas: int
    ausentes: int
    justificaciones_pendientes: int
    faltas_injustificadas: int
    total_alumnos: int
    tasa_asistencia_global: float
    por_materia: list[MateriaResumen]
    pendientes_revision: list[HistorialAlumnoItem]
    actividad_reciente: list[HistorialAlumnoItem]

