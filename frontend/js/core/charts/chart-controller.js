// This here should control which charts are being displayed in based on which tab is being clicked

import { BASE, TODAY, syncDateFilters } from '../../utils.js';
import { 
  renderFavExercisesChart,
  shortLabel, 
  destroyChart } from './chart-renderers.js';
import { fetchFavExercises } from './data-fetch.js';


function onDateChange(){
  syncDateFilters();
  loadFavExercisesChart();
}

// Tab logic
const tabs = document.querySelectorAll(".chart-tab"); // need . because that is how queryselector works plm
const panels = document.querySelectorAll(".chart-panel");

tabs.forEach(tab => {
  tab.addEventListener("click", () => {
    //Remove active class from all tabs
    tabs.forEach(t => t.classList.remove("active"));
    // Add active to selected tab
    tab.classList.add("active");

    const target = tab.dataset.tab;
    // hide panels
    panels.forEach(p => p.classList.remove("active"));
    // show target panel
    const panel = document.getElementById(`tab-${target}`);
    if (panel) panel.classList.add("active");
      
    // pick what chart to show
    if (target === "favourites") loadFavExercisesChart();
    // else if (target === "volume") loadVolumeChart(); // future chart

  });
});

// main function for favourite exercises
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

    // Map API data to chart arrays
    const labels = results.map(r => shortLabel(r.exercise_name, 14));
    const fullNames = results.map(r => r.exercise_name);
    const values = results.map(r => r.counter);
    const ranks = results.map(r => r.rank ?? 0);

    if (skeleton) skeleton.classList.add("hidden");
    if (chartInner) chartInner.style.display = "";
    renderFavExercisesChart(labels, values, fullNames, ranks);

  } catch (err) {
    if (msg) msg.textContent = "Failed to load chart data.";
    destroyChart();
    if (skeleton) skeleton.classList.add("hidden");

    // Optional: redirect to login if 401
    if (err.message.includes("401")) {
      window.location.replace(BASE + "/pages/auth/login.html");
    }
  }
}

// Wire date inputs
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


// initial load
const defaultTab = document.querySelector(".chart-tab.active")?.dataset.tab || "favourites";
if (defaultTab === "favourites") loadFavExercisesChart();

