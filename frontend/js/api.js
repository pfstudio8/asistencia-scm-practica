/**
 * Cliente HTTP para comunicarse con los Vertical Slices del Backend FastAPI.
 */

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const response = await fetch(path, {
    ...options,
    headers,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (_err) {
    payload = null;
  }

  if (!response.ok) {
    let errorMessage = "Ocurrió un error al procesar la solicitud.";
    if (payload) {
      if (typeof payload.detail === "string") {
        errorMessage = payload.detail;
      } else if (Array.isArray(payload.detail) && payload.detail.length > 0) {
        const first = payload.detail[0];
        errorMessage = first.msg ? first.msg.replace(/^Value error,\s*/i, "") : JSON.stringify(first);
      }
    }
    throw new Error(errorMessage);
  }

  return payload;
}

export const api = {
  // Slice 1: Autenticación
  login: (credentials) =>
    request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    }),

  register: (data) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Slice 2: Padrón de Alumnos
  listarAlumnos: (q = "") => {
    const query = q ? `?q=${encodeURIComponent(q)}` : "";
    return request(`/api/alumnos${query}`);
  },

  obtenerAlumno: (dni) => request(`/api/alumnos/${encodeURIComponent(dni)}`),

  guardarAlumno: (alumno) =>
    request("/api/alumnos", {
      method: "POST",
      body: JSON.stringify(alumno),
    }),

  // Slice 3: Registro de Asistencia por DNI (Entrada Presente / Salida / Listado)
  registrarPresente: (payload) =>
    request("/api/asistencias/presente", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  marcarSalida: (payload) =>
    request("/api/asistencias/salida", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  listarAsistencias: (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, val]) => {
      if (val !== undefined && val !== null && String(val).trim() !== "") {
        params.set(key, String(val).trim());
      }
    });
    const qs = params.toString() ? `?${params.toString()}` : "";
    return request(`/api/asistencias${qs}`);
  },

  // Slice 4: Tardanzas, Ausencias y Justificaciones
  registrarTardanza: (payload) =>
    request("/api/asistencias/tardanza", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  registrarAusente: (payload) =>
    request("/api/asistencias/ausente", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  revisarJustificacion: (id, payload) =>
    request(`/api/asistencias/${id}/justificacion`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  // Slice 5: Informe por Alumno y Resumen de Dashboard
  obtenerDashboard: () => request("/api/informes/dashboard"),

  obtenerInformeAlumno: (dni) =>
    request(`/api/informes/alumno/${encodeURIComponent(dni)}`),
};

