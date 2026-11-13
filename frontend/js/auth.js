/**
 * Gestión de Autenticación (Login, Register), persistencia en localStorage ('username')
 * y animaciones de loaders (~0.7s) al iniciar sesión y al salir.
 */

import { api } from "./api.js";
import { notify, runSessionLoader } from "./motion-engine.js";

const USERNAME_STORAGE_KEY = "username";
const PROFILE_STORAGE_KEY = "sica_user_profile";

export function getStoredUsername() {
  return localStorage.getItem(USERNAME_STORAGE_KEY);
}

export function getStoredProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (_e) {
    return null;
  }
}

function saveSession(usuario) {
  localStorage.setItem(USERNAME_STORAGE_KEY, usuario.username);
  localStorage.setItem(PROFILE_STORAGE_KEY, JSON.stringify(usuario));
}

function clearSession() {
  localStorage.removeItem(USERNAME_STORAGE_KEY);
  localStorage.removeItem(PROFILE_STORAGE_KEY);
}

export function renderWelcomeAndSessionUI() {
  const username = getStoredUsername() || "docente";
  const profile = getStoredProfile();
  const rol = profile?.rol || "Docente Institucional";
  const nombreCompleto = profile?.nombre_completo || username;

  const welcomeUsernameEl = document.getElementById("welcome-username");
  const welcomeSubtextEl = document.getElementById("welcome-subtext");
  const sidebarUsernameEl = document.getElementById("sidebar-username");
  const sidebarRoleEl = document.getElementById("sidebar-role");
  const sidebarAvatarEl = document.getElementById("sidebar-avatar");

  if (welcomeUsernameEl) welcomeUsernameEl.textContent = username;
  if (welcomeSubtextEl) {
    welcomeSubtextEl.textContent = `${nombreCompleto} (${rol}) · Sesión activa vinculada en localStorage ['username' = '${username}'].`;
  }
  if (sidebarUsernameEl) sidebarUsernameEl.textContent = username;
  if (sidebarRoleEl) sidebarRoleEl.textContent = rol;
  if (sidebarAvatarEl) {
    sidebarAvatarEl.textContent = username.slice(0, 2).toUpperCase();
  }
}

export function initAuthFlow({ onAuthenticated, onLoggedOut }) {
  const authScreen = document.getElementById("auth-screen");
  const appShell = document.getElementById("app-shell");
  const tabLogin = document.getElementById("tab-login");
  const tabRegister = document.getElementById("tab-register");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const btnFillDemo = document.getElementById("btn-fill-demo");
  const btnLogout = document.getElementById("btn-logout");

  const switchAuthTab = (mode) => {
    const isLogin = mode === "login";
    tabLogin.classList.toggle("active", isLogin);
    tabLogin.setAttribute("aria-selected", String(isLogin));
    tabRegister.classList.toggle("active", !isLogin);
    tabRegister.setAttribute("aria-selected", String(!isLogin));
    loginForm.classList.toggle("hidden", !isLogin);
    registerForm.classList.toggle("hidden", isLogin);
  };

  tabLogin?.addEventListener("click", () => switchAuthTab("login"));
  tabRegister?.addEventListener("click", () => switchAuthTab("register"));

  btnFillDemo?.addEventListener("click", () => {
    switchAuthTab("login");
    document.getElementById("login-username").value = "docente.scm";
    document.getElementById("login-password").value = "admin123";
    notify({
      type: "info",
      title: "Credenciales Demo Cargadas",
      message: "Presioná 'Ingresar al Sistema' para iniciar sesión con docente.scm.",
      duration: 2800,
    });
  });

  // LOGIN SUBMIT -> Loader ~0.7s -> Guarda username en localStorage -> Muestra Dashboard + Bienvenida
  loginForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const usernameInput = document.getElementById("login-username").value.trim();
    const passwordInput = document.getElementById("login-password").value;

    try {
      const res = await api.login({
        username: usernameInput,
        password: passwordInput,
      });

      saveSession(res.usuario);

      await runSessionLoader({
        title: `¡Hola, ${res.usuario.username}! Iniciando sesión...`,
        subtitle: "Cargando métricas institucionales y padrón de alumnos",
        barColor: "#10B981",
        durationMs: 700,
      });

      authScreen.classList.add("hidden");
      appShell.classList.remove("hidden");
      renderWelcomeAndSessionUI();
      loginForm.reset();

      notify({
        type: "success",
        title: `¡Bienvenido/a, ${res.usuario.username}!`,
        message: "Sesión iniciada correctamente. Panel de asistencia listo.",
      });

      await onAuthenticated();
    } catch (error) {
      notify({
        type: "error",
        title: "Error de Autenticación",
        message: error.message,
      });
    }
  });

  // REGISTER SUBMIT -> Crea usuario -> Loader ~0.7s -> Guarda username en localStorage -> Dashboard
  registerForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = {
      username: document.getElementById("reg-username").value.trim(),
      rol: document.getElementById("reg-rol").value,
      nombre_completo: document.getElementById("reg-fullname").value.trim(),
      email: document.getElementById("reg-email").value.trim(),
      password: document.getElementById("reg-password").value,
    };

    try {
      const res = await api.register(payload);
      saveSession(res.usuario);

      await runSessionLoader({
        title: `Configurando cuenta de ${res.usuario.username}...`,
        subtitle: "Registrando perfil docente e iniciando sesión",
        barColor: "#0284C7",
        durationMs: 700,
      });

      authScreen.classList.add("hidden");
      appShell.classList.remove("hidden");
      renderWelcomeAndSessionUI();
      registerForm.reset();
      switchAuthTab("login");

      notify({
        type: "success",
        title: `¡Cuenta creada! Bienvenido/a, ${res.usuario.username}`,
        message: "Tu usuario fue guardado en localStorage y en la base institucional.",
      });

      await onAuthenticated();
    } catch (error) {
      notify({
        type: "error",
        title: "No se pudo crear la cuenta",
        message: error.message,
      });
    }
  });

  // LOGOUT -> Loader ~0.7s -> Limpia localStorage -> Regresa a Login
  btnLogout?.addEventListener("click", async () => {
    const previousUser = getStoredUsername() || "usuario";

    await runSessionLoader({
      title: "Cerrando sesión institucional...",
      subtitle: `Resguardando registros de ${previousUser}`,
      barColor: "#F59E0B",
      durationMs: 700,
    });

    clearSession();
    appShell.classList.add("hidden");
    authScreen.classList.remove("hidden");

    notify({
      type: "info",
      title: "Sesión Finalizada",
      message: `Hasta pronto, ${previousUser}. Se cerró tu sesión de forma segura.`,
    });

    if (onLoggedOut) onLoggedOut();
  });

  // Restauración automática si ya existe `username` en localStorage
  const existingUsername = getStoredUsername();
  if (existingUsername) {
    authScreen.classList.add("hidden");
    appShell.classList.remove("hidden");
    renderWelcomeAndSessionUI();
    onAuthenticated();
  }
}

