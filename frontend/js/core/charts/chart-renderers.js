// Keep a single chart instance so we can destroy before redrawing

let chartInstance = null;

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

export function formatVolumeKg(n) {
  if (n == null || Number.isNaN(Number(n))) return "—";
  const v = Number(n);
  const opts =
    v >= 100
      ? { maximumFractionDigits: 0, minimumFractionDigits: 0 }
      : { maximumFractionDigits: 1, minimumFractionDigits: 1 };
  return new Intl.NumberFormat("en-US", opts).format(v);
}

export function renderVolumeTable(results, handlers) {
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
    volTd.textContent = formatVolumeKg(row.total_volume_kg);

    tr.append(rankTd, nameTd, sparkTd, volTd);
    tbody.appendChild(tr);
  }
}

const VOL_LINE = "rgb(34, 211, 238)";

export function renderVolumeDailyTimeSeries(labels, values, exerciseName, type) {
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

  chartInstance = new Chart(canvas.getContext("2d"), {
    type: t,
    data: {
      labels,
      datasets: [
        {
          label: exerciseName ? "Volume (kg) — " + exerciseName : "Volume (kg)",
          data: values,
          borderColor: VOL_LINE,
          backgroundColor:
            t === "bar" ? "rgba(34, 211, 238, 0.45)" : "rgba(34, 211, 238, 0.15)",
          fill: t === "line",
          tension: 0.25,
          borderWidth: t === "line" ? 2 : 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: "#e4e4e7" } },
        tooltip: {
          callbacks: {
            label: (c) => formatVolumeKg(c.raw) + " kg",
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
          ticks: { display: false },
          grid: { color: "rgba(255,255,255,0.06)" },
        },
      },
    },
    plugins,
  });
}
