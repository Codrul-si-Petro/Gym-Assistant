if (
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1" ||
  window.location.hostname === "::1"
) {
  API_BASE = "http://127.0.0.1:8000";
} else {
  API_BASE = "https://api.gym-assistant.app";
}

const PAGE_SIZE = 50;
let nextPageUrl = `${API_BASE}/api/workouts/?page=1&page_size=${PAGE_SIZE}`;
let isLoading = false;
let hasMore = true;
let loadedCount = 0;
let totalCount = null;
let cachedMaps = null;

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  return {
    Authorization: `Bearer ${token}`,
    Accept: "application/json",
    "Content-Type": "application/json",
  };
}

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

function parseDimensionList(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.results)) return payload.results;
  return [];
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function formatRowDate(row) {
  if (row.ta_created_at) return row.ta_created_at.slice(0, 10);
  if (row.date_id) return String(row.date_id).slice(0, 10);
  if (row.date) return String(row.date).slice(0, 10);
  return "";
}

function buildRowHtml(row, exerciseMap, attachmentMap, equipmentMap) {
  const date = formatRowDate(row);
  const exercise = exerciseMap[row.exercise] ?? row.exercise ?? "";
  const attachment = attachmentMap[row.attachment] ?? row.attachment ?? "";
  const equipment = equipmentMap[row.equipment] ?? row.equipment ?? "";
  return `<tr>
      <td>${row.workout_number ?? ""}</td>
      <td>${date}</td>
      <td>${escapeHtml(String(exercise))}</td>
      <td>${row.set_number ?? ""}</td>
      <td>${row.repetitions ?? ""}</td>
      <td>${row.load ?? ""}</td>
      <td>${escapeHtml(String(equipment))}</td>
      <td>${escapeHtml(String(attachment))}</td>
      <td>${escapeHtml(String(row.unit || ""))}</td>
      <td>${escapeHtml(String(row.set_type || ""))}</td>
      <td>${escapeHtml(String(row.comments || ""))}</td>
      <td>${escapeHtml(String(row.workout_split || ""))}</td>
  </tr>`;
}

async function loadDimensionMaps(headers) {
  if (cachedMaps) return cachedMaps;
  const exerciseMap = {};
  const attachmentMap = {};
  const equipmentMap = {};
  try {
    const [exRes, atRes, eqRes] = await Promise.all([
      fetch(`${API_BASE}/api/exercises/`, { headers }),
      fetch(`${API_BASE}/api/attachments/`, { headers }),
      fetch(`${API_BASE}/api/equipment/`, { headers }),
    ]);
    const [exJson, atJson, eqJson] = await Promise.all([
      exRes.ok ? exRes.json() : [],
      atRes.ok ? atRes.json() : [],
      eqRes.ok ? eqRes.json() : [],
    ]);
    parseDimensionList(exJson).forEach((e) => {
      exerciseMap[e.exercise_id] = e.exercise_name;
    });
    parseDimensionList(atJson).forEach((a) => {
      attachmentMap[a.attachment_id] = a.attachment_name;
    });
    parseDimensionList(eqJson).forEach((e) => {
      equipmentMap[e.equipment_id] = e.equipment_name;
    });
  } catch {
    /* use IDs if lookups fail */
  }
  cachedMaps = { exerciseMap, attachmentMap, equipmentMap };
  return cachedMaps;
}

function setStatusMessage(text) {
  const authMsg = document.getElementById("auth-msg");
  if (authMsg) authMsg.textContent = text;
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
    countEl.textContent = `Showing ${loadedCount}${totalText} workouts`;
  }
  if (loadMoreBtn) {
    loadMoreBtn.hidden = !hasMore;
    loadMoreBtn.disabled = isLoading;
    loadMoreBtn.textContent = isLoading ? "Loading…" : "Load more";
  }
}

async function fetchWorkoutsPage(reset = false) {
  if (isLoading || (!hasMore && !reset)) return;

  const headers = getAuthHeaders();
  const tbody = document.getElementById("workout-tbody");
  if (!headers) {
    setStatusMessage("Not logged in. Log in to see workouts.");
    if (tbody) tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">Not logged in</td></tr>';
    updatePaginationControls();
    return;
  }

  if (reset) {
    nextPageUrl = `${API_BASE}/api/workouts/?page=1&page_size=${PAGE_SIZE}`;
    hasMore = true;
    loadedCount = 0;
    totalCount = null;
    cachedMaps = null;
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
        tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">Unauthorized</td></tr>';
      }
      hasMore = false;
      return;
    }

    const contentType = res.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await res.json() : null;

    if (!res.ok) {
      const detail = payload?.detail || payload?.error || `Request failed (${res.status}).`;
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
      if (tbody) tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">No workouts found</td></tr>';
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

    if (!hasMore) {
      setStatusMessage("");
    }
  } catch (err) {
    setStatusMessage(err?.message || "Failed to load workouts.");
    if (reset && tbody) {
      tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">Error loading data</td></tr>';
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
  fetchWorkoutsPage(true);
  initLoadMore();
});
