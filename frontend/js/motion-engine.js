/**
 * Motor de Animaciones con Framer Motion (DOM API oficial de framer-motion).
 * Regla de diseño estricta:
 *  - Colores 100% sólidos (CERO glassmorphism / CERO blur / CERO transparencias).
 *  - CERO fades (NUNCA se anima `opacity`; todas las transiciones son mecánicas por `transform`).
 */

let fmAnimate = null;
let fmSpring = null;

// Carga asíncrona del motor DOM oficial de Framer Motion con respaldo local sin conexión
(async function loadFramerMotionDom() {
  const cdnUrls = [
    "https://cdn.jsdelivr.net/npm/framer-motion@11.11.17/dom/+esm",
    "https://esm.sh/framer-motion@11.11.17/dom",
  ];
  for (const url of cdnUrls) {
    try {
      const mod = await import(url);
      if (mod && typeof mod.animate === "function") {
        fmAnimate = mod.animate;
        fmSpring = mod.spring || null;
        break;
      }
    } catch (_err) {
      // Intenta siguiente CDN o usa fallback WAAPI mecánico si no hay red
    }
  }
})();

/**
 * Ejecuta una animación usando Framer Motion `animate` (o Web Animations API si está offline),
 * garantizando transformaciones puras sin tocar `opacity`.
 */
export function motionAnimate(element, keyframes, options = {}) {
  if (!element) return Promise.resolve();

  if (fmAnimate) {
    try {
      const fmOpts = { ...options };
      if (options.useSpring && fmSpring) {
        fmOpts.type = fmSpring;
        fmOpts.stiffness = options.stiffness || 460;
        fmOpts.damping = options.damping || 30;
        delete fmOpts.useSpring;
      }
      const controls = fmAnimate(element, keyframes, fmOpts);
      return controls.finished || Promise.resolve();
    } catch (_e) {
      // Continúa al respaldo nativo si hubiera incompatibilidad de argumentos
    }
  }

  // Respaldo nativo equivalente (sin fades, solo transformaciones geométricas)
  const durationMs = Math.round((options.duration || 0.32) * 1000);
  const easing = options.ease === "linear" ? "linear" : "cubic-bezier(0.22, 1, 0.36, 1)";
  const waapiFrames = buildWaapiFrames(keyframes);
  const anim = element.animate(waapiFrames, {
    duration: durationMs,
    easing,
    fill: "forwards",
  });
  return anim.finished.catch(() => {});
}

function buildWaapiFrames(keyframes) {
  if (Array.isArray(keyframes.x) && Array.isArray(keyframes.scale)) {
    return [
      { transform: `translateX(${keyframes.x[0]}px) scale(${keyframes.scale[0]})` },
      { transform: `translateX(${keyframes.x[1]}px) scale(${keyframes.scale[1]})` },
    ];
  }
  if (Array.isArray(keyframes.x)) {
    return [
      { transform: `translateX(${keyframes.x[0]}px)` },
      { transform: `translateX(${keyframes.x[1]}px)` },
    ];
  }
  if (Array.isArray(keyframes.scaleX)) {
    return [
      { transform: `scaleX(${keyframes.scaleX[0]})` },
      { transform: `scaleX(${keyframes.scaleX[1]})` },
    ];
  }
  if (Array.isArray(keyframes.y) && Array.isArray(keyframes.scale)) {
    return [
      { transform: `translateY(${keyframes.y[0]}px) scale(${keyframes.scale[0]})` },
      { transform: `translateY(${keyframes.y[1]}px) scale(${keyframes.scale[1]})` },
    ];
  }
  return [{ transform: "none" }, { transform: "none" }];
}

const ICONS_BY_TYPE = {
  success: "✓",
  warning: "⏱",
  error: "!",
  info: "→",
};

/**
 * Muestra una notificación con Framer Motion y colores sólidos puros (sin glassmorphism ni fades).
 * @param {Object} config
 * @param {'success'|'warning'|'error'|'info'} config.type
 * @param {string} config.title
 * @param {string} config.message
 * @param {number} [config.duration=3800]
 */
export function notify({ type = "info", title = "Notificación", message = "", duration = 3800 }) {
  const stack = document.getElementById("notification-stack");
  if (!stack) return;

  const toast = document.createElement("div");
  toast.className = `solid-toast toast-${type}`;
  toast.setAttribute("role", "alert");

  toast.innerHTML = `
    <div class="solid-toast-body">
      <span class="solid-toast-icon">${ICONS_BY_TYPE[type] || "•"}</span>
      <div class="solid-toast-content">
        <div class="solid-toast-title"></div>
        <div class="solid-toast-message"></div>
      </div>
      <button type="button" class="solid-toast-close" aria-label="Cerrar notificación">✕</button>
    </div>
    <div class="solid-toast-progress"></div>
  `;

  toast.querySelector(".solid-toast-title").textContent = title;
  toast.querySelector(".solid-toast-message").textContent = message;

  // Posición inicial fuera del viewport derecho (opacidad 1 siempre: NADA de fades)
  toast.style.transform = "translateX(440px) scale(0.95)";
  stack.appendChild(toast);

  const progressBar = toast.querySelector(".solid-toast-progress");
  let closed = false;

  const dismiss = async () => {
    if (closed) return;
    closed = true;
    await motionAnimate(
      toast,
      { x: [0, 460] },
      { duration: 0.24 }
    );
    toast.remove();
  };

  toast.querySelector(".solid-toast-close").addEventListener("click", dismiss);

  // Entrada con resorte mecánico de Framer Motion
  motionAnimate(
    toast,
    { x: [440, 0], scale: [0.95, 1] },
    { useSpring: true, stiffness: 470, damping: 29, duration: 0.34 }
  );

  // Barra de tiempo sólida
  motionAnimate(
    progressBar,
    { scaleX: [1, 0] },
    { duration: duration / 1000, ease: "linear" }
  );

  setTimeout(dismiss, duration);
}

/**
 * Ejecuta la animación de loader sólido de ~0.7s (700ms) al iniciar sesión o al cerrar sesión.
 * Sin fades de opacidad: entrada geométrica limpia y barra de carga animada con Framer Motion.
 */
export async function runSessionLoader({
  title = "Iniciando sesión...",
  subtitle = "Preparando entorno institucional",
  barColor = "#10B981",
  durationMs = 700,
}) {
  const overlay = document.getElementById("session-loader");
  const card = overlay?.querySelector(".loader-card");
  const titleEl = document.getElementById("loader-title");
  const subEl = document.getElementById("loader-subtitle");
  const barEl = document.getElementById("loader-bar");

  if (!overlay || !barEl) {
    await new Promise((r) => setTimeout(r, durationMs));
    return;
  }

  titleEl.textContent = title;
  subEl.textContent = subtitle;
  barEl.style.backgroundColor = barColor;
  barEl.style.transform = "scaleX(0)";

  overlay.classList.remove("hidden");

  if (card) {
    motionAnimate(
      card,
      { y: [18, 0], scale: [0.94, 1] },
      { useSpring: true, stiffness: 500, damping: 32, duration: 0.22 }
    );
  }

  await Promise.all([
    motionAnimate(
      barEl,
      { scaleX: [0, 1] },
      { duration: durationMs / 1000, ease: "linear" }
    ),
    new Promise((resolve) => setTimeout(resolve, durationMs)),
  ]);

  overlay.classList.add("hidden");
}

