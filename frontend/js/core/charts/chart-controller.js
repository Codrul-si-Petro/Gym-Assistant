// Controls which content loads per tab and wires shared date controls.

import { BASE, TODAY, syncDateFilters } from "../../utils.js";
import {
  renderFavExercisesChart,
  shortLabel,
  destroyChart,
  renderVolumeTable,
  renderVolumeDailyTimeSeries,
} from "./chart-renderers.js";
import { fetchFavExercises, fetchTotalVolume, fetchTotalVolumeDaily } from "./data-fetch.js";

let volumeParentId = null;
const volumeParentStack = [];

/** While the daily chart panel is open, refetch daily volume on date change. */
let volumeDailySelection = null; // { exerciseId: number, exerciseName: string } | null
let volumeDailyChartType = "line"; // "line" | "bar"

async function reloadVolumeDailyChart() {
  if (!volumeDailySelection) return;
  const skel = document.getElementById("chart-skeleton-volume-daily");
  const inner = document.getElementById("volume-daily-chart-inner");
  const vmsg = document.getElementById("volume-daily-chart-msg");
  skel?.classList.remove("hidden");
  if (inner) inner.style.display = "none";
  destroyChart();
  if (vmsg) vmsg.textContent = "";
  try {
    const { results: daily = [] } = await fetchTotalVolumeDaily(
      volumeDailySelection.exerciseId,
      dateFrom?.value,
      dateTo?.value
    );
    skel?.classList.add("hidden");
    if (!daily.length) {
      if (vmsg) vmsg.textContent = "No day-by-day volume in this range.";
      if (inner) inner.style.display = "none";
      return;
    }
    renderVolumeDailyTimeSeries(
      daily.map((r) => String(r.date)),
      daily.map((r) => Number(r.total_volume_kg) || 0),
      volumeDailySelection.exerciseName,
      volumeDailyChartType
    );
  } catch (e) {
    skel?.classList.add("hidden");
    if (vmsg) vmsg.textContent = "Failed to load daily volume.";
    destroyChart();
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
  if (!scrollWrap || !chartBlock) return;

  if (mode === "chart") {
    scrollWrap.classList.add("volume-mode-chart");
    chartBlock.hidden = false;
    setVolumeTableVisible(false); // hide table by JS so swap works without relying on CSS alone
  } else {
    scrollWrap.classList.remove("volume-mode-chart");
    chartBlock.hidden = true;
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

function onDateChange() {
  syncDateFilters();
  const active = document.querySelector(".chart-tab.active")?.dataset.tab;
  if (active === "favourites") loadFavExercisesChart();
  if (active === "volume") {
    void (async () => {
      await loadVolumeTable();
      if (volumeDailySelection) await reloadVolumeDailyChart();
    })();
  }
}

const tabs = document.querySelectorAll(".chart-tab");
const panels = document.querySelectorAll(".chart-panel");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");

    const target = tab.dataset.tab;
    panels.forEach((p) => p.classList.remove("active"));
    const panel = document.getElementById(`tab-${target}`);
    if (panel) panel.classList.add("active");

    if (target === "favourites") loadFavExercisesChart();
    if (target === "volume") loadVolumeTable();
  });
});

async function loadFavExercisesChart() {
  const msg = document.getElementById("chart-msg");
  const skeleton = document.getElementById("chart-skeleton-favourites");
  const chartInner = document.querySelector("#tab-favourites .chart-inner");

  if (msg) msg.textContent = "";
  setVolumeMainView("table");
  if (skeleton) skeleton.classList.remove("hidden");
  if (chartInner) chartInner.style.display = "none";

  try {
    const data = await fetchFavExercises(dateFrom.value, dateTo.value);
    const results = data?.results || [];

    if (results.length === 0) {
      if (msg) msg.textContent = "No data to display for this range.";
      destroyChart();
      if (skeleton) skeleton.classList.add("hidden");
      return;
    }

    const labels = results.map((r) => shortLabel(r.exercise_name, 14));
    const fullNames = results.map((r) => r.exercise_name);
    const values = results.map((r) => r.counter);
    const ranks = results.map((r) => r.rank ?? 0);

    if (skeleton) skeleton.classList.add("hidden");
    if (chartInner) chartInner.style.display = "";
    renderFavExercisesChart(labels, values, fullNames, ranks);
  } catch (err) {
    if (msg) msg.textContent = "Failed to load chart data.";
    destroyChart();
    if (skeleton) skeleton.classList.add("hidden");

    if (String(err.message || "").includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

async function loadVolumeTable() {
  const msg = document.getElementById("chart-msg");
  const skeleton = document.getElementById("chart-skeleton-volume");

  if (msg) msg.textContent = "";
  if (!volumeDailySelection) setVolumeMainView("table");
  if (skeleton) skeleton.classList.remove("hidden");
  setVolumeTableVisible(false);

  updateVolumeToolbar();

  try {
    const data = await fetchTotalVolume(
      dateFrom.value,
      dateTo.value,
      volumeParentId
    );
    const results = data?.results || [];

    if (results.length === 0) {
      if (msg) msg.textContent = "No volume data for this range.";
      if (skeleton) skeleton.classList.add("hidden");
      return;
    }

    if (msg) msg.textContent = "";
    if (skeleton) skeleton.classList.add("hidden");

    renderVolumeTable(results, {
      onDrill: (row) => {
        volumeParentStack.push(volumeParentId);
        volumeParentId = row.exercise_id;
        loadVolumeTable();
      },
      onMinichart: async (row) => {
        // DOM for daily chart panel, loading skeleton, canvas wrapper, messages, title
        const block = document.getElementById("volume-daily-chart-block");
        const skel = document.getElementById("chart-skeleton-volume-daily");
        const inner = document.getElementById("volume-daily-chart-inner");
        const vmsg = document.getElementById("volume-daily-chart-msg");
        const vtitle = document.getElementById("volume-daily-title");

        // Show chart panel and swap layout: table hidden, chart block visible (CSS .volume-mode-chart)
        if (block) {
          block.hidden = false;
          setVolumeMainView("chart");
        }

        if (vtitle) {
          vtitle.textContent = row.exercise_name
            ? "Volume by day: " + row.exercise_name
            : "Volume by day";
        }
        if (vmsg) vmsg.textContent = "";

        // Daily skeleton while API loads; hide canvas until we have data
        skel?.classList.remove("hidden");
        if (inner) inner.style.display = "none";
        destroyChart();

        try {
          const { results: daily = [] } = await fetchTotalVolumeDaily(
            row.exercise_id,
            dateFrom?.value,
            dateTo?.value
          );
          skel?.classList.add("hidden");

          if (!daily.length) {
            if (vmsg) {
              vmsg.textContent = "No day-by-day volume in this range.";
            }
            if (inner) inner.style.display = "none";
              volumeDailySelection = null;
            return;
          }

          volumeDailySelection = {
            exerciseId: row.exercise_id,
            exerciseName: row.exercise_name || "",
          };

          renderVolumeDailyTimeSeries(
            daily.map((r) => String(r.date)),
            daily.map((r) => Number(r.total_volume_kg) || 0),
            row.exercise_name,
            volumeDailyChartType
          );
        } catch (e) {
          skel?.classList.add("hidden");
          if (vmsg) vmsg.textContent = "Failed to load daily volume.";
          destroyChart();
          volumeDailySelection = null;
          if (inner) inner.style.display = "none";
          if (String(e.message || "").includes("401")) {
            window.location.replace(BASE + "/pages/auth/login.html");
          }
        }
      },
    });

    setVolumeTableVisible(!volumeDailySelection);
  } catch (err) {
    if (msg) msg.textContent = "Failed to load volume data.";
    if (skeleton) skeleton.classList.add("hidden");

    if (String(err.message || "").includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

const dateFrom = document.getElementById("start_date");
const dateTo = document.getElementById("end_date");
if (dateFrom) {
  dateFrom.setAttribute("max", TODAY);
  dateFrom.addEventListener("change", onDateChange);
}
if (dateTo) {
  dateTo.setAttribute("max", TODAY);
  dateTo.addEventListener("change", onDateChange);
}
if (dateTo && !dateTo.value) dateTo.value = TODAY;

const volumeBackBtn = document.getElementById("volume-back-btn");
if (volumeBackBtn) {
  volumeBackBtn.addEventListener("click", () => {

    volumeParentId = volumeParentStack.length ? volumeParentStack.pop() : null;
    loadVolumeTable();
  });
}

document.getElementById("volume-daily-close")?.addEventListener("click", () => {
  const b = document.getElementById("volume-daily-chart-block");
  if (b) b.hidden = true;
  document.getElementById("chart-skeleton-volume-daily")?.classList.add("hidden");
  const inner = document.getElementById("volume-daily-chart-inner");
  if (inner) inner.style.display = "none";
  document.getElementById("volume-daily-chart-msg") &&
    (document.getElementById("volume-daily-chart-msg").textContent = "");
  destroyChart();
  volumeDailySelection = null;
  setVolumeMainView("table");
  const tableInner = document.getElementById("volume-table-inner");
  if (tableInner) tableInner.style.display = "";
});
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

const defaultTab =
  document.querySelector(".chart-tab.active")?.dataset.tab || "favourites";
if (defaultTab === "favourites") loadFavExercisesChart();
if (defaultTab === "volume") loadVolumeTable();
