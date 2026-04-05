// Controls which content loads per tab and wires shared date controls.

import { BASE, TODAY, syncDateFilters } from "../../utils.js";
import {
  renderFavExercisesChart,
  shortLabel,
  destroyChart,
  renderVolumeTable,
} from "./chart-renderers.js";
import { fetchFavExercises, fetchTotalVolume } from "./data-fetch.js";

let volumeParentId = null;
const volumeParentStack = [];

function setVolumeTableVisible(visible) {
  const inner = document.getElementById("volume-table-inner");
  if (inner) inner.style.display = visible ? "" : "none";
}

function updateVolumeToolbar() {
  const toolbar = document.getElementById("volume-toolbar");
  if (!toolbar) return;
  toolbar.hidden = volumeParentId == null;
}

function navigateToVolumeChart(exerciseId, exerciseName) {
  const u = new URL(window.location.href);
  u.searchParams.set("volumeChart", String(exerciseId));
  if (exerciseName) u.searchParams.set("volumeChartName", exerciseName);
  if (dateFrom?.value) u.searchParams.set("start_date", dateFrom.value);
  if (dateTo?.value) u.searchParams.set("end_date", dateTo.value);
  window.location.href = u.toString();
}

function onDateChange() {
  syncDateFilters();
  const active = document.querySelector(".chart-tab.active")?.dataset.tab;
  if (active === "favourites") loadFavExercisesChart();
  if (active === "volume") loadVolumeTable();
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
      onMinichart: (row) => {
        navigateToVolumeChart(row.exercise_id, row.exercise_name);
      },
    });

    setVolumeTableVisible(true);
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
