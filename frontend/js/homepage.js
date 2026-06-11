import { API_BASE, API_PREFIX, SUPPORT_EMAIL } from "./config.js";
import { convertKgToPreferred, setPreferredUnit, unitSuffix } from "./user-preferences.js";

const words = ["inspiration.", "passion.", "motivation."];
let i = 0;

setInterval(() => {
  const el = document.getElementById("word");
  if (!el) return;
  i = (i + 1) % words.length;
  el.textContent = words[i];
}, 1500);

function formatNumber(value) {
  return new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(value);
}

async function loadHomeSummary() {
  const token = localStorage.getItem("access_token");
  const statsEl = document.getElementById("home-stats");
  const inactivityEl = document.getElementById("home-inactivity");
  const liftedEl = document.getElementById("home-total-lifted");
  if (!token || !statsEl || !inactivityEl || !liftedEl) return;

  try {
    const [summaryRes, userRes] = await Promise.all([
      fetch(`${API_BASE}${API_PREFIX}v1/home-summary`, {
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      }),
      fetch(`${API_BASE}${API_PREFIX}auth/current-user/`, {
        headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
      }),
    ]);
    if (!summaryRes.ok || !userRes.ok) return;
    const data = await summaryRes.json();
    const user = await userRes.json();
    const unit = setPreferredUnit(user?.preferred_unit || "KG");
    const username = user?.username || "athlete";
    statsEl.hidden = false;

    const days = data.days_since_last_workout;
    if (days == null) {
      inactivityEl.textContent = `Welcome back ${username}! Log your first workout today.`;
    } else if (days <= 0) {
      inactivityEl.textContent = `Welcome back ${username}! Your last workout was today.`;
    } else if (days < 5) {
      inactivityEl.textContent = `Welcome back ${username}! Your last workout was ${days} day${days === 1 ? "" : "s"} ago, enjoy your rest days.`;
    } else {
      inactivityEl.textContent = `Welcome back ${username}! Your last workout was ${days} days ago, it's time to get back in the gym.`;
    }

    const converted = convertKgToPreferred(data.total_volume_kg, unit);
    liftedEl.textContent = `${formatNumber(converted)} ${unitSuffix(unit)} lifted until now`;
  } catch {
    /* ignore summary errors on homepage */
  }
}

function updateHomeAuthState() {
  const loggedIn = !!localStorage.getItem("access_token");
  const authenticatedLinks = document.getElementById("authenticated-links");
  const statsEl = document.getElementById("home-stats");

  if (authenticatedLinks) authenticatedLinks.style.display = loggedIn ? "flex" : "none";
  if (statsEl) statsEl.hidden = !loggedIn;

  if (loggedIn) loadHomeSummary();
}

const supportLink = document.getElementById("support-link");
if (supportLink) {
  supportLink.href = `mailto:${SUPPORT_EMAIL}?subject=Gym%20Assistant%20Feedback`;
}

window.addEventListener("DOMContentLoaded", updateHomeAuthState);
window.addEventListener("jwt-stored", updateHomeAuthState);

export { loadHomeSummary };
