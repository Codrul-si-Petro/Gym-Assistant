// API_BASE / getAuthHeaders come from api-base.js (load that script first).
// Dimension fetch/parse helpers come from dimension-picker.js (load that script first).
// PLACEHOLDER_DIMENSION_ID is provided by dimension-picker.js.

const PLACEHOLDER_DIMENSION_NAME = "None";

function dimensionDisplayName(map, id) {
  if (id === PLACEHOLDER_DIMENSION_ID || id == null) return PLACEHOLDER_DIMENSION_NAME;
  return map[id] ?? id ?? "";
}

function displayWorkoutSplit(split) {
  return split && split !== PLACEHOLDER_DIMENSION_NAME ? split : "";
}

const PAGE_SIZE = 50;
const SET_TYPE_SEEDS = ["Working set", "Warm-up", "Drop set", "None"];
const COL_COUNT = 13;

let nextPageUrl = "";
let isLoading = false;
let hasMore = true;
let loadedCount = 0;
let totalCount = null;
let cachedMaps = null;
let dimensionLists = { exercises: [], attachments: [], equipment: [] };
let rowDataMap = {};
const seenSplits = new Set();
const seenSetTypes = new Set();
let activeFilters = {};
let editSheet = null;

function normalizeApiUrl(url) {
  if (!url) return null;
  try {
    const parsed = new URL(url, API_BASE);
    return `${API_BASE}${parsed.pathname}${parsed.search}`;
  } catch {
    return url.startsWith("http") ? url : `${API_BASE}${url}`;
  }
}

function parseListPayload(payload) {
  if (Array.isArray(payload)) {
    return { rows: payload, next: null, count: payload.length };
  }
  return {
    rows: payload?.results || [],
    next: payload?.next || null,
    count: typeof payload?.count === "number" ? payload.count : null,
  };
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function todayIsoDate() {
  // Local calendar date (not UTC) — matches plan/log/today helpers.
  const d = new Date();
  return (
    d.getFullYear() +
    "-" +
    String(d.getMonth() + 1).padStart(2, "0") +
    "-" +
    String(d.getDate()).padStart(2, "0")
  );
}

function formatRowDate(row) {
  if (row.date_id) return String(row.date_id).slice(0, 10);
  if (row.ta_created_at) return row.ta_created_at.slice(0, 10);
  if (row.date) return String(row.date).slice(0, 10);
  return "";
}

function buildFilterQueryString() {
  const params = new URLSearchParams();
  params.set("page", "1");
  params.set("page_size", String(PAGE_SIZE));
  if (activeFilters.exercise_id) params.set("exercise_id", activeFilters.exercise_id);
  if (activeFilters.workout_split) params.set("workout_split", activeFilters.workout_split);
  if (activeFilters.set_type) params.set("set_type", activeFilters.set_type);
  if (activeFilters.workout_number) params.set("workout_number", activeFilters.workout_number);
  if (activeFilters.start_date) params.set("start_date", activeFilters.start_date);
  if (activeFilters.end_date) params.set("end_date", activeFilters.end_date);
  if (activeFilters.scenario) params.set("scenario", activeFilters.scenario);
  return params.toString();
}

function getListUrl() {
  return `${API_BASE}/api/workouts/?${buildFilterQueryString()}`;
}

function countActiveFilters() {
  return Object.keys(activeFilters).length;
}

function updateFilterBadge() {
  const badge = document.getElementById("filters-badge");
  if (!badge) return;
  const n = countActiveFilters();
  badge.textContent = String(n);
  badge.hidden = n === 0;
}

function collectFilterOption(row) {
  if (row.workout_split && row.workout_split !== PLACEHOLDER_DIMENSION_NAME) {
    seenSplits.add(row.workout_split);
  }
  if (row.set_type) seenSetTypes.add(row.set_type);
}

function refillSelect(selectId, values, currentValue) {
  const select = document.getElementById(selectId);
  if (!select) return;
  const keep = currentValue || select.value;
  while (select.options.length > 1) select.remove(1);
  [...values].sort((a, b) => a.localeCompare(b)).forEach((val) => {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = val;
    select.appendChild(opt);
  });
  if (keep) select.value = keep;
}

function refreshFilterSelects() {
  refillSelect("filter-split", seenSplits, activeFilters.workout_split || "");
  refillSelect("filter-set-type", new Set([...SET_TYPE_SEEDS, ...seenSetTypes]), activeFilters.set_type || "");
}

function populateExerciseFilter() {
  const select = document.getElementById("filter-exercise");
  if (!select || select.options.length > 1) return;
  dimensionLists.exercises.forEach((ex) => {
    const opt = document.createElement("option");
    opt.value = String(ex.exercise_id);
    opt.textContent = ex.exercise_name;
    select.appendChild(opt);
  });
}

async function loadSplitFilterOptions(headers) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workout-splits`, { headers });
    if (!res.ok) return;
    const data = await res.json();
    (data.results || []).forEach((row) => {
      if (row.workout_split) seenSplits.add(row.workout_split);
    });
    refreshFilterSelects();
  } catch {
    /* splits dropdown falls back to values seen in loaded rows */
  }
}

function buildRowHtml(row, exerciseMap, attachmentMap, equipmentMap) {
  rowDataMap[row.workout_id] = row;
  collectFilterOption(row);

  const date = formatRowDate(row);
  const exercise = exerciseMap[row.exercise] ?? row.exercise ?? "";
  const attachment = dimensionDisplayName(attachmentMap, row.attachment);
  const equipment = dimensionDisplayName(equipmentMap, row.equipment);

  return `<tr class="workout-row" data-workout-id="${row.workout_id}" tabindex="0" role="button" aria-label="Edit set">
      <td>${row.workout_number ?? ""}</td>
      <td>${date}</td>
      <td>${escapeHtml(String(exercise))}</td>
      <td>${row.set_number ?? ""}</td>
      <td data-col="reps">${row.repetitions ?? ""}</td>
      <td>${row.load ?? ""}</td>
      <td>${escapeHtml(String(equipment))}</td>
      <td>${escapeHtml(String(attachment))}</td>
      <td>${escapeHtml(String(row.unit || ""))}</td>
      <td>${escapeHtml(String(row.set_type || ""))}</td>
      <td>${escapeHtml(String(row.comments || ""))}</td>
      <td>${escapeHtml(displayWorkoutSplit(row.workout_split))}</td>
      <td class="edit-col"><span class="edit-icon" aria-hidden="true">✎</span></td>
  </tr>`;
}

function updateRowFromData(tr, row, maps) {
  const exercise = maps.exerciseMap[row.exercise] ?? row.exercise ?? "";
  const attachment = dimensionDisplayName(maps.attachmentMap, row.attachment);
  const equipment = dimensionDisplayName(maps.equipmentMap, row.equipment);
  const cells = tr.querySelectorAll("td");
  if (cells.length < COL_COUNT) return;
  cells[0].textContent = row.workout_number ?? "";
  cells[1].textContent = formatRowDate(row);
  cells[2].textContent = String(exercise);
  cells[3].textContent = row.set_number ?? "";
  cells[4].textContent = row.repetitions ?? "";
  cells[5].textContent = row.load ?? "";
  cells[6].textContent = String(equipment);
  cells[7].textContent = String(attachment);
  cells[8].textContent = row.unit || "";
  cells[9].textContent = row.set_type || "";
  cells[10].textContent = row.comments || "";
  cells[11].textContent = displayWorkoutSplit(row.workout_split);
}

async function loadDimensionMaps(headers) {
  if (cachedMaps) return cachedMaps;
  try {
    const lists = await fetchDimensionLists(headers);
    dimensionLists.exercises = lists.exercises;
    dimensionLists.attachments = lists.attachments;
    dimensionLists.equipment = lists.equipment;
    cachedMaps = {
      exerciseMap: buildIdToNameMap(lists.exercises, "exercise_id", "exercise_name"),
      attachmentMap: buildIdToNameMap(lists.attachments, "attachment_id", "attachment_name"),
      equipmentMap: buildIdToNameMap(lists.equipment, "equipment_id", "equipment_name"),
    };
    populateExerciseFilter();
  } catch {
    /* use IDs if lookups fail */
    cachedMaps = { exerciseMap: {}, attachmentMap: {}, equipmentMap: {} };
  }
  return cachedMaps;
}

function setStatusMessage(text, isSuccess) {
  const authMsg = document.getElementById("auth-msg");
  if (!authMsg) return;
  authMsg.textContent = text;
  authMsg.classList.toggle("auth-msg--success", !!isSuccess);
}

function setLoadingRow(visible) {
  const loadingRow = document.getElementById("loading-row");
  if (loadingRow) loadingRow.hidden = !visible;
}

function updatePaginationControls() {
  const loadMoreBtn = document.getElementById("load-more-btn");
  const countEl = document.getElementById("workouts-count");
  if (countEl) {
    const totalText = totalCount != null ? ` of ${totalCount}` : "";
    countEl.textContent = `Showing ${loadedCount}${totalText} sets`;
  }
  if (loadMoreBtn) {
    loadMoreBtn.hidden = !hasMore;
    loadMoreBtn.disabled = isLoading;
    loadMoreBtn.textContent = isLoading ? "Loading…" : "Load more";
  }
}

function formatApiErrors(data) {
  return window.formatApiErrors(data);
}

function buildSelectOptions(items, idKey, nameKey, selectedId) {
  return items
    .map((item) => {
      const id = item[idKey];
      const selected = String(id) === String(selectedId) ? " selected" : "";
      return `<option value="${id}"${selected}>${escapeHtml(item[nameKey])}</option>`;
    })
    .join("");
}

function buildEditFormHtml(row) {
  const date = formatRowDate(row);
  const isPlan = row.scenario === "plan";
  const maxDateAttr = isPlan ? "" : ` max="${todayIsoDate()}"`;
  return `
    <div class="edit-sheet-row">
      <div class="field">
        <label for="edit-workout_number">Workout #</label>
        <input type="number" id="edit-workout_number" name="workout_number" min="1" value="${row.workout_number ?? 1}" required>
      </div>
      <div class="field">
        <label for="edit-date">Date</label>
        <input type="date" id="edit-date" name="date" value="${date}"${maxDateAttr} required>
      </div>
    </div>
    <div class="field">
      <label for="edit-workout_split">Split</label>
      <input type="text" id="edit-workout_split" name="workout_split" maxlength="50" value="${escapeHtml(row.workout_split === "None" ? "" : row.workout_split || "")}">
    </div>
    <div class="field">
      <label for="edit-exercise">Exercise</label>
      <select id="edit-exercise" name="exercise" required>
        ${buildSelectOptions(dimensionLists.exercises, "exercise_id", "exercise_name", row.exercise)}
      </select>
    </div>
    <div class="field">
      <label for="edit-equipment">Equipment</label>
      <select id="edit-equipment" name="equipment">
        <option value="${PLACEHOLDER_DIMENSION_ID}"${row.equipment === PLACEHOLDER_DIMENSION_ID ? " selected" : ""}>None</option>
        ${buildSelectOptions(dimensionLists.equipment, "equipment_id", "equipment_name", row.equipment)}
      </select>
    </div>
    <div class="field">
      <label for="edit-attachment">Attachment</label>
      <select id="edit-attachment" name="attachment">
        ${buildSelectOptions(dimensionLists.attachments, "attachment_id", "attachment_name", row.attachment)}
      </select>
    </div>
    <div class="edit-sheet-row edit-sheet-row--quad">
      <div class="field">
        <label for="edit-set_number">Set</label>
        <input type="number" id="edit-set_number" name="set_number" min="1" max="200" value="${row.set_number ?? 1}" required>
      </div>
      <div class="field">
        <label for="edit-repetitions">Reps</label>
        <input type="number" id="edit-repetitions" name="repetitions" min="1" max="1000" value="${row.repetitions ?? 1}" required>
      </div>
      <div class="field">
        <label for="edit-load">Load</label>
        <input type="number" id="edit-load" name="load" min="0" step="any" value="${row.load ?? 0}" required>
      </div>
      <div class="field">
        <label for="edit-unit">Unit</label>
        <select id="edit-unit" name="unit">
          <option value="KG"${row.unit === "KG" ? " selected" : ""}>KG</option>
          <option value="LBS"${row.unit === "LBS" ? " selected" : ""}>LBS</option>
        </select>
      </div>
    </div>
    <div class="field">
      <label for="edit-set_type">Set type</label>
      <input type="text" id="edit-set_type" name="set_type" value="${escapeHtml(row.set_type || "Working set")}">
    </div>
    <div class="field">
      <label for="edit-comments">Comments</label>
      <textarea id="edit-comments" name="comments" rows="2">${escapeHtml(row.comments || "")}</textarea>
    </div>`;
}

function readEditPayload(formEl, row) {
  const dateVal = formEl.querySelector("#edit-date").value;
  const isPlan = row && row.scenario === "plan";
  if (!isPlan && dateVal > todayIsoDate()) {
    throw new Error("Workout date cannot be in the future.");
  }
  const attachmentVal = formEl.querySelector("#edit-attachment").value;
  return {
    workout_number: parseInt(formEl.querySelector("#edit-workout_number").value, 10),
    date: dateVal,
    workout_split: formEl.querySelector("#edit-workout_split").value.trim() || "None",
    exercise: parseInt(formEl.querySelector("#edit-exercise").value, 10),
    equipment: parseInt(formEl.querySelector("#edit-equipment").value, 10) || PLACEHOLDER_DIMENSION_ID,
    attachment: attachmentVal ? parseInt(attachmentVal, 10) : null,
    set_number: parseInt(formEl.querySelector("#edit-set_number").value, 10),
    repetitions: parseInt(formEl.querySelector("#edit-repetitions").value, 10),
    load: parseFloat(formEl.querySelector("#edit-load").value),
    unit: formEl.querySelector("#edit-unit").value,
    set_type: formEl.querySelector("#edit-set_type").value.trim() || "Working set",
    comments: formEl.querySelector("#edit-comments").value.trim() || "None",
  };
}

function openEditSheet(workoutId) {
  const row = rowDataMap[workoutId];
  if (!row || !editSheet) return;

  editSheet.open({
    title: "Edit set",
    formHtml: buildEditFormHtml(row),
    onSave: async (formEl) => {
      const headers = getAuthHeaders();
      if (!headers) throw new Error("Not logged in.");

      const payload = readEditPayload(formEl, row);
      const res = await fetch(`${API_BASE}/api/workouts/${workoutId}/`, {
        method: "PATCH",
        headers,
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(formatApiErrors(data));

      rowDataMap[workoutId] = data;
      collectFilterOption(data);
      refreshFilterSelects();

      const tr = document.querySelector(`tr[data-workout-id="${workoutId}"]`);
      if (tr && cachedMaps) updateRowFromData(tr, data, cachedMaps);
      setStatusMessage("Set updated.", true);
    },
  });
}

function initEditSheet() {
  if (window.GymEditSheet) {
    editSheet = GymEditSheet.create({ title: "Edit set" });
  }
}

function initRowClicks() {
  const tbody = document.getElementById("workout-tbody");
  if (!tbody) return;

  tbody.addEventListener("click", (event) => {
    const tr = event.target.closest(".workout-row");
    if (!tr) return;
    openEditSheet(tr.dataset.workoutId);
  });

  tbody.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const tr = event.target.closest(".workout-row");
    if (!tr) return;
    event.preventDefault();
    openEditSheet(tr.dataset.workoutId);
  });
}

function readFiltersFromForm() {
  const exercise = document.getElementById("filter-exercise")?.value || "";
  const split = document.getElementById("filter-split")?.value || "";
  const setType = document.getElementById("filter-set-type")?.value || "";
  const workoutNumber = document.getElementById("filter-workout-number")?.value || "";
  const startDate = document.getElementById("filter-start-date")?.value || "";
  const endDate = document.getElementById("filter-end-date")?.value || "";
  const scenario = document.getElementById("filter-scenario")?.value || "actuals";

  const filters = {};
  if (exercise) filters.exercise_id = exercise;
  if (split) filters.workout_split = split;
  if (setType) filters.set_type = setType;
  if (workoutNumber) filters.workout_number = workoutNumber;
  if (startDate) filters.start_date = startDate;
  if (endDate) filters.end_date = endDate;
  if (scenario && scenario !== "actuals") filters.scenario = scenario;
  return filters;
}

function applyFilters() {
  activeFilters = readFiltersFromForm();
  updateFilterBadge();
  fetchWorkoutsPage(true);
}

function clearFilters() {
  activeFilters = {};
  ["filter-exercise", "filter-split", "filter-set-type"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  const scenarioEl = document.getElementById("filter-scenario");
  if (scenarioEl) scenarioEl.value = "actuals";
  ["filter-workout-number", "filter-start-date", "filter-end-date"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
  updateFilterBadge();
  fetchWorkoutsPage(true);
}

function initFilters() {
  const toggle = document.getElementById("filters-toggle");
  const panel = document.getElementById("filters-panel");
  if (toggle && panel) {
    toggle.addEventListener("click", () => {
      const open = panel.hidden;
      panel.hidden = !open;
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
  document.getElementById("filters-apply")?.addEventListener("click", applyFilters);
  document.getElementById("filters-clear")?.addEventListener("click", clearFilters);
  updateFilterBadge();
}

async function fetchWorkoutsPage(reset = false) {
  if (isLoading || (!hasMore && !reset)) return;

  const headers = getAuthHeaders();
  const tbody = document.getElementById("workout-tbody");
  if (!headers) {
    setStatusMessage("Not logged in. Log in to see workouts.");
    if (tbody) tbody.innerHTML = `<tr><td colspan="${COL_COUNT}" class="empty-msg">Not logged in</td></tr>`;
    updatePaginationControls();
    return;
  }

  if (reset) {
    nextPageUrl = getListUrl();
    hasMore = true;
    loadedCount = 0;
    totalCount = null;
    rowDataMap = {};
    if (tbody) tbody.innerHTML = "";
    const wrap = document.querySelector(".table-wrap");
    if (wrap) wrap.scrollLeft = 0;
  }

  isLoading = true;
  setLoadingRow(true);
  if (reset) setStatusMessage("");
  updatePaginationControls();

  try {
    const res = await fetch(nextPageUrl, { headers });
    if (res.status === 401) {
      setStatusMessage("Session expired. Please log in again.");
      if (tbody && reset) {
        tbody.innerHTML = `<tr><td colspan="${COL_COUNT}" class="empty-msg">Unauthorized</td></tr>`;
      }
      hasMore = false;
      return;
    }

    const contentType = res.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await res.json() : null;

    if (!res.ok) {
      const detail = payload?.detail || formatApiErrors(payload) || `Request failed (${res.status}).`;
      throw new Error(detail);
    }

    if (!payload) {
      throw new Error("Unexpected response from workouts API.");
    }

    const { rows, next, count } = parseListPayload(payload);
    nextPageUrl = normalizeApiUrl(next);
    hasMore = !!nextPageUrl;
    if (count != null) totalCount = count;

    if (reset && rows.length === 0) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="${COL_COUNT}" class="empty-msg">No workouts found</td></tr>`;
      hasMore = false;
      loadedCount = 0;
      return;
    }

    const maps = await loadDimensionMaps(headers);
    const html = rows
      .map((row) => buildRowHtml(row, maps.exerciseMap, maps.attachmentMap, maps.equipmentMap))
      .join("");
    if (tbody) tbody.insertAdjacentHTML("beforeend", html);
    loadedCount += rows.length;
    refreshFilterSelects();

    if (!hasMore) {
      setStatusMessage("");
    }
  } catch (err) {
    setStatusMessage(err?.message || "Failed to load workouts.");
    if (reset && tbody) {
      tbody.innerHTML = `<tr><td colspan="${COL_COUNT}" class="empty-msg">Error loading data</td></tr>`;
      loadedCount = 0;
    }
    hasMore = false;
  } finally {
    isLoading = false;
    setLoadingRow(false);
    updatePaginationControls();
  }
}

function initLoadMore() {
  const loadMoreBtn = document.getElementById("load-more-btn");
  if (!loadMoreBtn) return;
  loadMoreBtn.addEventListener("click", () => {
    fetchWorkoutsPage(false);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initEditSheet();
  initRowClicks();
  initFilters();
  initLoadMore();
  const headers = getAuthHeaders();
  if (headers) void loadSplitFilterOptions(headers);
  fetchWorkoutsPage(true);
});
