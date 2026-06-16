import { API_BASE, API_PREFIX } from "../config.js";
import { getAuthHeaders } from "../utils.js";

const SECTIONS = {
  exercises: { label: "Exercises", searchPlaceholder: "Search exercises..." },
  attachments: { label: "Attachments", searchPlaceholder: "Search attachments..." },
  equipment: { label: "Equipment", searchPlaceholder: "Search equipment..." },
};

function getSectionFromLocation() {
  const hash = location.hash.replace(/^#/, "");
  if (SECTIONS[hash]) return hash;

  const tabParam = new URLSearchParams(location.search).get("tab");
  if (SECTIONS[tabParam]) return tabParam;

  return "exercises";
}

function syncSectionToLocation(section) {
  const nextHash = section === "exercises" ? "" : `#${section}`;
  const nextUrl = `${location.pathname}${location.search}${nextHash}`;
  const currentUrl = `${location.pathname}${location.search}${location.hash}`;
  if (currentUrl !== nextUrl) {
    history.replaceState(null, "", nextUrl);
  }
}

let activeSection = getSectionFromLocation();
let allExercises = [];
let allAttachments = [];
let allEquipment = [];

function renderMuscles(muscles) {
  if (!muscles?.length) return "<span class=\"glossary-meta\">No muscle mapping yet</span>";
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
  return `<span class="glossary-meta">No demo video yet</span>`;
}

function renderExerciseCard(exercise) {
  return `
    <article class="glossary-card card reveal" data-name="${exercise.exercise_name.toLowerCase()}">
      <h2>${exercise.exercise_name}</h2>
      <div class="glossary-meta">${exercise.exercise_movement_type}</div>
      ${renderMuscles(exercise.muscles)}
      ${exercise.notes ? `<p class="glossary-notes">${exercise.notes}</p>` : ""}
      ${renderVideo(exercise)}
    </article>
  `;
}

function isDirectImageUrl(url) {
  if (!url) return false;
  if (url.includes("google.com/imgres")) return false;
  try {
    const parsed = new URL(url);
    const path = parsed.pathname.toLowerCase();
    if (/\.(png|jpe?g|webp|gif|svg)$/.test(path)) return true;
    const format = parsed.searchParams.get("fm") || parsed.searchParams.get("format");
    return format ? /^(jpg|jpeg|png|webp|gif)$/i.test(format) : false;
  } catch {
    return false;
  }
}

function formatGlossaryDescription(value) {
  if (!value || value.trim() === "N/A") return "No description yet.";
  return value;
}

function renderGlossaryImage(item, nameField, titleField = null) {
  const imageUrl = item.image_url;
  if (!imageUrl) {
    return `<span class="glossary-meta">No reference image yet</span>`;
  }
  if (isDirectImageUrl(imageUrl)) {
    const title = item[titleField] || item[nameField];
    return `<div class="glossary-image-wrap"><img src="${imageUrl}" alt="${title}" loading="lazy"></div>`;
  }
  return `<a class="video-link" href="${imageUrl}" target="_blank" rel="noopener noreferrer">Browse reference images</a>`;
}

function renderAttachmentImage(attachment) {
  return renderGlossaryImage(attachment, "attachment_name", "display_title");
}

function renderAttachmentCard(attachment) {
  return `
    <article class="glossary-card card reveal" data-name="${attachment.attachment_name.toLowerCase()}">
      <h2>${attachment.attachment_name}</h2>
      ${renderAttachmentImage(attachment)}
      <p class="glossary-notes">${formatGlossaryDescription(attachment.attachment_description)}</p>
    </article>
  `;
}

function renderEquipmentCard(item) {
  const category = item.equipment_category
    ? `<span class="glossary-badge">${item.equipment_category}</span>`
    : "";
  return `
    <article class="glossary-card card reveal" data-name="${item.equipment_name.toLowerCase()}">
      <div class="glossary-card-heading">
        <h2>${item.equipment_name}</h2>
        ${category}
      </div>
      ${renderGlossaryImage(item, "equipment_name", "display_title")}
      <p class="glossary-notes">${formatGlossaryDescription(item.equipment_description)}</p>
    </article>
  `;
}

function getActiveItems() {
  if (activeSection === "attachments") return allAttachments;
  if (activeSection === "equipment") return allEquipment;
  return allExercises;
}

function filterItems(query) {
  const q = query.trim().toLowerCase();
  const items = getActiveItems();
  if (!q) return items;

  if (activeSection === "exercises") {
    return items.filter((ex) =>
      ex.exercise_name.toLowerCase().includes(q) ||
      ex.exercise_movement_type.toLowerCase().includes(q) ||
      ex.muscles?.some((m) => m.muscle_name.toLowerCase().includes(q))
    );
  }

  if (activeSection === "attachments") {
    return items.filter((item) =>
      item.attachment_name.toLowerCase().includes(q) ||
      item.attachment_description?.toLowerCase().includes(q)
    );
  }

  return items.filter((item) =>
    item.equipment_name.toLowerCase().includes(q) ||
    item.equipment_description?.toLowerCase().includes(q) ||
    item.equipment_category?.toLowerCase().includes(q)
  );
}

function renderGrid(items) {
  const grid = document.getElementById("glossary-grid");
  const status = document.getElementById("glossary-status");
  if (!grid) return;

  const sectionLabel = SECTIONS[activeSection].label.toLowerCase();
  if (!items.length) {
    grid.innerHTML = "";
    status.textContent = `No ${sectionLabel} match your search.`;
    return;
  }

  const countLabels = {
    exercises: ["exercise", "exercises"],
    attachments: ["attachment", "attachments"],
    equipment: ["item", "items"],
  };
  const [singular, plural] = countLabels[activeSection];
  status.textContent = `${items.length} ${items.length === 1 ? singular : plural}`;
  const renderCard = activeSection === "attachments"
    ? renderAttachmentCard
    : activeSection === "equipment"
      ? renderEquipmentCard
      : renderExerciseCard;
  grid.innerHTML = items.map(renderCard).join("");
  grid.querySelectorAll(".reveal").forEach((el) => el.classList.add("is-visible"));
}

function updateSearchPlaceholder() {
  const search = document.getElementById("glossary-search");
  if (search) search.placeholder = SECTIONS[activeSection].searchPlaceholder;
}

function setActiveSection(section, { syncLocation = true } = {}) {
  if (!SECTIONS[section]) return;
  activeSection = section;
  document.querySelectorAll(".glossary-tab").forEach((tab) => {
    const isActive = tab.dataset.section === section;
    tab.classList.toggle("is-active", isActive);
    tab.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  updateSearchPlaceholder();
  const search = document.getElementById("glossary-search");
  renderGrid(filterItems(search?.value || ""));
  if (syncLocation) syncSectionToLocation(section);
}

const NO_STORE = { cache: "no-store" };

async function loadGlossary() {
  const status = document.getElementById("glossary-status");
  const headers = getAuthHeaders();
  if (!headers) {
    status.textContent = "Please log in to browse the glossary.";
    return;
  }

  try {
    const [exercisesRes, attachmentsRes, equipmentRes] = await Promise.all([
      fetch(`${API_BASE}${API_PREFIX}exercises/glossary/`, { headers, ...NO_STORE }),
      fetch(`${API_BASE}${API_PREFIX}attachments/`, { headers, ...NO_STORE }),
      fetch(`${API_BASE}${API_PREFIX}equipment/`, { headers, ...NO_STORE }),
    ]);
    if (!exercisesRes.ok || !attachmentsRes.ok || !equipmentRes.ok) throw new Error("Failed to load");
    [allExercises, allAttachments, allEquipment] = await Promise.all([
      exercisesRes.json(),
      attachmentsRes.json(),
      equipmentRes.json(),
    ]);
    setActiveSection(activeSection);
  } catch {
    status.textContent = "Could not load glossary. Please try again later.";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  setActiveSection(activeSection, { syncLocation: false });

  document.querySelectorAll(".glossary-tab").forEach((tab) => {
    tab.addEventListener("click", () => setActiveSection(tab.dataset.section));
  });
  window.addEventListener("hashchange", () => {
    const section = getSectionFromLocation();
    if (section !== activeSection) setActiveSection(section, { syncLocation: false });
  });
  const search = document.getElementById("glossary-search");
  search?.addEventListener("input", (e) => renderGrid(filterItems(e.target.value)));
  loadGlossary();
});
