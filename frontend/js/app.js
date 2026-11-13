/**
 * Controlador Principal del Frontend SICA:
 * Dashboard, Registro por DNI (Entrada/Salida/Tardanza/Ausente),
 * Revisión de Justificaciones, Informe por Alumno y Padrón.
 */

import { api } from "./api.js";
import { getStoredUsername, initAuthFlow } from "./auth.js";
import { notify } from "./motion-engine.js";

let cachedAlumnos = [];
let currentStudentReport = null;

/* ==========================================================================
   RELOJ INSTITUCIONAL EN TIEMPO REAL Y FECHA
   ========================================================================== */
function startInstitutionalClock() {
  const clockEl = document.getElementById("live-clock");
  const dateEl = document.getElementById("current-date-label");

  const update = () => {
    const now = new Date();
    if (clockEl) {
      clockEl.textContent = now.toLocaleTimeString("es-AR", { hour12: false });
    }
    if (dateEl) {
      const formattedDate = now.toLocaleDateString("es-AR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      });
      dateEl.textContent = formattedDate.toUpperCase();
    }
  };
  update();
  setInterval(update, 1000);
}

/* ==========================================================================
   NAVEGACIÓN ENTRE VISTAS DE LA SIDEBAR
   ========================================================================== */
function switchView(viewName) {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.view === viewName);
  });
  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.toggle("hidden", sec.id !== `view-${viewName}`);
  });
}

function initNavigation() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const target = btn.dataset.view;
      switchView(target);
      if (target === "dashboard") await refreshDashboard();
      if (target === "registro") await refreshFullAttendanceLog();
      if (target === "alumnos" || target === "informe") await refreshAlumnosDirectory();
    });
  });

  document.getElementById("btn-goto-registro")?.addEventListener("click", async () => {
    switchView("registro");
    await refreshFullAttendanceLog();
  });

  document.getElementById("btn-refresh-all")?.addEventListener("click", async () => {
    await refreshAllData();
    notify({
      type: "info",
      title: "Datos Sincronizados",
      message: "Se actualizaron las métricas y tablas desde el servidor FastAPI.",
      duration: 2400,
    });
  });
}

/* ==========================================================================
   HELPERS DE RENDERIZADO SEGURO Y BADGES SÓLIDOS
   ========================================================================== */
function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderEstadoBadge(estado, minutosRetraso = 0) {
  if (estado === "PRESENTE") {
    return `<span class="status-pill pill-present">✓ PRESENTE</span>`;
  }
  if (estado === "TARDANZA") {
    const extra = minutosRetraso > 0 ? ` (+${minutosRetraso}m)` : "";
    return `<span class="status-pill pill-late">⏱ TARDANZA${extra}</span>`;
  }
  return `<span class="status-pill pill-absent">✕ AUSENTE</span>`;
}

function renderJustificacionBadge(justEstado) {
  if (justEstado === "PENDIENTE") {
    return `<span class="status-pill pill-late">PENDIENTE</span>`;
  }
  if (justEstado === "JUSTIFICADA") {
    return `<span class="status-pill pill-present">JUSTIFICADA</span>`;
  }
  if (justEstado === "INJUSTIFICADA") {
    return `<span class="status-pill pill-absent">INJUSTIFICADA</span>`;
  }
  return `<span class="status-pill pill-neutral">N/A</span>`;
}

function renderCondicionBadge(condicion, el) {
  if (!el) return;
  el.textContent = condicion;
  el.className = "status-pill";
  if (condicion === "REGULAR") el.classList.add("pill-present");
  else if (condicion === "EN RIESGO") el.classList.add("pill-late");
  else if (condicion === "LIBRE") el.classList.add("pill-absent");
  else el.classList.add("pill-blue");
}

/* ==========================================================================
   DASHBOARD GENERAL: KPIs, COBERTURA POR MATERIA, PENDIENTES Y TABLA RECIENTE
   ========================================================================== */
async function refreshDashboard() {
  try {
    const data = await api.obtenerDashboard();

    document.getElementById("kpi-tasa").textContent = `${data.tasa_asistencia_global}%`;
    document.getElementById("kpi-total-registros").textContent = data.total_registros;
    document.getElementById("kpi-presentes").textContent = data.presentes;
    document.getElementById("kpi-tardanzas").textContent = data.tardanzas;
    document.getElementById("kpi-pendientes").textContent = data.justificaciones_pendientes;
    document.getElementById("kpi-ausentes").textContent = data.ausentes;
    document.getElementById("kpi-injustificadas").textContent = data.faltas_injustificadas;
    document.getElementById("kpi-total-alumnos").textContent = data.total_alumnos;
    document.getElementById("pending-badge-count").textContent =
      `${data.justificaciones_pendientes} pendientes`;

    renderMateriaBreakdown("materia-breakdown-list", data.por_materia);
    renderPendingJustifications(data.pendientes_revision);
    renderDashboardRecentTable(data.actividad_reciente);
  } catch (error) {
    notify({
      type: "error",
      title: "Error al cargar Dashboard",
      message: error.message,
    });
  }
}

function renderMateriaBreakdown(containerId, items) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!items || items.length === 0) {
    container.innerHTML = `<div class="empty-state">Sin registros cargados para calcular cobertura.</div>`;
    return;
  }

  container.innerHTML = items
    .map((m) => {
      let barClass = "";
      if (m.porcentaje_asistencia < 60) barClass = "fill-red";
      else if (m.porcentaje_asistencia < 75) barClass = "fill-amber";

      return `
        <div class="materia-item">
          <div class="materia-row-top">
            <span>${escapeHtml(m.materia)}</span>
            <span class="mono-text">${m.porcentaje_asistencia}%</span>
          </div>
          <div class="materia-counts">
            <span>Total: <strong>${m.total}</strong></span>
            <span>Presentes: <strong>${m.presentes}</strong></span>
            <span>Tardanzas: <strong>${m.tardanzas}</strong></span>
            <span>Ausentes: <strong>${m.ausentes}</strong></span>
          </div>
          <div class="solid-progress-track">
            <div class="solid-progress-fill ${barClass}" style="width: ${Math.min(100, m.porcentaje_asistencia)}%"></div>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderPendingJustifications(pendientes) {
  const container = document.getElementById("pending-list-container");
  if (!container) return;

  if (!pendientes || pendientes.length === 0) {
    container.innerHTML = `<div class="empty-state">No hay justificaciones pendientes de revisión en este momento.</div>`;
    return;
  }

  container.innerHTML = pendientes
    .map(
      (item) => `
      <div class="pending-item">
        <div>
          <strong>${escapeHtml(item.nombre_completo)}</strong>
          <span class="mono-text">(DNI ${escapeHtml(item.dni)})</span>
          &nbsp;·&nbsp;
          <span>${escapeHtml(item.materia)}</span>
          &nbsp;·&nbsp;
          <span class="mono-text">${escapeHtml(item.fecha)}</span>
          <div style="font-size:0.84rem; margin-top:3px;">
            ${renderEstadoBadge(item.estado, item.minutos_retraso)}
            &nbsp; Motivo: <em>${escapeHtml(item.observaciones || "Sin detalle")}</em>
          </div>
        </div>
        <div class="pending-actions">
          <button type="button" class="btn btn-success btn-sm" data-approve-id="${item.id}">
            ✓ Aprobar Justificación
          </button>
          <button type="button" class="btn btn-danger btn-sm" data-reject-id="${item.id}">
            ✕ Marcar Injustificada
          </button>
        </div>
      </div>
    `
    )
    .join("");

  container.querySelectorAll("[data-approve-id]").forEach((btn) => {
    btn.addEventListener("click", () =>
      handleJustificationDecision(Number(btn.dataset.approveId), "JUSTIFICADA")
    );
  });
  container.querySelectorAll("[data-reject-id]").forEach((btn) => {
    btn.addEventListener("click", () =>
      handleJustificationDecision(Number(btn.dataset.rejectId), "INJUSTIFICADA")
    );
  });
}

async function handleJustificationDecision(id, nuevoEstado) {
  try {
    const res = await api.revisarJustificacion(id, { justificacion_estado: nuevoEstado });
    notify({
      type: nuevoEstado === "JUSTIFICADA" ? "success" : "error",
      title: "Justificación Actualizada",
      message: res.mensaje,
    });
    await refreshAllData();
  } catch (error) {
    notify({
      type: "error",
      title: "No se pudo actualizar",
      message: error.message,
    });
  }
}

function renderDashboardRecentTable(rows) {
  const tbody = document.getElementById("dashboard-recent-tbody");
  if (!tbody) return;

  if (!rows || rows.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;">Sin registros recientes.</td></tr>`;
    return;
  }

  tbody.innerHTML = rows
    .slice(0, 12)
    .map(
      (r) => `
      <tr>
        <td class="mono-text">#${r.id}</td>
        <td class="mono-text"><strong>${escapeHtml(r.dni)}</strong></td>
        <td>${escapeHtml(r.nombre_completo)}</td>
        <td>${escapeHtml(r.materia)}</td>
        <td class="mono-text">${escapeHtml(r.fecha)}</td>
        <td class="mono-text">${escapeHtml(r.hora_entrada || "—")}</td>
        <td class="mono-text">${escapeHtml(r.hora_salida || "En curso")}</td>
        <td>${renderEstadoBadge(r.estado, r.minutos_retraso)}</td>
        <td>${renderJustificacionBadge(r.justificacion_estado)}</td>
        <td>
          <button type="button" class="btn btn-outline-navy btn-sm" data-open-report="${escapeHtml(r.dni)}">
            Informe
          </button>
        </td>
      </tr>
    `
    )
    .join("");

  tbody.querySelectorAll("[data-open-report]").forEach((btn) => {
    btn.addEventListener("click", () => openStudentReportByDni(btn.dataset.openReport));
  });
}

/* ==========================================================================
   TERMINAL RÁPIDA EN DASHBOARD Y FORMULARIOS OPERATIVOS POR DNI
   ========================================================================== */
function initQuickTerminalAndForms() {
  const quickDniInput = document.getElementById("quick-dni");
  const quickPreview = document.getElementById("quick-student-preview");

  // Previsualización instantánea del alumno al escribir su DNI
  quickDniInput?.addEventListener("input", () => {
    const clean = quickDniInput.value.trim();
    if (clean.length < 7) {
      quickPreview.textContent = "Ingresá un DNI de 7 a 10 dígitos numéricos.";
      quickPreview.classList.remove("found");
      return;
    }
    const found = cachedAlumnos.find((a) => a.dni === clean);
    if (found) {
      quickPreview.textContent = `✓ Alumno identificado: ${found.nombre_completo} (${found.legajo} · ${found.curso})`;
      quickPreview.classList.add("found");
    } else {
      quickPreview.textContent = `DNI válido (${clean}): no figura en padrón, se dará de alta automáticamente al registrar.`;
      quickPreview.classList.remove("found");
    }
  });

  const getQuickValues = () => ({
    dni: document.getElementById("quick-dni").value.trim(),
    materia: document.getElementById("quick-materia").value,
    observaciones: document.getElementById("quick-obs").value.trim(),
    registrado_por: getStoredUsername() || "Docente",
  });

  // Botón Rápido 1: Registrar Entrada (Presente)
  document.getElementById("btn-quick-entrada")?.addEventListener("click", async () => {
    const vals = getQuickValues();
    try {
      const res = await api.registrarPresente({
        dni: vals.dni,
        materia: vals.materia,
        observaciones: vals.observaciones || "Ingreso puntual registrado por DNI",
        registrado_por: vals.registrado_por,
      });
      notify({
        type: "success",
        title: "Entrada Presente Confirmada",
        message: res.mensaje,
      });
      document.getElementById("quick-obs").value = "";
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "DNI o Registro Inválido", message: error.message });
    }
  });

  // Botón Rápido 2: Marcar Salida
  document.getElementById("btn-quick-salida")?.addEventListener("click", async () => {
    const vals = getQuickValues();
    try {
      const res = await api.marcarSalida({
        dni: vals.dni,
        observaciones: vals.observaciones || undefined,
      });
      notify({
        type: "info",
        title: "Horario de Salida Registrado",
        message: res.mensaje,
      });
      document.getElementById("quick-obs").value = "";
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "No se pudo marcar salida", message: error.message });
    }
  });

  // Botón Rápido 3: Marcar Tardanza (#F59E0B)
  document.getElementById("btn-quick-tardanza")?.addEventListener("click", async () => {
    const vals = getQuickValues();
    try {
      const res = await api.registrarTardanza({
        dni: vals.dni,
        materia: vals.materia,
        minutos_retraso: 15,
        justificacion_estado: "PENDIENTE",
        observaciones: vals.observaciones || "Llegada tarde registrada desde terminal rápida",
        registrado_por: vals.registrado_por,
      });
      notify({
        type: "warning",
        title: "Tardanza Registrada",
        message: res.mensaje,
      });
      document.getElementById("quick-obs").value = "";
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "Error al registrar tardanza", message: error.message });
    }
  });

  // Botón Rápido 4: Marcar Ausente (#EF4444)
  document.getElementById("btn-quick-ausente")?.addEventListener("click", async () => {
    const vals = getQuickValues();
    try {
      const res = await api.registrarAusente({
        dni: vals.dni,
        materia: vals.materia,
        justificacion_estado: "INJUSTIFICADA",
        observaciones: vals.observaciones || "Ausencia sin aviso registrada por DNI",
        registrado_por: vals.registrado_por,
      });
      notify({
        type: "error",
        title: "Ausencia Registrada en Acta",
        message: res.mensaje,
      });
      document.getElementById("quick-obs").value = "";
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "Error al registrar ausencia", message: error.message });
    }
  });

  // VISTA 2 - Formulario Presente (Entrada y Salida)
  document.getElementById("form-presente-dni")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const res = await api.registrarPresente({
        dni: document.getElementById("pres-dni").value.trim(),
        materia: document.getElementById("pres-materia").value,
        nombre_alumno: document.getElementById("pres-nombre").value.trim() || null,
        observaciones: document.getElementById("pres-obs").value.trim() || "Ingreso en término",
        registrado_por: getStoredUsername() || "Docente",
      });
      notify({ type: "success", title: "Presente Registrado", message: res.mensaje });
      document.getElementById("pres-dni").value = "";
      document.getElementById("pres-nombre").value = "";
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "Error en Marcación", message: error.message });
    }
  });

  document.getElementById("btn-form-salida")?.addEventListener("click", async () => {
    const dni = document.getElementById("pres-dni").value.trim();
    const obs = document.getElementById("pres-obs").value.trim();
    try {
      const res = await api.marcarSalida({
        dni,
        observaciones: obs !== "Ingreso registrado en término" ? obs : undefined,
      });
      notify({ type: "info", title: "Salida Confirmada", message: res.mensaje });
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "No se pudo marcar salida", message: error.message });
    }
  });

  // VISTA 2 - Selector dinámico Tardanza vs Ausente
  const incTipoSelect = document.getElementById("inc-tipo");
  const groupMinutos = document.getElementById("group-minutos-retraso");
  const btnSubmitInc = document.getElementById("btn-submit-incidencia");
  const incJustSelect = document.getElementById("inc-justificacion");

  incTipoSelect?.addEventListener("change", () => {
    const isAusente = incTipoSelect.value === "AUSENTE";
    groupMinutos.classList.toggle("hidden", isAusente);
    if (isAusente) {
      btnSubmitInc.textContent = "Registrar Ausencia en Actas";
      btnSubmitInc.className = "btn btn-danger btn-block";
      incJustSelect.value = "INJUSTIFICADA";
    } else {
      btnSubmitInc.textContent = "Registrar Tardanza en Actas";
      btnSubmitInc.className = "btn btn-amber btn-block";
      incJustSelect.value = "PENDIENTE";
    }
  });

  document.getElementById("form-incidencia-dni")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const tipo = incTipoSelect.value;
    const dni = document.getElementById("inc-dni").value.trim();
    const materia = document.getElementById("inc-materia").value;
    const justificacion_estado = incJustSelect.value;
    const nombre_alumno = document.getElementById("inc-nombre").value.trim() || null;
    const observaciones = document.getElementById("inc-obs").value.trim();
    const registrado_por = getStoredUsername() || "Docente";

    try {
      if (tipo === "TARDANZA") {
        const minutos_retraso = Number(document.getElementById("inc-minutos").value) || 15;
        const res = await api.registrarTardanza({
          dni,
          materia,
          minutos_retraso,
          justificacion_estado,
          nombre_alumno,
          observaciones,
          registrado_por,
        });
        notify({ type: "warning", title: "Tardanza Asentada", message: res.mensaje });
      } else {
        const res = await api.registrarAusente({
          dni,
          materia,
          justificacion_estado,
          nombre_alumno,
          observaciones,
          registrado_por,
        });
        notify({ type: "error", title: "Ausencia Asentada", message: res.mensaje });
      }
      document.getElementById("inc-dni").value = "";
      document.getElementById("inc-nombre").value = "";
      document.getElementById("inc-obs").value = "";
      await refreshAllData();
    } catch (error) {
      notify({ type: "error", title: "No se pudo registrar incidencia", message: error.message });
    }
  });

  document.getElementById("btn-apply-filters")?.addEventListener("click", refreshFullAttendanceLog);
}

/* ==========================================================================
   PLANILLA GENERAL FILTRABLE (VISTA 2)
   ========================================================================== */
async function refreshFullAttendanceLog() {
  const tbody = document.getElementById("full-log-tbody");
  if (!tbody) return;

  const filters = {
    dni: document.getElementById("filter-dni")?.value || "",
    estado: document.getElementById("filter-estado")?.value || "",
    materia: document.getElementById("filter-materia")?.value || "",
  };

  try {
    const list = await api.listarAsistencias(filters);
    if (list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="11" style="text-align:center;">No se encontraron asistencias con esos criterios.</td></tr>`;
      return;
    }

    tbody.innerHTML = list
      .map((r) => {
        const canMarkExit = (r.estado === "PRESENTE" || r.estado === "TARDANZA") && !r.hora_salida;
        return `
          <tr>
            <td class="mono-text">#${r.id}</td>
            <td class="mono-text"><strong>${escapeHtml(r.dni)}</strong></td>
            <td>${escapeHtml(r.nombre_completo)}</td>
            <td>${escapeHtml(r.materia)}</td>
            <td class="mono-text">${escapeHtml(r.fecha)}</td>
            <td class="mono-text">${escapeHtml(r.hora_entrada || "—")}</td>
            <td class="mono-text">${escapeHtml(r.hora_salida || "—")}</td>
            <td>${renderEstadoBadge(r.estado, r.minutos_retraso)}</td>
            <td>${renderJustificacionBadge(r.justificacion_estado)}</td>
            <td>${escapeHtml(r.observaciones)}</td>
            <td>
              <div style="display:flex; gap:6px;">
                ${
                  canMarkExit
                    ? `<button type="button" class="btn btn-sky btn-sm" data-exit-dni="${escapeHtml(r.dni)}">⇥ Salida</button>`
                    : ""
                }
                <button type="button" class="btn btn-outline-navy btn-sm" data-open-report="${escapeHtml(r.dni)}">Informe</button>
              </div>
            </td>
          </tr>
        `;
      })
      .join("");

    tbody.querySelectorAll("[data-exit-dni]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          const res = await api.marcarSalida({ dni: btn.dataset.exitDni });
          notify({ type: "info", title: "Salida Marcada", message: res.mensaje });
          await refreshAllData();
        } catch (error) {
          notify({ type: "error", title: "Error al marcar salida", message: error.message });
        }
      });
    });

    tbody.querySelectorAll("[data-open-report]").forEach((btn) => {
      btn.addEventListener("click", () => openStudentReportByDni(btn.dataset.openReport));
    });
  } catch (error) {
    notify({ type: "error", title: "Error al consultar planilla", message: error.message });
  }
}

/* ==========================================================================
   INFORME DE ASISTENCIA POR ALUMNO (VISTA 3)
   ========================================================================== */
async function openStudentReportByDni(dni) {
  switchView("informe");
  const input = document.getElementById("report-dni-input");
  if (input) input.value = dni;
  await fetchAndRenderStudentReport(dni);
}

async function fetchAndRenderStudentReport(dni) {
  const container = document.getElementById("report-result-container");
  const exportBtn = document.getElementById("btn-export-report-csv");

  try {
    const report = await api.obtenerInformeAlumno(dni);
    currentStudentReport = report;

    const { alumno, metricas, desglose_por_materia, historial } = report;
    const initials = `${alumno.nombre[0] || ""}${alumno.apellido[0] || ""}`.toUpperCase();

    document.getElementById("rep-initials").textContent = initials || "AL";
    document.getElementById("rep-nombre").textContent = alumno.nombre_completo;
    document.getElementById("rep-dni").textContent = alumno.dni;
    document.getElementById("rep-legajo").textContent = alumno.legajo;
    document.getElementById("rep-curso").textContent = alumno.curso;
    document.getElementById("rep-email").textContent = alumno.email || "Sin correo";
    document.getElementById("rep-pct").textContent = `${metricas.porcentaje_asistencia}%`;

    renderCondicionBadge(
      metricas.condicion_academica,
      document.getElementById("rep-condicion-badge")
    );

    document.getElementById("rep-total").textContent = metricas.total_registros;
    document.getElementById("rep-salidas").textContent = metricas.salidas_registradas;
    document.getElementById("rep-presentes").textContent = metricas.presentes;
    document.getElementById("rep-tardanzas").textContent = metricas.tardanzas;
    document.getElementById("rep-pendientes").textContent = metricas.justificaciones_pendientes;
    document.getElementById("rep-ausentes").textContent = metricas.ausentes;
    document.getElementById("rep-injustificadas").textContent = metricas.faltas_injustificadas;

    renderMateriaBreakdown("rep-materias-list", desglose_por_materia);

    const tbody = document.getElementById("rep-historial-tbody");
    if (historial.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;">El alumno aún no registra asistencias cargadas.</td></tr>`;
    } else {
      tbody.innerHTML = historial
        .map(
          (h) => `
          <tr>
            <td class="mono-text">${escapeHtml(h.fecha)}</td>
            <td><strong>${escapeHtml(h.materia)}</strong></td>
            <td class="mono-text">${escapeHtml(h.hora_entrada || "—")}</td>
            <td class="mono-text">${escapeHtml(h.hora_salida || "—")}</td>
            <td>${renderEstadoBadge(h.estado, h.minutos_retraso)}</td>
            <td class="mono-text">${h.minutos_retraso > 0 ? `${h.minutos_retraso} min` : "0 min"}</td>
            <td>${renderJustificacionBadge(h.justificacion_estado)}</td>
            <td>${escapeHtml(h.observaciones)}</td>
          </tr>
        `
        )
        .join("");
    }

    container.classList.remove("hidden");
    exportBtn.classList.remove("hidden");

    notify({
      type: "info",
      title: "Informe Emitido",
      message: `${alumno.nombre_completo}: ${metricas.porcentaje_asistencia}% de asistencia (${metricas.condicion_academica}).`,
      duration: 3000,
    });
  } catch (error) {
    container.classList.add("hidden");
    exportBtn.classList.add("hidden");
    notify({
      type: "error",
      title: "No se pudo emitir el informe",
      message: error.message,
    });
  }
}

function exportCurrentReportCsv() {
  if (!currentStudentReport) return;
  const { alumno, metricas, historial } = currentStudentReport;

  const lines = [
    ["Alumno", alumno.nombre_completo],
    ["DNI", alumno.dni],
    ["Legajo", alumno.legajo],
    ["Condicion Academica", metricas.condicion_academica],
    ["Porcentaje Asistencia", `${metricas.porcentaje_asistencia}%`],
    [],
    ["Fecha", "Materia", "Entrada", "Salida", "Estado", "Minutos Retraso", "Justificacion", "Observaciones"],
    ...historial.map((h) => [
      h.fecha,
      h.materia,
      h.hora_entrada || "",
      h.hora_salida || "",
      h.estado,
      String(h.minutos_retraso),
      h.justificacion_estado,
      (h.observaciones || "").replace(/,/g, ";"),
    ]),
  ];

  const csvContent = "\uFEFF" + lines.map((row) => row.join(",")).join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `informe_asistencia_${alumno.dni}.csv`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);

  notify({
    type: "success",
    title: "CSV Descargado",
    message: `Se exportó informe_asistencia_${alumno.dni}.csv correctamente.`,
  });
}

function initReportView() {
  document.getElementById("form-search-informe")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const dni = document.getElementById("report-dni-input").value.trim();
    await fetchAndRenderStudentReport(dni);
  });

  document
    .getElementById("btn-export-report-csv")
    ?.addEventListener("click", exportCurrentReportCsv);
}

/* ==========================================================================
   PADRÓN DE ALUMNOS Y CHIPS RÁPIDOS (VISTA 4)
   ========================================================================== */
async function refreshAlumnosDirectory() {
  try {
    cachedAlumnos = await api.listarAlumnos();

    // Renderizar chips rápidos en Informe por Alumno
    const chipsContainer = document.getElementById("student-quick-chips");
    if (chipsContainer) {
      chipsContainer.innerHTML = cachedAlumnos
        .map(
          (a) => `
          <button type="button" class="student-chip" data-chip-dni="${escapeHtml(a.dni)}">
            ${escapeHtml(a.nombre_completo)} · <span class="mono-text">${escapeHtml(a.dni)}</span>
          </button>
        `
        )
        .join("");

      chipsContainer.querySelectorAll("[data-chip-dni]").forEach((chip) => {
        chip.addEventListener("click", () => openStudentReportByDni(chip.dataset.chipDni));
      });
    }

    // Renderizar tabla del Padrón
    const tbody = document.getElementById("alumnos-tbody");
    if (tbody) {
      tbody.innerHTML = cachedAlumnos
        .map(
          (a) => `
          <tr>
            <td class="mono-text"><strong>${escapeHtml(a.dni)}</strong></td>
            <td>${escapeHtml(a.nombre_completo)}</td>
            <td class="mono-text">${escapeHtml(a.legajo)}</td>
            <td>${escapeHtml(a.curso)}</td>
            <td>
              <div style="display:flex; gap:6px;">
                <button type="button" class="btn btn-primary btn-sm" data-quick-pres="${escapeHtml(a.dni)}">
                  ✓ Presente
                </button>
                <button type="button" class="btn btn-outline-navy btn-sm" data-open-report="${escapeHtml(a.dni)}">
                  Ver Informe
                </button>
              </div>
            </td>
          </tr>
        `
        )
        .join("");

      tbody.querySelectorAll("[data-quick-pres]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          try {
            const res = await api.registrarPresente({
              dni: btn.dataset.quickPres,
              materia: "Programación III",
              observaciones: "Presente registrado desde padrón",
              registrado_por: getStoredUsername() || "Docente",
            });
            notify({ type: "success", title: "Presente Registrado", message: res.mensaje });
            await refreshAllData();
          } catch (error) {
            notify({ type: "error", title: "Error", message: error.message });
          }
        });
      });

      tbody.querySelectorAll("[data-open-report]").forEach((btn) => {
        btn.addEventListener("click", () => openStudentReportByDni(btn.dataset.openReport));
      });
    }
  } catch (error) {
    notify({ type: "error", title: "Error al cargar padrón", message: error.message });
  }
}

function initAlumnosForm() {
  document.getElementById("form-nuevo-alumno")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const saved = await api.guardarAlumno({
        dni: document.getElementById("alu-dni").value.trim(),
        legajo: document.getElementById("alu-legajo").value.trim() || null,
        nombre: document.getElementById("alu-nombre").value.trim(),
        apellido: document.getElementById("alu-apellido").value.trim(),
        curso: document.getElementById("alu-curso").value.trim(),
        email: document.getElementById("alu-email").value.trim(),
      });
      notify({
        type: "success",
        title: "Alumno Guardado",
        message: `${saved.nombre_completo} (DNI ${saved.dni}) actualizado en el padrón.`,
      });
      e.target.reset();
      document.getElementById("alu-curso").value = "3° Año - Comisión A";
      await refreshAlumnosDirectory();
    } catch (error) {
      notify({ type: "error", title: "Datos de Alumno Inválidos", message: error.message });
    }
  });
}

async function refreshAllData() {
  await Promise.all([
    refreshDashboard(),
    refreshAlumnosDirectory(),
    refreshFullAttendanceLog(),
  ]);
  if (currentStudentReport?.alumno?.dni) {
    await fetchAndRenderStudentReport(currentStudentReport.alumno.dni);
  }
}

/* ==========================================================================
   ARRANQUE DE LA APLICACIÓN
   ========================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  startInstitutionalClock();
  initNavigation();
  initQuickTerminalAndForms();
  initReportView();
  initAlumnosForm();

  initAuthFlow({
    onAuthenticated: async () => {
      await refreshAllData();
    },
    onLoggedOut: () => {
      currentStudentReport = null;
      switchView("dashboard");
    },
  });
});

