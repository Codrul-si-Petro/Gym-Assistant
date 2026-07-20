import {API_BASE, getAuthHeaders } from '../../utils.js';

export async function fetchFavExercises(startDate, endDate) {
  const url = new URL(API_BASE + "/api/v1/favourite-exercises");
  if (startDate) url.searchParams.set("start_date", startDate);
  if (endDate) url.searchParams.set("end_date", endDate);

  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

/**
 * Total volume hierarchy table.
 * @param {{ period?: string, parentId?: number|null, startDate?: string, endDate?: string }} opts
 */
export async function fetchTotalVolume(opts = {}) {
  const periodKey = (opts.period || "all").toLowerCase();
  const url = new URL(API_BASE + "/api/v1/total-volume");
  url.searchParams.set("period", periodKey);

  if (periodKey === "all") {
    if (opts.startDate) url.searchParams.set("start_date", opts.startDate);
    if (opts.endDate) url.searchParams.set("end_date", opts.endDate);
  }

  if (opts.parentId != null && opts.parentId !== "") {
    url.searchParams.set("parent_id", String(opts.parentId));
  }

  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchTotalVolumeDaily(exerciseId, startDate, endDate) {
  const url = new URL(API_BASE + "/api/v1/total-volume-daily");
  url.searchParams.set("exercise_id", String(exerciseId));
  if (startDate) url.searchParams.set("start_date", startDate);
  if (endDate) url.searchParams.set("end_date", endDate);

  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchWorkoutSplits(startDate, endDate) {
  const url = new URL(API_BASE + "/api/v1/workout-splits");
  if (startDate) url.searchParams.set("start_date", startDate);
  if (endDate) url.searchParams.set("end_date", endDate);

  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchGymWeekdays(startDate, endDate) {
  const url = new URL(API_BASE + "/api/v1/gym-weekdays");
  if (startDate) url.searchParams.set("start_date", startDate);
  if (endDate) url.searchParams.set("end_date", endDate);

  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchHomeSummary() {
  const url = new URL(API_BASE + "/api/v1/home-summary");
  const headers = getAuthHeaders();
  const res = await fetch(url.toString(), { headers });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
