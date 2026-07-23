// useful variables and functions to be reused across the project
// API_BASE / FRONTEND_URL come from config.js (single source of truth for modules).
import { API_BASE, API_PREFIX } from "./config.js";
export { API_BASE, FRONTEND_URL as BASE, API_PREFIX } from "./config.js";

export const TODAY = (() => {
  const d = new Date();
  return (
    d.getFullYear() +
    "-" +
    String(d.getMonth() + 1).padStart(2, "0") +
    "-" +
    String(d.getDate()).padStart(2, "0")
  );
})();

export function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  return {
    "Authorization": "Bearer " + token,
    "Accept": "application/json",
    "Content-Type": "application/json",
  };
}

export async function refreshAccessToken() {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (!data.access) return false;
    localStorage.setItem("access_token", data.access);
    if (data.refresh) localStorage.setItem("refresh_token", data.refresh);
    return true;
  } catch {
    return false;
  }
}

export async function apiFetch(url, options = {}) {
  let res = await fetch(url, options);
  if (res.status === 401 && localStorage.getItem("refresh_token")) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      res = await fetch(url, {
        ...options,
        headers: { ...(options.headers || {}), ...getAuthHeaders() },
      });
    } else {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    }
  }
  return res;
}

let _messageHideTimer = null;

/**
 * Shared status toast for ES module pages.
 * Classic pages use general-components/status-message.js (same API).
 * @param {string} text
 * @param {"success"|"error"|""} [type]
 * @param {{ elementId?: string, baseClass?: string, autoHideMs?: number|null }} [opts]
 */
export function showMessage(text, type = "", opts = {}) {
  const el = document.getElementById(opts.elementId || "message");
  if (!el) return;
  if (_messageHideTimer != null) {
    clearTimeout(_messageHideTimer);
    _messageHideTimer = null;
  }
  const baseClass = opts.baseClass || "message";
  const typeClass =
    type === "success" ? "success" : type === "error" ? "error" : type || "";
  el.textContent = text;
  el.className = typeClass ? `${baseClass} ${typeClass}`.trim() : baseClass;
  el.removeAttribute("hidden");

  const autoHideMs =
    opts.autoHideMs !== undefined
      ? opts.autoHideMs
      : type === "success"
        ? 4000
        : null;
  if (autoHideMs != null) {
    _messageHideTimer = setTimeout(() => {
      _messageHideTimer = null;
      el.textContent = "";
      el.className = baseClass;
    }, autoHideMs);
  }
}

/** Shared vs-prior / vs-plan percent delta (null baseline → null). */
export function computeDeltaPct(current, baseline) {
  if (baseline == null) return null;
  const cur = Number(current) || 0;
  const base = Number(baseline) || 0;
  if (base === 0 && cur === 0) return null;
  if (base === 0) return 100;
  return ((cur - base) / base) * 100;
}

/** Tone for delta coloring: up / down / neutral (≈±10% thresholds). */
export function deltaTone(current, baseline) {
  const pct = computeDeltaPct(current, baseline);
  if (pct == null) return "neutral";
  if (pct > 10) return "up";
  if (pct < -10) return "down";
  return "neutral";
}

/**
 * Read a tab/section key from location hash or ?tab=, falling back to defaultKey.
 * @param {Set<string>|Record<string, unknown>} allowed
 * @param {string} defaultKey
 */
export function getTabFromLocation(allowed, defaultKey) {
  const isAllowed =
    allowed instanceof Set
      ? (key) => allowed.has(key)
      : (key) => Object.prototype.hasOwnProperty.call(allowed, key);
  const hash = location.hash.replace(/^#/, "");
  if (isAllowed(hash)) return hash;
  const tabParam = new URLSearchParams(location.search).get("tab");
  if (isAllowed(tabParam)) return tabParam;
  return defaultKey;
}

/** Sync hash to the active tab; clears hash when on the default tab. */
export function syncTabToLocation(tab, defaultKey) {
  const nextHash = tab === defaultKey ? "" : `#${tab}`;
  const nextUrl = `${location.pathname}${location.search}${nextHash}`;
  const currentUrl = `${location.pathname}${location.search}${location.hash}`;
  if (currentUrl !== nextUrl) {
    history.replaceState(null, "", nextUrl);
  }
}

/**
 * Bind document click-outside + Escape to close an open overlay/menu.
 * Each consumer keeps its own open-state CSS/ARIA contract.
 * @param {{ isOpen: () => boolean, onClose: () => void, isInside: (target: EventTarget|null) => boolean }} opts
 * @returns {() => void} unbind
 */
export function bindDismissOnOutsideOrEscape({ isOpen, onClose, isInside }) {
  function onClick(event) {
    if (!isOpen()) return;
    if (isInside(event.target)) return;
    onClose();
  }
  function onKey(event) {
    if (event.key === "Escape" && isOpen()) onClose();
  }
  document.addEventListener("click", onClick);
  document.addEventListener("keydown", onKey);
  return () => {
    document.removeEventListener("click", onClick);
    document.removeEventListener("keydown", onKey);
  };
}

function flattenErrorLeaves(data) {
  if (data == null) return [];
  if (typeof data === "string") return [data];
  if (Array.isArray(data)) return data.flatMap(flattenErrorLeaves);
  if (typeof data === "object") {
    return Object.keys(data).flatMap((key) => flattenErrorLeaves(data[key]));
  }
  return [String(data)];
}

/**
 * Flatten DRF-style error payloads into a single user-facing string.
 * @param {*} data
 * @param {{ fallback?: string, humanize?: function, includeKey?: boolean, leavesOnly?: boolean, joiner?: string }} [opts]
 */
export function formatApiErrors(data, opts = {}) {
  const fallback = opts.fallback || "Something went wrong.";
  if (data == null) return fallback;
  if (typeof data === "string") return data;

  if (opts.leavesOnly) {
    const leaves = flattenErrorLeaves(data);
    const unique = [...new Set(leaves)];
    return unique.length ? unique.join(opts.joiner || " ") : fallback;
  }

  if (Array.isArray(data)) {
    return data.map(String).join(opts.joiner || " ") || fallback;
  }
  if (typeof data !== "object") return String(data);
  if (data.detail) return String(data.detail);
  if (data.non_field_errors) {
    return data.non_field_errors.map(String).join(opts.joiner || " ") || fallback;
  }

  const parts = [];
  const includeKey = opts.includeKey !== false;
  Object.keys(data).forEach((key) => {
    const val = data[key];
    const messages = Array.isArray(val) ? val : [String(val)];
    messages.forEach((msg) => {
      if (opts.humanize) parts.push(opts.humanize(key, String(msg)));
      else if (includeKey) parts.push(`${key}: ${msg}`);
      else parts.push(String(msg));
    });
  });
  return parts.length ? parts.join(opts.joiner || " ") : fallback;
}

// to be used when the date filters are present 
export function syncDateFilters() {
    var fromEl = document.getElementById("start_date");
    var toEl = document.getElementById("end_date");
    if (!fromEl || !toEl) return;
  
    // Clamp end_date to today if user picks a future date
    if (toEl.value && toEl.value > TODAY) {
      toEl.value = TODAY;
    }
    // Clamp start_date to today as well (can't start in the future)
    if (fromEl.value && fromEl.value > TODAY) {
      fromEl.value = TODAY;
    }
  
    var from = fromEl.value;
    var to = toEl.value;
    if (!from || !to) return;
    if (from > to) {
      toEl.value = from;
    }
  }
