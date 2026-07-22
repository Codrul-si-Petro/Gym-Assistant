/**
 * Quick KG/LBS display toggle (localStorage only).
 * Profile remains the durable server-synced default; this toggle prefers the
 * local value for immediate Metrics redraws via preferred-unit-changed.
 */
import { getPreferredUnit, setPreferredUnit } from "../user-preferences.js";

function syncToggleButtons(unit) {
  document.querySelectorAll(".unit-toggle").forEach((wrap) => {
    wrap.querySelectorAll(".unit-toggle-btn").forEach((btn) => {
      const isActive = btn.dataset.unit === unit;
      btn.classList.toggle("is-active", isActive);
      btn.setAttribute("aria-pressed", isActive ? "true" : "false");
    });
  });
}

function applyUnit(unit) {
  const normalized = setPreferredUnit(unit);
  syncToggleButtons(normalized);
  window.dispatchEvent(new CustomEvent("preferred-unit-changed", { detail: { unit: normalized } }));
}

export function initUnitToggle(root = document) {
  const unit = getPreferredUnit();
  syncToggleButtons(unit);

  root.querySelectorAll(".unit-toggle").forEach((wrap) => {
    wrap.addEventListener("click", (event) => {
      const btn = event.target.closest(".unit-toggle-btn");
      if (!btn || !wrap.contains(btn)) return;
      const next = btn.dataset.unit === "LBS" ? "LBS" : "KG";
      if (next === getPreferredUnit()) return;
      applyUnit(next);
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => initUnitToggle());
} else {
  initUnitToggle();
}
