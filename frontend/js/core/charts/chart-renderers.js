// Keep chart instances per canvas so tabs do not clobber each other.

const chartInstances = new Map();

function getCanvasId(canvas) {
  return canvas?.id || "default";
}

export function destroyChart(canvasId) {
  if (canvasId) {
    const instance = chartInstances.get(canvasId);
    if (instance) {
      instance.destroy();
      chartInstances.delete(canvasId);
    }
    return;
  }
  chartInstances.forEach((instance) => instance.destroy());
  chartInstances.clear();
}

function getCssVar(name, fallback) {
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
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


/**
 * Renders a modern ranked list with gradient progress bars.
 * items: [{ rank, label, valueText, percent }]
 */
function renderStatList(listId, items) {
  const list = document.getElementById(listId);
  if (!list) return;
  list.replaceChildren();

  const fills = [];
  for (const item of items) {
    const li = document.createElement("li");
    li.className = item.rank ? "stat-row" : "stat-row stat-row--no-rank";

    let rank = null;
    if (item.rank) {
      rank = document.createElement("span");
      rank.className = "stat-rank";
      rank.textContent = item.rank;
    }

    const name = document.createElement("span");
    name.className = "stat-name";
    name.textContent = item.label;
    name.title = item.label;

    const value = document.createElement("span");
    value.className = "stat-value";
    value.textContent = item.valueText;

    const track = document.createElement("div");
    track.className = "stat-bar-track";
    const fill = document.createElement("div");
    fill.className = "stat-bar-fill";
    track.appendChild(fill);
    fills.push([fill, Math.max(0, Math.min(100, item.percent))]);

    if (rank) li.append(rank);
    li.append(name, value, track);
    list.appendChild(li);
  }

  // Two frames so the 0-width state paints first and the bars animate in.
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      fills.forEach(([fill, pct]) => {
        fill.style.width = pct + "%";
      });
    });
  });
}

export function renderFavExercisesChart(labels, values, fullNames, ranks) {
  const max = Math.max(...values, 1);
  renderStatList(
    "fav-exercises-list",
    values.map((v, i) => ({
      rank: "#" + (ranks?.[i] || i + 1),
      label: fullNames?.[i] || labels[i] || "",
      valueText: `${v} sets`,
      percent: (v / max) * 100,
    }))
  );
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

function formatDeltaPct(current, baseline) {
  const cur = Number(current) || 0;
  const base = Number(baseline) || 0;
  if (base === 0) return cur === 0 ? "—" : "+100%";
  const pct = ((cur - base) / base) * 100;
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(0)}%`;
}

function deltaClass(current, baseline) {
  const cur = Number(current) || 0;
  const base = Number(baseline) || 0;
  if (cur === base) return "volume-delta-neutral";
  return cur > base ? "volume-delta-up" : "volume-delta-down";
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

    const vsWeekTd = document.createElement("td");
    vsWeekTd.className = "volume-col-delta " + deltaClass(row.total_volume_kg, row.prev_week_volume_kg);
    vsWeekTd.textContent = formatDeltaPct(row.total_volume_kg, row.prev_week_volume_kg);

    const vsMonthTd = document.createElement("td");
    vsMonthTd.className = "volume-col-delta " + deltaClass(row.total_volume_kg, row.prev_month_volume_kg);
    vsMonthTd.textContent = formatDeltaPct(row.total_volume_kg, row.prev_month_volume_kg);

    const vsYearTd = document.createElement("td");
    vsYearTd.className = "volume-col-delta " + deltaClass(row.total_volume_kg, row.prev_year_volume_kg);
    vsYearTd.textContent = formatDeltaPct(row.total_volume_kg, row.prev_year_volume_kg);

    tr.append(rankTd, nameTd, sparkTd, volTd, vsWeekTd, vsMonthTd, vsYearTd);
    tbody.appendChild(tr);
  }
}

export function renderVolumeDailyTimeSeries(dailyRows, exerciseName, type, unit = "KG") {
  const canvas = document.getElementById("volume-daily-canvas");
  if (!canvas) return;
  destroyChart(getCanvasId(canvas));

  const labels = dailyRows.map((r) => String(r.date));
  const actualsValues = dailyRows.map((r) => Number(r.actuals_volume_kg) || 0);
  const planValues = dailyRows.map((r) => Number(r.plan_volume_kg) || 0);

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
  const actualColor = getCssVar("--accent", "#22d3ee");
  const planColor = getCssVar("--accent-secondary", "#a78bfa");
  const textMuted = getCssVar("--text-muted", "#71717a");

  const ctx = canvas.getContext("2d");
  const actualGradient = ctx.createLinearGradient(0, 0, 0, 280);
  if (t === "line") {
    actualGradient.addColorStop(0, "rgba(34, 211, 238, 0.28)");
    actualGradient.addColorStop(1, "rgba(34, 211, 238, 0)");
  } else {
    actualGradient.addColorStop(0, "rgba(34, 211, 238, 0.85)");
    actualGradient.addColorStop(1, "rgba(34, 211, 238, 0.55)");
  }

  const planGradient = ctx.createLinearGradient(0, 0, 0, 280);
  if (t === "line") {
    planGradient.addColorStop(0, "rgba(139, 92, 246, 0.35)");
    planGradient.addColorStop(1, "rgba(139, 92, 246, 0)");
  } else {
    planGradient.addColorStop(0, "rgba(167, 139, 250, 0.95)");
    planGradient.addColorStop(1, "rgba(124, 58, 237, 0.65)");
  }

  const fmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });
  const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

  const lineDataset = (label, values, color, gradient) => ({
    label,
    data: values.map((v) => toDisplayUnit(v, unit)),
    borderColor: color,
    backgroundColor: gradient,
    fill: t === "line",
    tension: 0.35,
    borderWidth: t === "line" ? 2.5 : 0,
    borderRadius: t === "bar" ? 8 : 0,
    borderSkipped: false,
    maxBarThickness: t === "bar" ? 24 : undefined,
    pointRadius: 0,
    pointHoverRadius: 5,
    pointHoverBackgroundColor: color,
    pointHoverBorderColor: "#fff",
    pointHoverBorderWidth: 2,
    hitRadius: 12,
  });

  chartInstances.set(getCanvasId(canvas), new Chart(ctx, {
    type: t,
    data: {
      labels,
      datasets: [
        lineDataset("Actuals", actualsValues, actualColor, actualGradient),
        lineDataset("Plan", planValues, planColor, planGradient),
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          display: true,
          labels: { color: getCssVar("--text-secondary", "#a1a1aa"), boxWidth: 12 },
        },
        tooltip: {
          backgroundColor: getCssVar("--bg-elevated", "#16161a"),
          borderColor: getCssVar("--border-subtle", "#2a2a2e"),
          borderWidth: 1,
          titleColor: getCssVar("--text-primary", "#f4f4f5"),
          bodyColor: getCssVar("--text-secondary", "#a1a1aa"),
          padding: 12,
          cornerRadius: 10,
          displayColors: true,
          callbacks: {
            label: (c) => `${c.dataset.label}: ${fmt.format(c.raw)} ${unitSuffix(unit)}`,
          },
        },
        datalabels: { display: false },
      },
      scales: {
        x: {
          ticks: {
            color: textMuted,
            font: { size: 10 },
            maxTicksLimit: 6,
            maxRotation: 0,
            autoSkip: true,
          },
          grid: { display: false },
          border: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: textMuted,
            font: { size: 10 },
            maxTicksLimit: 5,
            callback: (v) => compact.format(v),
          },
          grid: { color: "rgba(139, 92, 246, 0.08)" },
          border: { display: false, dash: [4, 4] },
        },
      },
    },
    plugins,
  }));
}

function getChartPalette() {
  return [
    "rgba(139, 92, 246, 0.75)",
    "rgba(217, 70, 239, 0.75)",
    "rgba(99, 102, 241, 0.75)",
    "rgba(192, 132, 252, 0.75)",
    "rgba(236, 72, 153, 0.75)",
    "rgba(124, 58, 237, 0.75)",
    "rgba(167, 139, 250, 0.75)",
    "rgba(244, 114, 182, 0.75)",
  ];
}

export function renderWorkoutSplitsChart(labels, values) {
  const canvas = document.getElementById("workout-splits-canvas");
  if (!canvas) return;
  destroyChart(getCanvasId(canvas));
  const palette = getChartPalette();
  const total = values.reduce((sum, v) => sum + v, 0) || 1;
  chartInstances.set(getCanvasId(canvas), new Chart(canvas.getContext("2d"), {
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
            label: (ctx) => `${ctx.label}: ${ctx.raw} sets · ${((ctx.raw / total) * 100).toFixed(0)}%`,
          },
        },
        datalabels: { display: false },
      },
    },
  }));
}

export function renderGymWeekdaysChart(labels, values) {
  const rows = labels.map((label, i) => ({ label, value: values[i] }));
  rows.sort((a, b) => b.value - a.value);
  const max = Math.max(...values, 1);
  renderStatList(
    "gym-weekdays-list",
    rows.map((r, i) => ({
      rank: "#" + (i + 1),
      label: r.label,
      valueText: `${r.value} ${r.value === 1 ? "day" : "days"}`,
      percent: (r.value / max) * 100,
    }))
  );
}
