// Self-contained component (own fetch + own mount), same pattern as
// profile-menu.js, so it can be dropped onto any authenticated page.
import { API_BASE, API_PREFIX } from "../config.js";
import { computeDeltaPct, deltaTone } from "../utils.js";

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

function formatDeltaLabel(current, baseline, vsLabel) {
  const pct = computeDeltaPct(current, baseline);
  if (pct == null) return `vs ${vsLabel}: —`;
  const sign = pct >= 0 ? "+" : "";
  return `vs ${vsLabel}: ${sign}${pct.toFixed(0)}%`;
}

function renderDelta(el, current, previous, planned, vsPriorLabel) {
  if (!el) return;
  const parts = [];
  parts.push(formatDeltaLabel(current, previous, vsPriorLabel));
  if (planned != null) {
    parts.push(formatDeltaLabel(current, planned, "plan"));
  }
  el.textContent = parts.join(" · ");
  // Color by vs-prior when available; otherwise vs-plan.
  const toneBaseline = previous != null && (Number(previous) || 0) !== 0 ? previous : planned;
  el.className = `workout-count-delta is-${deltaTone(current, toneBaseline)}`;
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
  const yearEl = container.querySelector("#workout-count-year");
  if (weekEl) weekEl.textContent = data.workouts_this_week ?? 0;
  if (monthEl) monthEl.textContent = data.workouts_this_month ?? 0;
  if (yearEl) yearEl.textContent = data.workouts_this_year ?? 0;

  renderDelta(
    container.querySelector("#workout-count-week-delta"),
    data.workouts_this_week ?? 0,
    data.workouts_last_week ?? 0,
    data.workouts_planned_this_week ?? 0,
    "last week"
  );
  renderDelta(
    container.querySelector("#workout-count-month-delta"),
    data.workouts_this_month ?? 0,
    data.workouts_last_month ?? 0,
    data.workouts_planned_this_month ?? 0,
    "last month"
  );
  renderDelta(
    container.querySelector("#workout-count-year-delta"),
    data.workouts_this_year ?? 0,
    data.workouts_last_year ?? 0,
    data.workouts_planned_this_year ?? 0,
    "last year"
  );

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
