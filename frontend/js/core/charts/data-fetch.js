import { API_BASE, getAuthHeaders } from "../../utils.js";

async function fetchJson(url) {
  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

function fetchWithDateRange(path, extraParams, startDate, endDate) {
  const url = new URL(API_BASE + path);
  Object.entries(extraParams || {}).forEach(([key, value]) => {
    if (value != null && value !== "") url.searchParams.set(key, String(value));
  });
  if (startDate) url.searchParams.set("start_date", startDate);
  if (endDate) url.searchParams.set("end_date", endDate);
  return fetchJson(url);
}

export async function fetchFavExercises(startDate, endDate) {
  return fetchWithDateRange("/api/v1/favourite-exercises", {}, startDate, endDate);
}

/**
 * Total volume hierarchy table.
 * @param {{ period?: string, parentId?: number|null, startDate?: string, endDate?: string }} opts
 */
export async function fetchTotalVolume(opts = {}) {
  const periodKey = (opts.period || "all").toLowerCase();
  const extra = { period: periodKey };

  if (periodKey === "all") {
    if (opts.startDate) extra.start_date = opts.startDate;
    if (opts.endDate) extra.end_date = opts.endDate;
  }

  if (opts.parentId != null && opts.parentId !== "") {
    extra.parent_id = String(opts.parentId);
  }

  return fetchWithDateRange("/api/v1/total-volume", extra);
}

export async function fetchTotalVolumeDaily(exerciseId, startDate, endDate) {
  return fetchWithDateRange("/api/v1/total-volume-daily", { exercise_id: exerciseId }, startDate, endDate);
}

export async function fetchWorkoutSplits(startDate, endDate) {
  return fetchWithDateRange("/api/v1/workout-splits", {}, startDate, endDate);
}

export async function fetchGymWeekdays(startDate, endDate) {
  return fetchWithDateRange("/api/v1/gym-weekdays", {}, startDate, endDate);
}

export async function fetchHomeSummary() {
  return fetchJson(new URL(API_BASE + "/api/v1/home-summary"));
}
