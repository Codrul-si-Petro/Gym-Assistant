import { API_BASE, API_PREFIX } from "../config.js";
import { getPreferredUnit, setPreferredUnit } from "../user-preferences.js";

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
}

function showMessage(text, type = "") {
  const el = document.getElementById("account-msg");
  if (!el) return;
  el.textContent = text;
  el.className = `account-msg ${type}`.trim();
}

function formatErrors(data) {
  if (!data || typeof data !== "object") return "Something went wrong.";
  const parts = [];
  Object.keys(data).forEach((key) => {
    const val = data[key];
    if (Array.isArray(val)) parts.push(`${key}: ${val.join(" ")}`);
    else parts.push(`${key}: ${String(val)}`);
  });
  return parts.length ? parts.join(" ") : "Something went wrong.";
}

async function submitUsername(event) {
  event.preventDefault();
  const headers = getAuthHeaders();
  if (!headers) {
    showMessage("Please log in first.", "error");
    return;
  }

  const form = event.target;
  const payload = {
    username: form.username.value.trim(),
    current_password: form.current_password.value,
  };

  const res = await fetch(`${API_BASE}${API_PREFIX}auth/update-username/`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    showMessage(formatErrors(data), "error");
    return;
  }
  showMessage(data.message || "Username updated.", "success");
  form.current_password.value = "";
}

async function submitPassword(event) {
  event.preventDefault();
  const headers = getAuthHeaders();
  if (!headers) {
    showMessage("Please log in first.", "error");
    return;
  }

  const form = event.target;
  const payload = {
    current_password: form.current_password.value,
    new_password1: form.new_password1.value,
    new_password2: form.new_password2.value,
  };

  const res = await fetch(`${API_BASE}${API_PREFIX}auth/change-password/`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    showMessage(formatErrors(data), "error");
    return;
  }
  showMessage(data.message || "Password updated.", "success");
  form.reset();
}

async function loadPreferences() {
  const headers = getAuthHeaders();
  const select = document.getElementById("preferred-unit");
  if (!headers || !select) return;

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}auth/current-user/`, { headers });
    if (!res.ok) return;
    const data = await res.json();
    const unit = data?.preferred_unit || getPreferredUnit();
    select.value = setPreferredUnit(unit);
  } catch {
    select.value = getPreferredUnit();
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
    showMessage(formatErrors(data), "error");
    return;
  }

  setPreferredUnit(data.preferred_unit || payload.preferred_unit);
  showMessage("Display preference updated.", "success");
}

document.getElementById("username-form")?.addEventListener("submit", submitUsername);
document.getElementById("preferences-form")?.addEventListener("submit", submitPreferences);
document.getElementById("password-form")?.addEventListener("submit", submitPassword);
window.addEventListener("DOMContentLoaded", loadPreferences);
