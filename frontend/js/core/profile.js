import { API_BASE, API_PREFIX, SUPPORT_EMAIL } from "../config.js";
import { getAuthHeaders } from "../utils.js";
import { getPreferredUnit, setPreferredUnit } from "../user-preferences.js";

function showMessage(text, type = "") {
  const el = document.getElementById("profile-msg");
  if (!el) return;
  el.textContent = text;
  el.className = `profile-msg ${type}`.trim();
}

async function loadProfile() {
  const headers = getAuthHeaders();
  if (!headers) return;

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}auth/current-user/`, { headers });
    if (!res.ok) return;
    const user = await res.json();
    if (!user) return;

    document.getElementById("profile-username").textContent = user.username || "—";
    document.getElementById("profile-email").textContent = user.email || "—";

    const select = document.getElementById("preferred-unit");
    if (select) {
      select.value = setPreferredUnit(user.preferred_unit || getPreferredUnit());
    }
  } catch {
    /* ignore */
  }
}

async function submitPreferences(event) {
  event.preventDefault();
  const headers = getAuthHeaders();
  if (!headers) {
    showMessage("Please log in first.", "error");
    return;
  }

  const form = event.target;
  const payload = {
    preferred_unit: form.preferred_unit.value,
  };

  const res = await fetch(`${API_BASE}${API_PREFIX}auth/preferences/`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    showMessage("Could not save your preference. Please try again.", "error");
    return;
  }

  const unit = setPreferredUnit(data.preferred_unit || payload.preferred_unit);
  window.dispatchEvent(new CustomEvent("preferred-unit-changed", { detail: { unit } }));
  showMessage("Display preference updated.", "success");
}

const support = document.getElementById("profile-support");
if (support) {
  support.href = `mailto:${SUPPORT_EMAIL}?subject=Gym%20Assistant%20Support`;
}

document.getElementById("preferences-form")?.addEventListener("submit", submitPreferences);
window.addEventListener("DOMContentLoaded", loadProfile);
