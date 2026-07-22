// Controls which content loads per tab and wires shared date controls.

import { BASE, TODAY, syncDateFilters, getTabFromLocation, syncTabToLocation } from "../../utils.js?v=3";
import { getPreferredUnit, unitSuffix } from "../../user-preferences.js";
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
  renderSessionsTable,
  toggleVolumeDeltaDisplayMode,
  resetVolumeDeltaDisplayMode,
  formatVolume,
} from "./chart-renderers.js?v=13";
import { fetchFavExercises, fetchGymWeekdays, fetchTotalVolume, fetchTotalVolumeDaily, fetchWorkoutSessions, fetchWorkoutSplits } from "./data-fetch.js?v=5";

let volumeParentId = null;
/** Stack of { id, name, total_volume } for breadcrumb while drilling. */
const volumeParentStack = [];
let volumePeriod = "all";
/** Skip resetting to All when date inputs are updated by a period chip. */
let dateChangeFromChip = false;

function redirectToLogin() {
  window.location.replace(BASE + "/pages/auth/login.html");
}

/** While the daily chart panel is open, refetch daily volume on date change. */
let volumeDailySelection = null; // { exerciseId: number, exerciseName: string } | null
let volumeDailyChartType = "line"; // "line" | "bar"
let preferredUnit = getPreferredUnit();
/** Cached for click-to-toggle delta display without refetching. */
let lastVolumeTableResults = [];
/** Cached sessions table payload for delta toggle re-render. */
let lastSessionsResults = [];
let lastSessionsComparisons = {};

const dateFrom = document.getElementById("start_date");
const dateTo = document.getElementById("end_date");

function getPeriodDateRange(period) {
  const today = new Date();
  const end = TODAY;
  if (period === "wtd") {
    const monday = new Date(today);
    const isoDay = monday.getDay() === 0 ? 7 : monday.getDay();
    monday.setDate(monday.getDate() - (isoDay - 1));
    // Local calendar date (not UTC) — matches TODAY and other page helpers.
    const start =
      monday.getFullYear() +
      "-" +
      String(monday.getMonth() + 1).padStart(2, "0") +
      "-" +
      String(monday.getDate()).padStart(2, "0");
    return { start, end };
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
  const activePanel = document.querySelector(".chart-panel.active") || document.getElementById("tab-volume");
  const chips = activePanel
    ? activePanel.querySelectorAll(".volume-period-chip")
    : document.querySelectorAll(".volume-period-chip");
  chips.forEach((el) => {
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
  void reloadActiveTab();
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
  // Metrics prefers localStorage (quick KG/LBS toggle) over the server default.
  // Profile remains the durable sync path for preferred_unit.
  preferredUnit = getPreferredUnit();
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
      redirectToLogin();
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
  const periodChips = document.querySelector("#tab-volume .volume-period-chips");
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
  const crumb = document.getElementById("volume-breadcrumb");
  if (!crumb) return;
  if (!volumeParentStack.length) {
    crumb.textContent = "";
    return;
  }
  // Roots are non-overlapping; summing stack totals would double-count ancestors.
  // Show the path of names and the current parent's own total (last stack entry).
  const path = volumeParentStack
    .map((entry) => shortLabel(entry.name || "Exercise", 18))
    .join(" → ");
  const current = volumeParentStack[volumeParentStack.length - 1];
  crumb.textContent = `${path} — ${formatVolume(current.total_volume, preferredUnit)} ${unitSuffix(preferredUnit)}`;
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
      volumeParentStack.push({
        id: volumeParentId,
        name: row.exercise_name || "",
        total_volume: Number(row.total_volume) || 0,
      });
      volumeParentId = row.exercise_id;
      loadVolumeTable();
    },
    onMinichart: (row) => openVolumeDailyChart(row),
    onDeltaToggle: () => {
      toggleVolumeDeltaDisplayMode();
      renderVolumeTable(lastVolumeTableResults, preferredUnit, volumePeriod, buildVolumeTableHandlers());
      if (lastSessionsResults.length) {
        renderSessionsTable(
          lastSessionsResults,
          volumePeriod,
          lastSessionsComparisons,
          buildVolumeTableHandlers().onDeltaToggle
        );
      }
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
      redirectToLogin();
    }
  }
}

function onDateChange() {
  syncDateFilters();
  const active = document.querySelector(".chart-tab.active")?.dataset.tab;
  if ((active === "volume" || active === "sessions") && !dateChangeFromChip) {
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
  if (active === "sessions") loadWorkoutSessionsTable();
  if (active === "splits") loadWorkoutSplitsChart();
  if (active === "weekdays") loadGymWeekdaysChart();
}

const METRICS_TABS = new Set(["volume", "favourites", "sessions", "splits", "weekdays"]);
const DEFAULT_METRICS_TAB = "volume";

function loadTabData(tab) {
  if (tab === "favourites") loadFavExercisesChart();
  if (tab === "volume") loadVolumeTable();
  if (tab === "sessions") loadWorkoutSessionsTable();
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

  if (syncLocation) syncTabToLocation(tab, DEFAULT_METRICS_TAB);
  if (loadData) loadTabData(tab);
}

const tabs = document.querySelectorAll(".chart-tab");
const panels = document.querySelectorAll(".chart-panel");

activateTab(getTabFromLocation(METRICS_TABS, DEFAULT_METRICS_TAB), { syncLocation: false, loadData: false });

tabs.forEach((tab) => {
  tab.addEventListener("click", () => activateTab(tab.dataset.tab));
});

window.addEventListener("hashchange", () => {
  const tab = getTabFromLocation(METRICS_TABS, DEFAULT_METRICS_TAB);
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
      redirectToLogin();
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
      redirectToLogin();
    }
  }
}

async function loadWorkoutSessionsTable() {
  const msg = document.getElementById("chart-msg");
  const skeleton = document.getElementById("chart-skeleton-sessions");
  const chartInner = document.getElementById("sessions-table-inner");

  if (msg) msg.textContent = "";
  if (skeleton) skeleton.classList.remove("hidden");
  if (chartInner) chartInner.style.display = "none";

  const { start, end } = getDateRange();
  try {
    const data = await fetchWorkoutSessions(start, end);
    const results = data?.results || [];
    const comparisons = data?.comparisons || {};
    if (!results.length) {
      if (msg) msg.textContent = "No sessions in this range.";
      if (skeleton) skeleton.classList.add("hidden");
      lastSessionsResults = [];
      lastSessionsComparisons = {};
      return;
    }
    if (skeleton) skeleton.classList.add("hidden");
    if (chartInner) chartInner.style.display = "";
    lastSessionsResults = results;
    lastSessionsComparisons = comparisons;
    const onDeltaToggle = () => {
      toggleVolumeDeltaDisplayMode();
      if (lastVolumeTableResults.length) {
        renderVolumeTable(lastVolumeTableResults, preferredUnit, volumePeriod, buildVolumeTableHandlers());
      }
      renderSessionsTable(lastSessionsResults, volumePeriod, lastSessionsComparisons, onDeltaToggle);
    };
    renderSessionsTable(results, volumePeriod, comparisons, onDeltaToggle);
  } catch (err) {
    if (msg) msg.textContent = "Failed to load sessions.";
    if (skeleton) skeleton.classList.add("hidden");
    if (String(err.message || "").includes("401")) {
      redirectToLogin();
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

document.querySelectorAll("#tab-volume .volume-period-chip, #tab-sessions .volume-period-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    applyPeriodChip(chip.dataset.period || "all");
  });
});

const volumeBackBtn = document.getElementById("volume-back-btn");
if (volumeBackBtn) {
  volumeBackBtn.addEventListener("click", () => {
    const prev = volumeParentStack.length ? volumeParentStack.pop() : null;
    volumeParentId = prev ? prev.id : null;
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
  const active = getTabFromLocation(METRICS_TABS, DEFAULT_METRICS_TAB);
  if (active === "favourites") await loadFavExercisesChart();
  if (active === "volume") await loadVolumeTable();
  if (active === "sessions") await loadWorkoutSessionsTable();
  if (active === "splits") await loadWorkoutSplitsChart();
  if (active === "weekdays") await loadGymWeekdaysChart();
}

window.addEventListener("preferred-unit-changed", async () => {
  await loadPreferredUnit();
  await reloadActiveTab();
});

const initialTab = getTabFromLocation(METRICS_TABS, DEFAULT_METRICS_TAB);
void (async () => {
  await loadPreferredUnit();
  setActivePeriodChip(volumePeriod);
  loadTabData(initialTab);
})();
