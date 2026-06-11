const THEME_KEY = "gym_assistant_theme";

export function getStoredTheme() {
  return localStorage.getItem(THEME_KEY) || "dark";
}

export function applyTheme(theme) {
  const resolved = theme === "light" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", resolved);
  localStorage.setItem(THEME_KEY, resolved);
  document.querySelectorAll(".theme-toggle").forEach((btn) => {
    const isDark = resolved === "dark";
    btn.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
    btn.textContent = isDark ? "☀" : "☾";
  });
}

export function bindThemeToggles(root = document) {
  root.querySelectorAll(".theme-toggle").forEach((btn) => {
    const clone = btn.cloneNode(true);
    btn.replaceWith(clone);
    clone.addEventListener("click", () => {
      const next = getStoredTheme() === "dark" ? "light" : "dark";
      applyTheme(next);
    });
  });
}

export function initTheme() {
  applyTheme(getStoredTheme());
  bindThemeToggles();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initTheme);
} else {
  initTheme();
}
