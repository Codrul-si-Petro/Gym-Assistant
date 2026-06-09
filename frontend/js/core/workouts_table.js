if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
  API_BASE = "http://127.0.0.1:8000";
} else {
  API_BASE = "https://api.gym-assistant.app";
}

const PAGE_SIZE = 50;
let nextPageUrl = `${API_BASE}/api/workouts/?page=1&page_size=${PAGE_SIZE}`;
let isLoading = false;
let hasMore = true;
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

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function buildRowHtml(row, exerciseMap, attachmentMap, equipmentMap) {
  const date = row.ta_created_at ? row.ta_created_at.slice(0, 10) : "";
  const exercise = exerciseMap[row.exercise] ?? row.exercise;
  const attachment = attachmentMap[row.attachment] ?? row.attachment;
  const equipment = equipmentMap[row.equipment] ?? row.equipment;
  return `<tr>
      <td>${row.workout_number}</td>
      <td>${date}</td>
      <td>${escapeHtml(String(exercise))}</td>
      <td>${row.set_number}</td>
      <td>${row.repetitions}</td>
      <td>${row.load}</td>
      <td>${escapeHtml(String(equipment))}</td>
      <td>${escapeHtml(String(attachment))}</td>
      <td>${row.unit}</td>
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
    const [exJson, atJson, eqJson] = await Promise.all([exRes.json(), atRes.json(), eqRes.json()]);
    (exJson || []).forEach((e) => { exerciseMap[e.exercise_id] = e.exercise_name; });
    (atJson || []).forEach((a) => { attachmentMap[a.attachment_id] = a.attachment_name; });
    (eqJson || []).forEach((e) => { equipmentMap[e.equipment_id] = e.equipment_name; });
  } catch (_) {
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

async function fetchWorkoutsPage(reset = false) {
  if (isLoading || (!hasMore && !reset)) return;

  const headers = getAuthHeaders();
  const tbody = document.getElementById("workout-tbody");
  if (!headers) {
    setStatusMessage("Not logged in. Log in to see workouts.");
    if (tbody) tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">Not logged in</td></tr>';
    return;
  }

  if (reset) {
    nextPageUrl = `${API_BASE}/api/workouts/?page=1&page_size=${PAGE_SIZE}`;
    hasMore = true;
    cachedMaps = null;
    if (tbody) tbody.innerHTML = "";
    const wrap = document.querySelector(".table-wrap");
    if (wrap) wrap.scrollLeft = 0;
  }

  isLoading = true;
  setLoadingRow(true);
  setStatusMessage("");

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
    const payload = contentType.includes("application/json")
      ? await res.json()
      : null;

    if (!res.ok) {
      const detail = payload?.detail || payload?.error || `Request failed (${res.status}).`;
      throw new Error(detail);
    }

    if (!payload) {
      throw new Error("Unexpected response from workouts API.");
    }

    const rows = Array.isArray(payload) ? payload : (payload.results || []);
    nextPageUrl = payload.next || null;
    hasMore = !!nextPageUrl;

    if (reset && rows.length === 0) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">No workouts found</td></tr>';
      hasMore = false;
      return;
    }

    const maps = await loadDimensionMaps(headers);
    const html = rows.map((row) => buildRowHtml(row, maps.exerciseMap, maps.attachmentMap, maps.equipmentMap)).join("");
    if (tbody) tbody.insertAdjacentHTML("beforeend", html);

    if (!hasMore) {
      setStatusMessage(rows.length ? "All workouts loaded." : "");
    }
  } catch (err) {
    setStatusMessage(err?.message || "Failed to load workouts.");
    if (reset && tbody) {
      tbody.innerHTML = '<tr><td colspan="12" class="empty-msg">Error loading data</td></tr>';
    }
    hasMore = false;
  } finally {
    isLoading = false;
    setLoadingRow(false);
  }
}

function initInfiniteScroll() {
  const sentinel = document.getElementById("scroll-sentinel");
  if (!sentinel || !("IntersectionObserver" in window)) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) fetchWorkoutsPage(false);
    });
  }, { rootMargin: "200px" });

  observer.observe(sentinel);
}

document.addEventListener("DOMContentLoaded", () => {
  fetchWorkoutsPage(true);
  initInfiniteScroll();
});
