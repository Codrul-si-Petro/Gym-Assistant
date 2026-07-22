import { API_BASE, API_PREFIX, SUPPORT_EMAIL } from "../config.js";
import { getAuthHeaders } from "../utils.js";
import { getPreferredUnit, setPreferredUnit } from "../user-preferences.js";

let workoutSplits = [];

function showMessage(text, type = "") {
  const el = document.getElementById("profile-msg");
  if (!el) return;
  el.textContent = text;
  el.className = `profile-msg ${type}`.trim();
}

function renderSplitList() {
  const list = document.getElementById("split-list");
  if (!list) return;
  if (!workoutSplits.length) {
    list.innerHTML = `<li class="profile-split-empty">No splits defined yet.</li>`;
    return;
  }
  list.innerHTML = workoutSplits
    .map(
      (name, index) =>
        `<li class="profile-split-item">
          <span>${name}</span>
          <button type="button" class="profile-split-remove" data-index="${index}" aria-label="Remove ${name}">×</button>
        </li>`
    )
    .join("");
}

function addSplitFromInput() {
  const input = document.getElementById("split-input");
  if (!input) return;
  const name = (input.value || "").trim();
  if (!name) return;
  if (workoutSplits.some((s) => s.toLowerCase() === name.toLowerCase())) {
    showMessage("That split is already in your list.", "error");
    return;
  }
  if (workoutSplits.length >= 20) {
    showMessage("You can define up to 20 splits.", "error");
    return;
  }
  workoutSplits.push(name);
  input.value = "";
  renderSplitList();
  showMessage("");
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

    workoutSplits = Array.isArray(user.workout_splits) ? [...user.workout_splits] : [];
    renderSplitList();
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
    workout_splits: workoutSplits,
  };

  const res = await fetch(`${API_BASE}${API_PREFIX}auth/preferences/`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    showMessage("Could not save your preferences. Please try again.", "error");
    return;
  }

  const unit = setPreferredUnit(data.preferred_unit || payload.preferred_unit);
  workoutSplits = Array.isArray(data.workout_splits) ? [...data.workout_splits] : [...workoutSplits];
  renderSplitList();
  window.dispatchEvent(new CustomEvent("preferred-unit-changed", { detail: { unit } }));
  showMessage("Preferences updated.", "success");
}

const support = document.getElementById("profile-support");
if (support) {
  support.href = `mailto:${SUPPORT_EMAIL}?subject=Gym%20Assistant%20Support`;
}

document.getElementById("preferences-form")?.addEventListener("submit", submitPreferences);
document.getElementById("split-add-btn")?.addEventListener("click", addSplitFromInput);
document.getElementById("split-input")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    addSplitFromInput();
  }
});
document.getElementById("split-list")?.addEventListener("click", (event) => {
  const btn = event.target.closest(".profile-split-remove");
  if (!btn) return;
  const index = Number(btn.dataset.index);
  if (!Number.isFinite(index)) return;
  workoutSplits.splice(index, 1);
  renderSplitList();
});

window.addEventListener("DOMContentLoaded", loadProfile);
