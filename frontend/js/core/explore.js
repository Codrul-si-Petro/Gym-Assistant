import { API_BASE, API_PREFIX } from "../config.js";
import { getAuthHeaders } from "../utils.js";

let allExercises = [];

function renderMuscles(muscles) {
  if (!muscles?.length) return "<span class=\"exercise-meta\">No muscle mapping yet</span>";
  return `<div class="muscle-list">${muscles.map((m) => {
    const cls = m.muscle_role?.toLowerCase() === "primary" ? "muscle-tag muscle-tag--primary" : "muscle-tag";
    const role = m.muscle_role ? ` (${m.muscle_role})` : "";
    return `<span class="${cls}">${m.muscle_name}${role}</span>`;
  }).join("")}</div>`;
}

function renderVideo(exercise) {
  if (exercise.youtube_embed_url) {
    return `<div class="video-wrap"><iframe src="${exercise.youtube_embed_url}" title="${exercise.display_title || exercise.exercise_name}" allowfullscreen loading="lazy"></iframe></div>`;
  }
  if (exercise.youtube_url) {
    return `<a class="video-link" href="${exercise.youtube_url}" target="_blank" rel="noopener noreferrer">Watch on YouTube</a>`;
  }
  return `<span class="exercise-meta">No demo video yet</span>`;
}

function renderCard(exercise) {
  return `
    <article class="exercise-card card reveal" data-name="${exercise.exercise_name.toLowerCase()}">
      <h2>${exercise.exercise_name}</h2>
      <div class="exercise-meta">${exercise.exercise_movement_type}</div>
      ${renderMuscles(exercise.muscles)}
      ${exercise.notes ? `<p class="exercise-notes">${exercise.notes}</p>` : ""}
      ${renderVideo(exercise)}
    </article>
  `;
}

function renderGrid(exercises) {
  const grid = document.getElementById("exercise-grid");
  const status = document.getElementById("explore-status");
  if (!grid) return;

  if (!exercises.length) {
    grid.innerHTML = "";
    status.textContent = "No exercises match your search.";
    return;
  }

  status.textContent = `${exercises.length} exercise${exercises.length === 1 ? "" : "s"}`;
  grid.innerHTML = exercises.map(renderCard).join("");
  grid.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
}

function filterExercises(query) {
  const q = query.trim().toLowerCase();
  if (!q) return allExercises;
  return allExercises.filter((ex) =>
    ex.exercise_name.toLowerCase().includes(q) ||
    ex.exercise_movement_type.toLowerCase().includes(q) ||
    ex.muscles?.some((m) => m.muscle_name.toLowerCase().includes(q))
  );
}

async function loadExercises() {
  const status = document.getElementById("explore-status");
  const headers = getAuthHeaders();
  if (!headers) {
    status.textContent = "Please log in to browse exercises.";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}${API_PREFIX}exercises/glossary/`, { headers });
    if (!res.ok) throw new Error("Failed to load");
    allExercises = await res.json();
    renderGrid(allExercises);
  } catch {
    status.textContent = "Could not load exercises. Please try again later.";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  loadExercises();
  const search = document.getElementById("exercise-search");
  search?.addEventListener("input", (e) => renderGrid(filterExercises(e.target.value)));
});
