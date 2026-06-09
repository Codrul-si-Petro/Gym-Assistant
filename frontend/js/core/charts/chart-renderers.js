// Keep a single chart instance so we can destroy before redrawing

let chartInstance = null;

function getCssVar(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
}

function getChartPalette() {
  return [
    "rgba(34, 211, 238, 0.75)",
    "rgba(168, 85, 247, 0.75)",
    "rgba(251, 146, 60, 0.75)",
    "rgba(52, 211, 153, 0.75)",
    "rgba(251, 113, 133, 0.75)",
    "rgba(96, 165, 250, 0.75)",
    "rgba(250, 204, 21, 0.75)",
    "rgba(244, 114, 182, 0.75)",
  ];
}

export function destroyChart() {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

export function shortLabel(name, maxLen = 14) {
  if (!name || name.length <= maxLen) return name;
  return name.slice(0, maxLen) + "\u2026";
}

function unitSuffix(unit) {
  return unit === "LBS" ? "lbs" : "kg";
}

function toDisplayUnit(kgValue, unit) {
  const kg = Number(kgValue) || 0;
  return unit === "LBS" ? kg * 2.2046226218 : kg;
}


export function renderFavExercisesChart(labels, values, fullNames, ranks){
  destroyChart();
  const canvas = document.getElementById("fav-exercises-canvas");
  if (!canvas) return;
    var n = values.length;
  
    // Make the chart container tall enough so the scroll wrapper can scroll vertically
    var barHeight = 48;
    var chartInner = canvas.closest(".chart-inner");
    if (chartInner && n) {
      chartInner.style.height = Math.max(320, n * barHeight) + "px";
    }
  
    var isNarrow = window.innerWidth < 414;
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
    var palette = getChartPalette();
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
          borderRadius: 10,
          borderSkipped: false,
          barThickness: 26,
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
          x: { beginAtZero: true, display: false, grid: { color: "rgba(255,255,255,0.04)" } },
          y: {
            display: true,
            grid: { display: false },
            ticks: {
              color: getCssVar("--text-primary", "#f4f4f5"),
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

export function formatVolume(n, unit = "KG") {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const v = toDisplayUnit(n, unit);
  const opts =
    v >= 100
      ? { maximumFractionDigits: 0, minimumFractionDigits: 0 }
      : { maximumFractionDigits: 1, minimumFractionDigits: 1 };
  return new Intl.NumberFormat("en-US", opts).format(v);
}

export function renderVolumeTable(results, unit, handlers) {
  const tbody = document.getElementById("volume-table-body");
  if (!tbody) return;

  const onDrill = handlers?.onDrill;
  const onMinichart = handlers?.onMinichart;

  tbody.replaceChildren();

  for (const row of results) {
    const tr = document.createElement("tr");

    const rankTd = document.createElement("td");
    rankTd.className = "volume-col-rank";
    rankTd.textContent = String(row.rank ?? "");

    const nameTd = document.createElement("td");
    nameTd.className = "volume-col-exercise";
    const canDrill = row.is_leaf === false;
    if (canDrill && onDrill) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "volume-exercise-drill";
      const label = document.createElement("span");
      label.className = "volume-exercise-drill-label";
      label.textContent = row.exercise_name || "";
      const chev = document.createElement("span");
      chev.className = "volume-exercise-drill-chevron";
      chev.setAttribute("aria-hidden", "true");
      chev.textContent = ">";
      btn.append(label, chev);
      btn.addEventListener("click", () => onDrill(row));
      nameTd.appendChild(btn);
    } else {
      nameTd.textContent = row.exercise_name || "";
    }

    const sparkTd = document.createElement("td");
    sparkTd.className = "volume-col-chart";
    const sparkBtn = document.createElement("button");
    sparkBtn.type = "button";
    sparkBtn.className = "volume-minichart-placeholder";
    sparkBtn.setAttribute(
      "aria-label",
      "Open volume chart for " + (row.exercise_name || "exercise")
    );
    sparkBtn.textContent = "◇";
    sparkBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (onMinichart) onMinichart(row);
    });
    sparkTd.appendChild(sparkBtn);

    const volTd = document.createElement("td");
    volTd.className = "volume-col-vol";
    volTd.textContent = formatVolume(row.total_volume_kg, unit);

    tr.append(rankTd, nameTd, sparkTd, volTd);
    tbody.appendChild(tr);
  }
}

export function renderVolumeDailyTimeSeries(labels, values, exerciseName, type, unit = "KG") {
  destroyChart();
  const canvas = document.getElementById("volume-daily-canvas");
  if (!canvas) return;

  const box = document.getElementById("volume-daily-chart-inner");
  const sizeEl = document.getElementById("volume-daily-chart-size");
  const scrollEl = document.getElementById("volume-daily-chart-scroll");
  const minPxPerPoint = 14;

  if (box) {
    box.style.display = "";
    box.style.height = "280px";
  }
  if (sizeEl && scrollEl && labels.length) {
    const minW = Math.max(scrollEl.clientWidth || 400, labels.length * minPxPerPoint);
    sizeEl.style.width = minW + "px";
    sizeEl.style.height = "280px";
  }

  const t = type || "line";
  const plugins = typeof ChartDataLabels !== "undefined" ? [ChartDataLabels] : [];
  const accent = getCssVar("--accent-secondary", "#22d3ee");
  const accentSoft = "rgba(34, 211, 238, 0.2)";

  chartInstance = new Chart(canvas.getContext("2d"), {
    type: t,
    data: {
      labels,
      datasets: [
        {
          label: exerciseName ? `Volume (${unitSuffix(unit)}) — ${exerciseName}` : `Volume (${unitSuffix(unit)})`,
          data: values.map((v) => toDisplayUnit(v, unit)),
          borderColor: accent,
          backgroundColor:
            t === "bar" ? accent : accentSoft,
          fill: t === "line",
          tension: 0.25,
          borderWidth: t === "line" ? 3 : 1,
          borderRadius: t === "bar" ? 10 : 0,
          maxBarThickness: t === "bar" ? 28 : undefined,
          pointRadius: t === "line" ? 2.5 : 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: getCssVar("--text-primary", "#e4e4e7") } },
        tooltip: {
          callbacks: {
            label: (c) => `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(c.raw)} ${unitSuffix(unit)}`,
          },
        },
        datalabels: { display: false },
      },
      scales: {
        x: {
          ticks: { display: false },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: { color: getCssVar("--text-secondary", "#a1a1aa") },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
      },
    },
    plugins,
  });
}

export function renderWorkoutSplitsChart(labels, values) {
  destroyChart();
  const canvas = document.getElementById("workout-splits-canvas");
  if (!canvas) return;
  const palette = getChartPalette();
  chartInstance = new Chart(canvas.getContext("2d"), {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: labels.map((_, i) => palette[i % palette.length]),
        borderColor: getCssVar("--bg-primary", "#000"),
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "52%",
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: getCssVar("--text-primary", "#f4f4f5") },
        },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.raw} sets`,
          },
        },
      },
    },
  });
}

export function renderGymWeekdaysChart(labels, values) {
  destroyChart();
  const canvas = document.getElementById("gym-weekdays-canvas");
  if (!canvas) return;
  const accent = getCssVar("--accent-secondary", "#22d3ee");
  chartInstance = new Chart(canvas.getContext("2d"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Gym days",
        data: values,
        backgroundColor: "rgba(34, 211, 238, 0.75)",
        borderColor: accent,
        borderWidth: 1,
        borderRadius: 10,
        maxBarThickness: 36,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: getCssVar("--text-secondary", "#a1a1aa") },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: { color: getCssVar("--text-secondary", "#a1a1aa"), precision: 0 },
          grid: { color: getCssVar("--border-subtle", "rgba(255,255,255,0.06)") },
        },
      },
    },
  });
}
