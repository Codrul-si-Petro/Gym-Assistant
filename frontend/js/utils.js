// useful variables and functions to be reused across the project
// will have to deprecate a lot of stuff after
export const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://127.0.0.1:8000"
  : "https://api.gym-assistant.app";

export const BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:5500"
  : "https://gym-assistant.app";

export const TODAY = new Date().toISOString().slice(0, 10);

export function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  if (!token) return null;
  return {
    "Authorization": "Bearer " + token,
    "Accept": "application/json",
    "Content-Type": "application/json",
  };
}

// to be used when the date filters are present 
export function syncDateFilters() {
    var fromEl = document.getElementById("start_date");
    var toEl = document.getElementById("end_date");
    if (!fromEl || !toEl) return;
  
    // Clamp end_date to today if user picks a future date
    if (toEl.value && toEl.value > TODAY) {
      toEl.value = TODAY;
    }
    // Clamp start_date to today as well (can't start in the future)
    if (fromEl.value && fromEl.value > TODAY) {
      fromEl.value = TODAY;
    }
  
    var from = fromEl.value;
    var to = toEl.value;
    if (!from || !to) return;
    if (from > to) {
      toEl.value = from;
    }
  }
