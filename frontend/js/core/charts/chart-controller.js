// Controls which content loads per tab and wires shared date controls.

import { API_BASE, BASE, TODAY, getAuthHeaders, syncDateFilters } from "../../utils.js";
import { convertKgToPreferred, getPreferredUnit, setPreferredUnit, unitSuffix } from "../../user-preferences.js";
// The ?v= on these two imports is a manual cache-buster — bump it whenever
// chart-renderers.js/data-fetch.js change. They aren't covered by the ?v= on
// the <script> tag that loads this file, so edits here can silently keep
// serving a stale cached copy even after a normal refresh.
import {
  renderFavExercisesChart,
  shortLabel,
  destroyChart,
  renderVolumeTable,
  renderVolumeDailyTimeSeries,
  renderWorkoutSplitsChart,
  renderGymWeekdaysChart,
  toggleVolumeDeltaDisplayMode,
  resetVolumeDeltaDisplayMode,
} from "./chart-renderers.js?v=8";
import { fetchFavExercises, fetchGymWeekdays, fetchTotalVolume, fetchTotalVolumeDaily, fetchWorkoutSplits } from "./data-fetch.js?v=3";

let volumeParentId = null;
const volumeParentStack = [];
let volumePeriod = "all";
/** Skip resetting to All when date inputs are updated by a period chip. */
let dateChangeFromChip = false;

/** While the daily chart panel is open, refetch daily volume on date change. */
let volumeDailySelection = null; // { exerciseId: number, exerciseName: string } | null
let volumeDailyChartType = "line"; // "line" | "bar"
let preferredUnit = getPreferredUnit();
/** Cached for click-to-toggle delta display without refetching. */
let lastVolumeTableResults = [];

const dateFrom = document.getElementById("start_date");
const dateTo = document.getElementById("end_date");

function getPeriodDateRange(period) {
  const today = new Date();
  const end = TODAY;
  if (period === "wtd") {
    const monday = new Date(today);
    const isoDay = monday.getDay() === 0 ? 7 : monday.getDay();
    monday.setDate(monday.getDate() - (isoDay - 1));
    return { start: monday.toISOString().slice(0, 10), end };
  }
  if (period === "mtd") {
    return { start: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-01`, end };
  }
  if (period === "ytd") {
    return { start: `${today.getFullYear()}-01-01`, end };
  }
  return { start: "", end };
}

function setActivePeriodChip(period) {
  document.querySelectorAll(".volume-period-chip").forEach((el) => {
    el.classList.toggle("is-active", el.dataset.period === period);
  });
}

function applyPeriodChip(period) {
  volumePeriod = period || "all";
  setActivePeriodChip(volumePeriod);
  resetVolumeDeltaDisplayMode();
  dateChangeFromChip = true;
  if (volumePeriod === "all") {
    if (dateFrom) dateFrom.value = "";
    if (dateTo) dateTo.value = TODAY;
  } else {
    const { start, end } = getPeriodDateRange(volumePeriod);
    if (dateFrom) dateFrom.value = start;
    if (dateTo) dateTo.value = end;
  }
  syncDateFilters();
  dateChangeFromChip = false;
  void loadVolumeTable();
  if (volumeDailySelection) void reloadVolumeDailyChart();
}

function getDateRange() {
  return {
    start: dateFrom?.value || "",
    end: dateTo?.value || "",
  };
}

function updateVolumeHeadingUnit() {
  const heading = document.querySelector(".volume-col-vol");
  if (!heading) return;
  // Just the unit — "Total volume (kg)" was wide enough to push the table out
  // of bounds on narrow screens.
  heading.textContent = unitSuffix(preferredUnit);
}

async function loadPreferredUnit() {
  const headers = getAuthHeaders();
  if (!headers) {
    preferredUnit = getPreferredUnit();
    updateVolumeHeadingUnit();
    return;
  }
  try {
    const res = await fetch(`${API_BASE}/api/auth/current-user/`, { headers });
    if (!res.ok) throw new Error("not-authenticated");
    const user = await res.json();
    preferredUnit = setPreferredUnit(user?.preferred_unit || "KG");
  } catch {
    preferredUnit = getPreferredUnit();
  }
  updateVolumeHeadingUnit();
}

async function reloadVolumeDailyChart() {
  if (!volumeDailySelection) return;
  const skel = document.getElementById("chart-skeleton-volume-daily");
  const inner = document.getElementById("volume-daily-chart-inner");
  const vmsg = document.getElementById("volume-daily-chart-msg");
  skel?.classList.remove("hidden");
  if (inner) inner.style.display = "none";
  destroyChart("volume-daily-canvas");
  if (vmsg) vmsg.textContent = "";
  try {
    const { start, end } = getDateRange();
    const { results: daily = [] } = await fetchTotalVolumeDaily(
      volumeDailySelection.exerciseId,
      start,
      end
    );
    skel?.classList.add("hidden");
    if (!daily.length) {
      if (vmsg) vmsg.textContent = "No day-by-day volume in this range.";
      if (inner) inner.style.display = "none";
      return;
    }
    renderVolumeDailyTimeSeries(
      daily,
      volumeDailySelection.exerciseName,
      volumeDailyChartType,
      preferredUnit
    );
  } catch (e) {
    skel?.classList.add("hidden");
    if (vmsg) vmsg.textContent = "Failed to load daily volume.";
    destroyChart("volume-daily-canvas");
    if (inner) inner.style.display = "none";
    if (String(e.message || "").includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

function setVolumeTableVisible(visible) {
  const inner = document.getElementById("volume-table-inner");
  if (inner) inner.style.display = visible ? "" : "none";
}

/**
 * Swaps the main volume view between the ranking table and the daily chart panel.
 * - "table": show table (when data loaded), hide daily chart block.
 * - "chart": hide table, show daily chart block (loading/render happens in onMinichart).
 */
function setVolumeMainView(mode) {
  const scrollWrap = document.querySelector("#tab-volume .chart-scroll-wrap");
  const chartBlock = document.getElementById("volume-daily-chart-block");
  const periodChips = document.querySelector(".volume-period-chips");
  if (!scrollWrap || !chartBlock) return;

  if (mode === "chart") {
    scrollWrap.classList.add("volume-mode-chart");
    chartBlock.hidden = false;
    if (periodChips) periodChips.hidden = true;
    setVolumeTableVisible(false);
  } else {
    scrollWrap.classList.remove("volume-mode-chart");
    chartBlock.hidden = true;
    if (periodChips) periodChips.hidden = false;
  }
}

function updateVolumeToolbar() {
  const toolbar = document.getElementById("volume-toolbar");
  if (!toolbar) return;
  toolbar.hidden = volumeParentId == null;
}

// function navigateToVolumeChart(exerciseId, exerciseName) {
//   const u = new URL(window.location.href);
//   u.searchParams.set("volumeChart", String(exerciseId));
//   if (exerciseName) u.searchParams.set("volumeChartName", exerciseName);
//   if (dateFrom?.value) u.searchParams.set("start_date", dateFrom.value);
//   if (dateTo?.value) u.searchParams.set("end_date", dateTo.value);
//   window.location.href = u.toString();
//
const VOLUME_CHART_TOAST_MS = 2000;
const VOLUME_CHART_TOAST_TEXT = "This feature is not finished yet. Wait for it, it'll be cool.";

let volumeChartToastTimer = null;

function showVolumeChartComingSoonToast() {
  const el = document.getElementById("volume-chart-toast");
  if (!el) return;
  el.textContent = VOLUME_CHART_TOAST_TEXT;
  el.hidden = false;
  el.setAttribute("aria-hidden", "false");
  el.classList.add("volume-chart-toast--visible");
  if (volumeChartToastTimer) clearTimeout(volumeChartToastTimer);
  volumeChartToastTimer = setTimeout(() => {
    el.classList.remove("volume-chart-toast--visible");
    el.hidden = true;
    el.setAttribute("aria-hidden", "true");
    volumeChartToastTimer = null;
  }, VOLUME_CHART_TOAST_MS);
}

function closeVolumeDailyChart() {
  const b = document.getElementById("volume-daily-chart-block");
  if (b) b.hidden = true;
  document.getElementById("chart-skeleton-volume-daily")?.classList.add("hidden");
  const inner = document.getElementById("volume-daily-chart-inner");
  if (inner) inner.style.display = "none";
  const msg = document.getElementById("volume-daily-chart-msg");
  if (msg) msg.textContent = "";
  destroyChart("volume-daily-canvas");
  volumeDailySelection = null;
  setVolumeMainView("table");
  const tableInner = document.getElementById("volume-table-inner");
  if (tableInner) tableInner.style.display = "";
}

function buildVolumeTableHandlers() {
  return {
    onDrill: (row) => {
      volumeParentStack.push(volumeParentId);
      volumeParentId = row.exercise_id;
      loadVolumeTable();
    },
    onMinichart: (row) => openVolumeDailyChart(row),
    onDeltaToggle: () => {
      toggleVolumeDeltaDisplayMode();
      renderVolumeTable(lastVolumeTableResults, preferredUnit, volumePeriod, buildVolumeTableHandlers());
    },
  };
}

async function openVolumeDailyChart(row) {
  const block = document.getElementById("volume-daily-chart-block");
  const skel = document.getElementById("chart-skeleton-volume-daily");
  const inner = document.getElementById("volume-daily-chart-inner");
  const vmsg = document.getElementById("volume-daily-chart-msg");
  const vtitle = document.getElementById("volume-daily-title");

  if (block) {
    block.hidden = false;
    setVolumeMainView("chart");
  }

  if (vtitle) {
    vtitle.textContent = row.exercise_name || "Volume";
  }
  if (vmsg) vmsg.textContent = "";

  skel?.classList.remove("hidden");
  if (inner) inner.style.display = "none";
  destroyChart("volume-daily-canvas");

  try {
    const { start, end } = getDateRange();
    const { results: daily = [] } = await fetchTotalVolumeDaily(row.exercise_id, start, end);
    skel?.classList.add("hidden");

    if (!daily.length) {
      if (vmsg) vmsg.textContent = "No day-by-day volume in this range.";
      if (inner) inner.style.display = "none";
      volumeDailySelection = null;
      return;
    }

    volumeDailySelection = {
      exerciseId: row.exercise_id,
      exerciseName: row.exercise_name || "",
    };

    renderVolumeDailyTimeSeries(daily, row.exercise_name, volumeDailyChartType, preferredUnit);
  } catch (e) {
    skel?.classList.add("hidden");
    if (vmsg) vmsg.textContent = "Failed to load daily volume.";
    destroyChart("volume-daily-canvas");
    volumeDailySelection = null;
    if (inner) inner.style.display = "none";
    if (String(e.message || "").includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

function onDateChange() {
  syncDateFilters();
  const active = document.querySelector(".chart-tab.active")?.dataset.tab;
  if (active === "volume" && !dateChangeFromChip) {
    volumePeriod = "all";
    setActivePeriodChip("all");
    resetVolumeDeltaDisplayMode();
  }
  if (active === "favourites") loadFavExercisesChart();
  if (active === "volume") {
    void (async () => {
      await loadVolumeTable();
      if (volumeDailySelection) await reloadVolumeDailyChart();
    })();
    return;
  }
  if (active === "splits") loadWorkoutSplitsChart();
  if (active === "weekdays") loadGymWeekdaysChart();
}

const METRICS_TABS = new Set(["volume", "favourites", "splits", "weekdays"]);
const DEFAULT_METRICS_TAB = "volume";

function getTabFromLocation() {
  const hash = location.hash.replace(/^#/, "");
  if (METRICS_TABS.has(hash)) return hash;

  const tabParam = new URLSearchParams(location.search).get("tab");
  if (METRICS_TABS.has(tabParam)) return tabParam;

  return DEFAULT_METRICS_TAB;
}

function syncTabToLocation(tab) {
  const nextHash = tab === DEFAULT_METRICS_TAB ? "" : `#${tab}`;
  const nextUrl = `${location.pathname}${location.search}${nextHash}`;
  const currentUrl = `${location.pathname}${location.search}${location.hash}`;
  if (currentUrl !== nextUrl) {
    history.replaceState(null, "", nextUrl);
  }
}

function loadTabData(tab) {
  if (tab === "favourites") loadFavExercisesChart();
  if (tab === "volume") loadVolumeTable();
  if (tab === "splits") loadWorkoutSplitsChart();
  if (tab === "weekdays") loadGymWeekdaysChart();
}

function activateTab(tab, { syncLocation = true, loadData = true } = {}) {
  if (!METRICS_TABS.has(tab)) return;

  tabs.forEach((t) => {
    const isActive = t.dataset.tab === tab;
    t.classList.toggle("active", isActive);
    t.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  panels.forEach((p) => p.classList.remove("active"));
  document.getElementById(`tab-${tab}`)?.classList.add("active");

  if (syncLocation) syncTabToLocation(tab);
  if (loadData) loadTabData(tab);
}

const tabs = document.querySelectorAll(".chart-tab");
const panels = document.querySelectorAll(".chart-panel");

activateTab(getTabFromLocation(), { syncLocation: false, loadData: false });

tabs.forEach((tab) => {
  tab.addEventListener("click", () => activateTab(tab.dataset.tab));
});

window.addEventListener("hashchange", () => {
  const tab = getTabFromLocation();
  const active = document.querySelector(".chart-tab.active")?.dataset.tab;
  if (tab !== active) activateTab(tab, { syncLocation: false });
});

async function loadSimpleChart({
  skeletonId,
  innerSelector,
  canvasId,
  emptyMessage,
  errorMessage,
  fetchFn,
  render,
}) {
  const msg = document.getElementById("chart-msg");
  const skeleton = document.getElementById(skeletonId);
  const chartInner = document.querySelector(innerSelector);

  if (msg) msg.textContent = "";
  if (skeleton) skeleton.classList.remove("hidden");
  if (chartInner) chartInner.style.display = "none";
  if (canvasId) destroyChart(canvasId);

  const { start, end } = getDateRange();
  try {
    const data = await fetchFn(start, end);
    const results = data?.results || [];
    if (!results.length) {
      if (msg) msg.textContent = emptyMessage;
      if (canvasId) destroyChart(canvasId);
      if (skeleton) skeleton.classList.add("hidden");
      return;
    }
    if (skeleton) skeleton.classList.add("hidden");
    if (chartInner) chartInner.style.display = "";
    render(results);
  } catch (err) {
    if (msg) msg.textContent = errorMessage;
    if (canvasId) destroyChart(canvasId);
    if (skeleton) skeleton.classList.add("hidden");
    if (String(err.message || "").includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

async function loadFavExercisesChart() {
  await loadSimpleChart({
    skeletonId: "chart-skeleton-favourites",
    innerSelector: "#tab-favourites .chart-inner",
    canvasId: "fav-exercises-canvas",
    emptyMessage: "No data to display for this range.",
    errorMessage: "Failed to load chart data.",
    fetchFn: fetchFavExercises,
    render(results) {
      renderFavExercisesChart(
        results.map((r) => shortLabel(r.exercise_name, 14)),
        results.map((r) => r.counter),
        results.map((r) => r.exercise_name),
        results.map((r) => r.rank ?? 0)
      );
    },
  });
}

async function loadVolumeTable() {
  const msg = document.getElementById("chart-msg");
  const skeleton = document.getElementById("chart-skeleton-volume");

  if (msg) msg.textContent = "";
  // If the daily chart block got hidden while a selection is still set (e.g.
  // after switching tabs), drop the stale selection so the table comes back.
  const dailyBlock = document.getElementById("volume-daily-chart-block");
  if (volumeDailySelection && dailyBlock?.hidden) volumeDailySelection = null;
  if (!volumeDailySelection) setVolumeMainView("table");
  if (skeleton) skeleton.classList.remove("hidden");
  setVolumeTableVisible(false);

  updateVolumeToolbar();

  try {
    const { start, end } = getDateRange();
    const data = await fetchTotalVolume({
      period: volumePeriod,
      parentId: volumeParentId,
      startDate: start,
      endDate: end,
    });
    const results = data?.results || [];

    if (results.length === 0) {
      if (msg) msg.textContent = "No volume data for this period.";
      if (skeleton) skeleton.classList.add("hidden");
      return;
    }

    if (msg) msg.textContent = "";
    if (skeleton) skeleton.classList.add("hidden");

    lastVolumeTableResults = results;
    renderVolumeTable(results, preferredUnit, volumePeriod, buildVolumeTableHandlers());

    setVolumeTableVisible(!volumeDailySelection);
  } catch (err) {
    if (msg) msg.textContent = "Failed to load volume data.";
    if (skeleton) skeleton.classList.add("hidden");

    if (String(err.message || "").includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

async function loadWorkoutSplitsChart() {
  await loadSimpleChart({
    skeletonId: "chart-skeleton-splits",
    innerSelector: "#tab-splits .chart-inner",
    canvasId: "workout-splits-canvas",
    emptyMessage: "No split data for this range.",
    errorMessage: "Failed to load split data.",
    fetchFn: fetchWorkoutSplits,
    render(results) {
      renderWorkoutSplitsChart(
        results.map((r) => r.workout_split),
        results.map((r) => Number(r.set_count) || 0)
      );
    },
  });
}

async function loadGymWeekdaysChart() {
  await loadSimpleChart({
    skeletonId: "chart-skeleton-weekdays",
    innerSelector: "#tab-weekdays .chart-inner",
    canvasId: "gym-weekdays-canvas",
    emptyMessage: "No weekday data for this range.",
    errorMessage: "Failed to load weekday data.",
    fetchFn: fetchGymWeekdays,
    render(results) {
      renderGymWeekdaysChart(
        results.map((r) => r.day_name),
        results.map((r) => Number(r.gym_days) || 0)
      );
    },
  });
}

if (dateFrom) {
  dateFrom.setAttribute("max", TODAY);
  dateFrom.addEventListener("change", onDateChange);
}
if (dateTo) {
  dateTo.setAttribute("max", TODAY);
  dateTo.addEventListener("change", onDateChange);
}
if (dateTo && !dateTo.value) dateTo.value = TODAY;

document.querySelectorAll(".volume-period-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    applyPeriodChip(chip.dataset.period || "all");
  });
});

const volumeBackBtn = document.getElementById("volume-back-btn");
if (volumeBackBtn) {
  volumeBackBtn.addEventListener("click", () => {

    volumeParentId = volumeParentStack.length ? volumeParentStack.pop() : null;
    loadVolumeTable();
  });
}

document.getElementById("volume-daily-back")?.addEventListener("click", closeVolumeDailyChart);
document.getElementById("volume-daily-type-line")?.addEventListener("click", () => {
  volumeDailyChartType = "line";
  document.getElementById("volume-daily-type-line")?.classList.add("is-active");
  document.getElementById("volume-daily-type-bar")?.classList.remove("is-active");
  void reloadVolumeDailyChart();
});
document.getElementById("volume-daily-type-bar")?.addEventListener("click", () => {
  volumeDailyChartType = "bar";
  document.getElementById("volume-daily-type-bar")?.classList.add("is-active");
  document.getElementById("volume-daily-type-line")?.classList.remove("is-active");
  void reloadVolumeDailyChart();
});

const params = new URLSearchParams(window.location.search);
const chartExId = params.get("volumeChart");
const chartName = params.get("volumeChartName");
const placeholder = document.getElementById("volume-chart-placeholder");
if (chartExId && placeholder) {
  placeholder.hidden = false;
  placeholder.textContent =
    "Chart for " +
    (chartName || "exercise #" + chartExId) +
    " — hook up timeseries API next.";
}

async function reloadActiveTab() {
  const active = getTabFromLocation();
  if (active === "favourites") await loadFavExercisesChart();
  if (active === "volume") await loadVolumeTable();
  if (active === "splits") await loadWorkoutSplitsChart();
  if (active === "weekdays") await loadGymWeekdaysChart();
}

window.addEventListener("preferred-unit-changed", async () => {
  await loadPreferredUnit();
  await reloadActiveTab();
});

const initialTab = getTabFromLocation();
void (async () => {
  await loadPreferredUnit();
  setActivePeriodChip(volumePeriod);
  loadTabData(initialTab);
})();
