// ----- API and frontend base URLs -----
if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    var API_BASE = "http://127.0.0.1:8000";
  } else {
    var API_BASE = "https://gym-assistant-2smv.onrender.com";
  }
  var base = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:5500"
    : "https://gym-assistant-6z0m.onrender.com";
  
  // Today's date as YYYY-MM-DD (used for date guards and default end_date)
  var TODAY = new Date().toISOString().slice(0, 10);
  
  /**
   * Returns request headers with JWT for authenticated API calls, or null if not logged in.
   */
  function getAuthHeaders() {
    var token = localStorage.getItem("access_token");
    if (!token) return null;
    return {
      "Authorization": "Bearer " + token,
      "Accept": "application/json",
      "Content-Type": "application/json",
    };
  }
  
  // Single Chart.js instance so we can destroy it before redrawing
  var chartInstance = null;
  
  /**
   * Destroys the current chart if it exists (before loading new data or on error).
   */
  function destroyChart() {
    if (chartInstance) {
      chartInstance.destroy();
      chartInstance = null;
    }
  }
  
  /**
   * Shortens a label to maxLen characters and adds an ellipsis if longer.
   */
  function shortLabel(name, maxLen) {
    maxLen = maxLen || 14;
    if (!name || name.length <= maxLen) return name;
    return name.slice(0, maxLen) + "\u2026";
  }
  
  /**
   * Renders the favourite-exercises chart as horizontal bars.
   * Rank 1 at top, rank X at bottom (API order).
   * Bars animate from left to right on load.
   * Label placement: inside bar (dark text) if bar is wide enough, otherwise to the right (white text).
   */
  function renderPyramidChart(labels, values, fullNames, ranks) {
    destroyChart();
    var canvas = document.getElementById("chart-canvas");
    if (!canvas) return;
  
    var n = values.length;
  
    // Make the chart container tall enough so the scroll wrapper can scroll vertically
    var barHeight = 48;
    var chartInner = canvas.closest(".chart-inner");
    if (chartInner && n) {
      chartInner.style.height = Math.max(320, n * barHeight) + "px";
    }
  
    var isNarrow = window.innerWidth < 600;
    var rankFontSize = isNarrow ? 10 : 14;
    var labelFontSize = isNarrow ? 11 : 12;
  
    // Pre-compute which labels fit inside the bar vs. outside
    var maxValue = Math.max.apply(null, values) || 1;
    var yAxisWidth = 50;
    var chartWidth = canvas.parentElement.clientWidth - yAxisWidth - 16;
  
    var alignPerBar = [];
    var colorPerBar = [];
    for (var i = 0; i < n; i++) {
      var barPixelWidth = (values[i] / maxValue) * chartWidth;
      var text = fullNames[i] + " - " + values[i] + " sets";
      var approxTextWidth = text.length * 7;
      if (barPixelWidth > approxTextWidth) {
        alignPerBar.push("start");
        colorPerBar.push("#0c0c0e");
      } else {
        alignPerBar.push("end");
        colorPerBar.push("#ffffff");
      }
    }
  
    // Colour palette: one colour per bar
    var palette = [
      "rgba(34, 211, 238, 0.7)",
      "rgba(168, 85, 247, 0.7)",
      "rgba(251, 146, 60, 0.7)",
      "rgba(52, 211, 153, 0.7)",
      "rgba(251, 113, 133, 0.7)",
      "rgba(96, 165, 250, 0.7)",
      "rgba(250, 204, 21, 0.7)",
      "rgba(244, 114, 182, 0.7)",
      "rgba(129, 140, 248, 0.7)",
      "rgba(45, 212, 191, 0.7)",
    ];
    var barColors = [];
    var borderColors = [];
    for (var i = 0; i < n; i++) {
      var c = palette[i % palette.length];
      barColors.push(c);
      borderColors.push(c.replace("0.7)", "1)"));
    }
  
    var ctx = canvas.getContext("2d");
    var plugins = [];
    if (typeof ChartDataLabels !== "undefined") plugins.push(ChartDataLabels);
  
    chartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: ranks,
        datasets: [{
          label: "Workouts",
          data: values,
          backgroundColor: barColors,
          borderColor: borderColors,
          borderWidth: 1,
        }],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        // Bars grow from left to right
        animation: {
          duration: 1000,
          easing: "easeOutQuart",
        },
        layout: { padding: { left: 8, right: 8 } },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function(ctx) {
                var name = fullNames[ctx.dataIndex] || ctx.chart.data.labels[ctx.dataIndex] || "";
                return name + " - " + (ctx.raw || 0) + " sets";
              },
            },
          },
          datalabels: {
            anchor: "end",
            offset: 6,
            font: { size: labelFontSize, weight: "bold" },
            formatter: function(value, ctx) {
              var name = fullNames[ctx.dataIndex] || ctx.chart.data.labels[ctx.dataIndex] || "";
              return name + " - " + (value || 0) + " sets";
            },
            align: function(ctx) {
              return alignPerBar[ctx.dataIndex] || "end";
            },
            color: function(ctx) {
              return colorPerBar[ctx.dataIndex] || "#ffffff";
            },
          },
        },
        scales: {
          x: { beginAtZero: true, display: false },
          y: {
            display: true,
            grid: { display: false },
            ticks: {
              color: "#f4f4f5",
              font: { size: rankFontSize, weight: "600" },
              autoSkip: false,
              callback: function(value) {
                return "#" + (value + 1);
              },
            },
          },
        },
      },
      plugins: plugins,
    });
  }
  
  /**
   * Builds the favourite-exercises API URL, appending start_date and end_date
   * query params only when the user has picked dates.
   */
  function getChartUrl() {
    var url = API_BASE + "/api/v1/favourite-exercises";
    var fromEl = document.getElementById("start_date");
    var toEl = document.getElementById("end_date");
    var from = fromEl && fromEl.value;
    var to = toEl && toEl.value;
    var params = new URLSearchParams();
    if (from) params.set("start_date", from);
    if (to) params.set("end_date", to);
    var qs = params.toString();
    return qs ? url + "?" + qs : url;
  }
  
  /**
   * Ensures from <= to and neither date is in the future.
   * If end_date > today, clamp it to today.
   * If start_date > end_date, set end_date = start_date.
   */
  function syncDateFilters() {
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
  
  /**
   * Called when either date input changes: sync the range then refetch chart data.
   */
  function onDateChange() {
    syncDateFilters();
    fetchChartData();
  }
  
  /**
   * Fetches favourite-exercises from the API and renders the chart.
   * Shows backend error messages or a generic fallback in #chart-msg on failure.
   */
  async function fetchChartData() {
    var msg = document.getElementById("chart-msg");
    var skeleton = document.getElementById("chart-skeleton");
    var chartInner = document.querySelector(".chart-inner");
    if (msg) msg.textContent = "";
  
    // Show skeleton, hide chart canvas while loading
    if (skeleton) skeleton.classList.remove("hidden");
    if (chartInner) chartInner.style.display = "none";
  
    var headers = getAuthHeaders();
    try {
      var res = await fetch(getChartUrl(), { headers: headers });
      var data = await res.json().catch(function() { return {}; });
  
      if (!res.ok) {
        var errText = (data.detail != null) ? data.detail : (data.message || res.statusText || "Failed to load chart data.");
        if (msg) msg.textContent = errText;
        destroyChart();
        if (skeleton) skeleton.classList.add("hidden");
        return;
      }
      if (res.status === 401) {
        window.location.replace(base + "/pages/auth/login.html");
        return;
      }
  
      var results = (data && data.results) ? data.results : [];
      if (results.length === 0) {
        if (msg) msg.textContent = "No data to display for this range.";
        destroyChart();
        if (skeleton) skeleton.classList.add("hidden");
        return;
      }
  
      var labels = results.map(function(r) { return shortLabel(r.exercise_name, 14); });
      var fullNames = results.map(function(r) { return r.exercise_name; });
      var values = results.map(function(r) { return r.counter; });
      var ranks = results.map(function(r) { return r.rank != null ? r.rank : 0; });
  
      // Hide skeleton, show chart canvas, then render
      if (skeleton) skeleton.classList.add("hidden");
      if (chartInner) chartInner.style.display = "";
      renderPyramidChart(labels, values, fullNames, ranks);
    } catch (err) {
      if (msg) msg.textContent = "Failed to load chart data.";
      if (skeleton) skeleton.classList.add("hidden");
    }
  }
  
  // Wire date inputs and set max attribute so the browser prevents picking future dates
  var dateFrom = document.getElementById("start_date");
  var dateTo = document.getElementById("end_date");
  if (dateFrom) {
    dateFrom.setAttribute("max", TODAY);
    dateFrom.addEventListener("change", onDateChange);
  }
  if (dateTo) {
    dateTo.setAttribute("max", TODAY);
    dateTo.addEventListener("change", onDateChange);
  }
  
  // Default end_date to today
  if (dateTo && !dateTo.value) {
    dateTo.value = TODAY;
  }
  
  fetchChartData();