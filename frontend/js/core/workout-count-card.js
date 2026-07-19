// Self-contained component (own fetch + own mount), same pattern as
// profile-menu.js, so it can be dropped onto any authenticated page.
import { API_BASE, API_PREFIX } from "../config.js";

async function fetchHomeSummary() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}v1/home-summary`, {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export async function initWorkoutCountCard(containerId = "workout-count-card") {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.hidden = true;

  const loggedIn = !!localStorage.getItem("access_token");
  if (!loggedIn) return;

  const data = await fetchHomeSummary();
  if (!data) return;

  const weekEl = container.querySelector("#workout-count-week");
  const monthEl = container.querySelector("#workout-count-month");
  if (weekEl) weekEl.textContent = data.workouts_this_week ?? 0;
  if (monthEl) monthEl.textContent = data.workouts_this_month ?? 0;

  container.hidden = false;
}

function boot() {
  initWorkoutCountCard();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

window.addEventListener("jwt-stored", boot);
