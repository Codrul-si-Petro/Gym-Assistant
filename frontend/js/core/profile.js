import { API_BASE, API_PREFIX, SUPPORT_EMAIL } from "../config.js";
import { getAuthHeaders } from "../utils.js";

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
  } catch {
    /* ignore */
  }
}

const support = document.getElementById("profile-support");
if (support) {
  support.href = `mailto:${SUPPORT_EMAIL}?subject=Gym%20Assistant%20Support`;
}

window.addEventListener("DOMContentLoaded", loadProfile);
