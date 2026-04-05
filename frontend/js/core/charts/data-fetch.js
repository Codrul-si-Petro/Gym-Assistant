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
