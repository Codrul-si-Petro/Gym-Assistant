import { API_BASE, API_PREFIX, SUPPORT_EMAIL } from "./config.js";
import { convertKgToPreferred, setPreferredUnit, unitSuffix } from "./user-preferences.js";

const words = ["inspiration.", "passion.", "motivation."];
let wordIndex = 0;

setInterval(() => {
  const el = document.getElementById("word");
  if (!el) return;
  wordIndex = (wordIndex + 1) % words.length;
  el.textContent = words[wordIndex];
}, 1500);

function formatNumber(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(value);
}

const TREND_ARROW_PATHS = {
  "is-up": `<line x1="4" y1="20" x2="20" y2="4" /><polyline points="10,4 20,4 20,14" />`,
  "is-down": `<line x1="4" y1="4" x2="20" y2="20" /><polyline points="20,10 20,20 10,20" />`,
  "is-flat": `<line x1="3" y1="12" x2="19" y2="12" /><polyline points="14,6 20,12 14,18" />`,
};

function renderTrendComparison(container, current, previous, periodLabel) {
  const delta = current - previous;
  const trendClass = delta > 0 ? "is-up" : delta < 0 ? "is-down" : "is-flat";
  const sessionWord = (n) => (Math.abs(n) === 1 ? "session" : "sessions");

  let sentence;
  if (delta > 0) {
    sentence = `${delta} more ${sessionWord(delta)} ${periodLabel} than last`;
  } else if (delta < 0) {
    sentence = `${Math.abs(delta)} fewer ${sessionWord(delta)} ${periodLabel} than last`;
  } else {
    sentence = `Same number of sessions ${periodLabel} as last`;
  }

  container.className = `home-trend-row ${trendClass}`;
  container.setAttribute(
    "aria-label",
    `${current} sessions ${periodLabel}, ${previous} last ${periodLabel.replace("this ", "")}. ${sentence}.`,
  );
  container.innerHTML = `
    <svg class="home-trend-arrow-icon" viewBox="0 0 24 24" aria-hidden="true">${TREND_ARROW_PATHS[trendClass]}</svg>
    <p class="home-trend-text">${sentence}</p>
  `;
}

function clearAuthTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

function setViewMode(loggedIn) {
  const guestLanding = document.getElementById("guest-landing");
  const memberHero = document.getElementById("member-hero");
  const siteFooter = document.getElementById("site-footer");

  if (guestLanding) guestLanding.hidden = loggedIn;
  if (memberHero) memberHero.hidden = !loggedIn;
  if (siteFooter) siteFooter.hidden = !loggedIn;
}

async function loadHomeSummary() {
  const token = localStorage.getItem("access_token");
  const statsEl = document.getElementById("home-stats");
  const inactivityEl = document.getElementById("home-inactivity");
  const liftedEl = document.getElementById("home-total-lifted");
  const weekTrendEl = document.getElementById("home-week-trend");
  const monthTrendEl = document.getElementById("home-month-trend");
  const memberNameEl = document.getElementById("member-name");
  if (!token || !statsEl || !inactivityEl || !liftedEl) return;

  statsEl.hidden = true;

  try {
    const [summaryRes, userRes] = await Promise.all([
      fetch(`${API_BASE}${API_PREFIX}v1/home-summary`, {
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      }),
      fetch(`${API_BASE}${API_PREFIX}auth/current-user/`, {
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      }),
    ]);

    if (summaryRes.status === 401 || userRes.status === 401) {
      clearAuthTokens();
      updateHomeAuthState();
      return;
    }
    if (!summaryRes.ok || !userRes.ok) return;

    const data = await summaryRes.json();
    const user = await userRes.json();
    const unit = setPreferredUnit(user?.preferred_unit || "KG");
    const username = user?.username || "athlete";

    if (memberNameEl) memberNameEl.textContent = username;

    const days = data.days_since_last_workout;
    if (days == null) {
      inactivityEl.textContent = `Log your first workout today — let's build the habit.`;
    } else if (days <= 0) {
      inactivityEl.textContent = `What a good day to lift some heavy weights.`;
    } else if (days < 5) {
      inactivityEl.textContent = `Your last workout was ${days} day${days === 1 ? "" : "s"} ago — enjoy your rest days.`;
    } else {
      inactivityEl.textContent = `Your last workout was ${days} days ago — time to get back in the gym.`;
    }

    const converted = convertKgToPreferred(data.total_volume_kg, unit);
    liftedEl.textContent = `${formatNumber(converted)} ${unitSuffix(unit)} lifted until now`;

    if (weekTrendEl) {
      renderTrendComparison(
        weekTrendEl,
        data.workouts_this_week ?? 0,
        data.workouts_last_week ?? 0,
        "this week",
      );
    }
    if (monthTrendEl) {
      renderTrendComparison(
        monthTrendEl,
        data.workouts_this_month ?? 0,
        data.workouts_last_month ?? 0,
        "this month",
      );
    }

    statsEl.hidden = false;
    statsEl.classList.add("is-visible");
  } catch {
    statsEl.hidden = true;
  }
}

function updateHomeAuthState() {
  const loggedIn = !!localStorage.getItem("access_token");
  setViewMode(loggedIn);

  const statsEl = document.getElementById("home-stats");
  if (statsEl) statsEl.hidden = true;

  if (loggedIn) loadHomeSummary();
}

const supportLink = document.getElementById("support-link");
if (supportLink) {
  supportLink.href = `mailto:${SUPPORT_EMAIL}?subject=Gym%20Assistant%20Feedback`;
}

window.addEventListener("DOMContentLoaded", updateHomeAuthState);
window.addEventListener("jwt-stored", updateHomeAuthState);

export { loadHomeSummary };
