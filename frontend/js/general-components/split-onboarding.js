/**
 * Blocking first-run modal: user must set workout splits or explicitly opt out.
 * Mounted on authenticated pages; no-ops when already configured or logged out.
 */
import { API_BASE, API_PREFIX } from "../config.js";
import { getAuthHeaders } from "../utils.js";

let splits = [];
let dialogEl = null;

function renderList() {
  const list = dialogEl?.querySelector(".split-onboarding-list");
  if (!list) return;
  if (!splits.length) {
    list.innerHTML = `<li class="split-onboarding-empty">No splits yet — add Push, Pull, Legs… or opt out below.</li>`;
    return;
  }
  list.innerHTML = splits
    .map(
      (name, index) =>
        `<li class="split-onboarding-item">
          <span>${name}</span>
          <button type="button" class="split-onboarding-remove" data-index="${index}" aria-label="Remove ${name}">×</button>
        </li>`
    )
    .join("");
}

function setError(message) {
  const el = dialogEl?.querySelector(".split-onboarding-error");
  if (!el) return;
  el.textContent = message || "";
  el.hidden = !message;
}

function addFromInput() {
  const input = dialogEl?.querySelector("#split-onboarding-input");
  if (!input) return;
  const name = (input.value || "").trim();
  if (!name) return;
  if (splits.some((s) => s.toLowerCase() === name.toLowerCase())) {
    setError("That split is already in your list.");
    return;
  }
  if (splits.length >= 20) {
    setError("You can define up to 20 splits.");
    return;
  }
  splits.push(name);
  input.value = "";
  setError("");
  renderList();
}

async function savePreferences(payload) {
  const headers = getAuthHeaders();
  if (!headers) throw new Error("Please log in first.");
  const res = await fetch(`${API_BASE}${API_PREFIX}auth/preferences/`, {
    method: "PATCH",
    headers,
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || "Could not save preferences.");
  }
  return data;
}

function buildDialog() {
  const dialog = document.createElement("dialog");
  dialog.className = "split-onboarding";
  dialog.setAttribute("aria-labelledby", "split-onboarding-title");
  dialog.innerHTML = `
    <div class="split-onboarding-surface" role="document">
      <h2 id="split-onboarding-title" class="split-onboarding-title">Set up workout splits</h2>
      <p class="split-onboarding-copy">
        Splits label your sessions (e.g. Upper, Lower, Push). You can change these later in Profile.
        If you prefer not to use splits, choose that option below — plan and log forms will leave the split blank.
      </p>
      <div class="split-onboarding-add">
        <input type="text" id="split-onboarding-input" maxlength="50" placeholder="e.g. Upper" autocomplete="off">
        <button type="button" class="cta-button cta-button--ghost" id="split-onboarding-add-btn">Add</button>
      </div>
      <ul class="split-onboarding-list" aria-live="polite"></ul>
      <p class="split-onboarding-error" role="alert" hidden></p>
      <div class="split-onboarding-actions">
        <button type="button" class="cta-button" id="split-onboarding-save">Save my splits</button>
        <button type="button" class="cta-button cta-button--ghost" id="split-onboarding-skip">
          I don't want to think about workout splits
        </button>
      </div>
    </div>
  `;
  document.body.appendChild(dialog);

  dialog.querySelector("#split-onboarding-add-btn")?.addEventListener("click", addFromInput);
  dialog.querySelector("#split-onboarding-input")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addFromInput();
    }
  });
  dialog.querySelector(".split-onboarding-list")?.addEventListener("click", (event) => {
    const btn = event.target.closest(".split-onboarding-remove");
    if (!btn) return;
    const index = Number(btn.dataset.index);
    if (!Number.isFinite(index)) return;
    splits.splice(index, 1);
    renderList();
  });

  dialog.querySelector("#split-onboarding-save")?.addEventListener("click", async () => {
    addFromInput();
    if (!splits.length) {
      setError("Add at least one split, or choose “I don't want to think about workout splits”.");
      return;
    }
    setError("");
    try {
      await savePreferences({ workout_splits: splits });
      dialog.close();
    } catch (err) {
      setError(err.message || "Could not save.");
    }
  });

  dialog.querySelector("#split-onboarding-skip")?.addEventListener("click", async () => {
    setError("");
    try {
      await savePreferences({ workout_splits: [], workout_splits_configured: true });
      dialog.close();
    } catch (err) {
      setError(err.message || "Could not save.");
    }
  });

  // Block Esc / backdrop dismiss — user must pick an action.
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
  });
  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      event.stopPropagation();
    }
  });

  return dialog;
}

async function maybeShowOnboarding() {
  const headers = getAuthHeaders();
  if (!headers) return;

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}auth/current-user/`, { headers });
    if (!res.ok) return;
    const user = await res.json();
    if (!user) return;

    // Prompt until the user finishes onboarding (sets splits or opts out).
    // Truncating authentication_userworkoutsplit alone does NOT reset this —
    // also run: UPDATE authentication_user SET workout_splits_configured = false;
    const configured = user.workout_splits_configured === true;
    if (configured) return;

    splits = Array.isArray(user.workout_splits) ? [...user.workout_splits] : [];
    if (!dialogEl) dialogEl = buildDialog();
    renderList();
    setError("");
    if (!dialogEl.open) dialogEl.showModal();
    dialogEl.querySelector("#split-onboarding-input")?.focus();
  } catch (err) {
    console.warn("split-onboarding: could not check preferences", err);
  }
}

function boot() {
  maybeShowOnboarding();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}

window.addEventListener("jwt-stored", boot);
