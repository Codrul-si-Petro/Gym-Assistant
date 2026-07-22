// Keep chart instances per canvas so tabs do not clobber each other.

const chartInstances = new Map();

/** Table-wide toggle for vs-column display: percent (default) or absolute kg/lbs diff. */
let volumeDeltaDisplayMode = "percent";

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

export function toggleVolumeDeltaDisplayMode() {
  volumeDeltaDisplayMode = volumeDeltaDisplayMode === "percent" ? "absolute" : "percent";
  return volumeDeltaDisplayMode;
}

export function resetVolumeDeltaDisplayMode() {
  volumeDeltaDisplayMode = "percent";
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

// "To date" comparisons: apples-to-apples vs the prior period *as far as it has run*
// (e.g. this-month-so-far vs the same day-of-month last month).
const PERIOD_DELTA_CONFIG = {
  wtd: { key: "previous_week_to_date", label: "vs PW" },
  mtd: { key: "previous_month_to_date", label: "vs PM" },
  ytd: { key: "previous_year_to_date", label: "vs PY" },
};

// "Full" comparisons: vs the *complete* prior period, regardless of how far the
// current one has run (e.g. this-month-so-far vs all of last month).
const PERIOD_DELTA_FULL_CONFIG = {
  wtd: { key: "previous_week", label: "vs Full PW" },
  mtd: { key: "previous_month", label: "vs Full PM" },
  ytd: { key: "previous_year", label: "vs Full PY" },
};

// Plan gets the same duality as the "vs FULL" columns above: plan_volume (always
// shown, any period) is plan-to-date, an apples-to-apples "on pace" read; these are
// the *entire* current week/month/year's plan — the actual target to hit.
const PERIOD_PLAN_FULL_CONFIG = {
  wtd: { key: "plan_week_full", label: "Plan full week" },
  mtd: { key: "plan_month_full", label: "Plan full month" },
  ytd: { key: "plan_year_full", label: "Plan full year" },
};

function setDeltaHeader(id, cfg) {
  const th = document.getElementById(id);
  if (!th) return;
  if (!cfg) {
    th.hidden = true;
    return;
  }
  th.hidden = false;
  th.textContent = cfg.label;
}

/**
 * Show/hide and relabel the period-dependent comparison column headers for the
 * active period (hidden entirely for period=all, which has no enclosing week/
 * month/year to compare against).
 */
export function updateVolumeDeltaHeader(period) {
  setDeltaHeader("volume-col-delta-header", PERIOD_DELTA_CONFIG[period]);
  setDeltaHeader("volume-col-delta-full-header", PERIOD_DELTA_FULL_CONFIG[period]);
  setDeltaHeader("volume-col-plan-full-header", PERIOD_PLAN_FULL_CONFIG[period]);
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
    const isTotal = item.label === "Total" || item.isTotal;
    li.className = item.rank ? "stat-row" : "stat-row stat-row--no-rank";
    if (isTotal) li.classList.add("stat-row--total");

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
  const items = [];
  const totalSets = values.reduce((sum, v) => sum + (Number(v) || 0), 0);
  if (values.length) {
    items.push({
      rank: "",
      label: "Total",
      valueText: `${totalSets} sets`,
      percent: 100,
      isTotal: true,
    });
  }
  for (let i = 0; i < values.length; i += 1) {
    items.push({
      rank: "#" + (ranks?.[i] || i + 1),
      label: fullNames?.[i] || labels[i] || "",
      valueText: `${values[i]} sets`,
      percent: (values[i] / max) * 100,
    });
  }
  renderStatList("fav-exercises-list", items);
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

/**
 * Hierarchy breadcrumb companion lives in updateVolumeToolbar.
 * Overall totals are the first "Total" row inside the volume table.
 */

/** True when the API returned a real plan baseline (null/undefined = no plan → N/A). */
function hasPlanBaseline(baseline) {
  return baseline != null;
}

function computeDeltaPct(current, baseline) {
  // null/undefined baseline = "no plan" → caller renders N/A (do not compute %).
  if (!hasPlanBaseline(baseline)) return null;
  const cur = Number(current) || 0;
  const base = Number(baseline) || 0;
  if (base === 0 && cur === 0) return null;
  if (base === 0) return 100;
  return ((cur - base) / base) * 100;
}

function formatDeltaPct(current, baseline) {
  if (!hasPlanBaseline(baseline)) return "N/A";
  const pct = computeDeltaPct(current, baseline);
  if (pct == null) return "—";
  const sign = pct >= 0 ? "+" : "";
  return `${sign}${pct.toFixed(0)}%`;
}

function formatDeltaAbsolute(current, baseline, unit) {
  if (!hasPlanBaseline(baseline)) return "N/A";
  const cur = Number(current) || 0;
  const base = Number(baseline) || 0;
  const diffKg = cur - base;
  if (diffKg === 0) return "—";
  const sign = diffKg > 0 ? "+" : "-";
  // Unit lives in the table heading (kg/lbs) — don't repeat it in every vs cell.
  return `${sign}${formatVolume(Math.abs(diffKg), unit)}`;
}

function deltaClass(current, baseline) {
  if (!hasPlanBaseline(baseline)) return "volume-delta-na";
  const pct = computeDeltaPct(current, baseline);
  if (pct == null) return "volume-delta-neutral";
  if (pct > 10) return "volume-delta-up";
  if (pct < -10) return "volume-delta-down";
  return "volume-delta-neutral";
}

function formatDeltaCell(current, baseline, unit) {
  if (!hasPlanBaseline(baseline)) return "N/A";
  if (volumeDeltaDisplayMode === "absolute") {
    return formatDeltaAbsolute(current, baseline, unit);
  }
  return formatDeltaPct(current, baseline);
}

/** One "vs X" cell: tabular %/absolute diff, click-to-toggle, color-coded by direction. */
function makeDeltaCell(current, baseline, unit, onDeltaToggle) {
  const td = document.createElement("td");
  const noPlan = !hasPlanBaseline(baseline);
  td.className =
    "volume-col-delta " +
    (noPlan ? "" : "volume-col-delta-toggle ") +
    deltaClass(current, baseline);
  td.textContent = formatDeltaCell(current, baseline, unit);
  if (!noPlan) {
    td.title = "Tap to switch between % and absolute difference";
    td.addEventListener("click", () => {
      if (onDeltaToggle) onDeltaToggle();
    });
  } else {
    td.title = "No plan for this exercise in the selected window";
  }
  return td;
}

export function renderVolumeTable(results, unit, period, handlers) {
  const tbody = document.getElementById("volume-table-body");
  if (!tbody) return;

  const onDrill = handlers?.onDrill;
  const onMinichart = handlers?.onMinichart;
  const onDeltaToggle = handlers?.onDeltaToggle;
  const deltaCfg = PERIOD_DELTA_CONFIG[period] || null;
  const deltaFullCfg = PERIOD_DELTA_FULL_CONFIG[period] || null;
  const planFullCfg = PERIOD_PLAN_FULL_CONFIG[period] || null;

  updateVolumeDeltaHeader(period);
  tbody.replaceChildren();

  const appendVolumeRow = (row, { isTotal = false, displayRank = null, planActualVolume = null } = {}) => {
    const tr = document.createElement("tr");
    if (isTotal) tr.className = "volume-row-total";

    const rankTd = document.createElement("td");
    rankTd.className = "volume-col-rank";
    rankTd.textContent = displayRank != null ? String(displayRank) : String(row.rank ?? "");

    const nameTd = document.createElement("td");
    nameTd.className = "volume-col-exercise";
    if (isTotal) {
      nameTd.textContent = "Total";
    } else {
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
    }

    const sparkTd = document.createElement("td");
    sparkTd.className = "volume-col-chart";
    if (!isTotal) {
      const sparkBtn = document.createElement("button");
      sparkBtn.type = "button";
      sparkBtn.className = "volume-minichart-placeholder";
      sparkBtn.setAttribute(
        "aria-label",
        "Open volume chart for " + (row.exercise_name || "exercise")
      );
      sparkBtn.innerHTML =
        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<line x1="5" y1="20" x2="5" y2="14"></line>' +
        '<line x1="12" y1="20" x2="12" y2="8"></line>' +
        '<line x1="19" y1="20" x2="19" y2="4"></line>' +
        "</svg>";
      sparkBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        if (onMinichart) onMinichart(row);
      });
      sparkTd.appendChild(sparkBtn);
    }

    const volTd = document.createElement("td");
    volTd.className = "volume-col-vol";
    volTd.textContent = formatVolume(row.total_volume, unit);

    tr.append(rankTd, nameTd, sparkTd, volTd);

    // For plan deltas on the Total row, compare only actuals from rows that have a plan
    // (avoids mixing unplanned volume into the numerator while plan stays small).
    const planCurrent =
      isTotal && planActualVolume != null ? planActualVolume : row.total_volume;

    if (deltaCfg) {
      tr.appendChild(makeDeltaCell(row.total_volume, row[deltaCfg.key], unit, onDeltaToggle));
    }
    if (deltaFullCfg) {
      const cell = makeDeltaCell(row.total_volume, row[deltaFullCfg.key], unit, onDeltaToggle);
      cell.classList.add("volume-col-delta-full");
      tr.appendChild(cell);
    }
    tr.appendChild(makeDeltaCell(planCurrent, row.plan_volume, unit, onDeltaToggle));
    if (planFullCfg) {
      const cell = makeDeltaCell(planCurrent, row[planFullCfg.key], unit, onDeltaToggle);
      cell.classList.add("volume-col-delta-full");
      tr.appendChild(cell);
    }

    tbody.appendChild(tr);
  };

  if (results.length) {
    const PLAN_KEYS = ["plan_volume", "plan_week_full", "plan_month_full", "plan_year_full"];
    const PRIOR_KEYS = [
      "previous_week",
      "previous_week_to_date",
      "previous_month",
      "previous_month_to_date",
      "previous_year",
      "previous_year_to_date",
    ];
    const totals = {
      total_volume: 0,
      plan_volume: null,
      previous_week: 0,
      previous_week_to_date: 0,
      previous_month: 0,
      previous_month_to_date: 0,
      previous_year: 0,
      previous_year_to_date: 0,
      plan_week_full: null,
      plan_month_full: null,
      plan_year_full: null,
    };
    let planActualVolume = null;
    for (const row of results) {
      totals.total_volume += Number(row.total_volume) || 0;
      for (const key of PRIOR_KEYS) {
        totals[key] += Number(row[key]) || 0;
      }
      for (const key of PLAN_KEYS) {
        if (row[key] == null) continue;
        totals[key] = (totals[key] || 0) + (Number(row[key]) || 0);
        if (key === "plan_volume") {
          planActualVolume = (planActualVolume || 0) + (Number(row.total_volume) || 0);
        }
      }
    }
    appendVolumeRow(totals, {
      isTotal: true,
      displayRank: 1,
      planActualVolume,
    });
  }

  for (let i = 0; i < results.length; i += 1) {
    appendVolumeRow(results[i], { displayRank: i + 2 });
  }
}

function updateSessionsDeltaHeader(period) {
  setDeltaHeader("sessions-col-delta-header", PERIOD_DELTA_CONFIG[period]);
  setDeltaHeader("sessions-col-delta-full-header", PERIOD_DELTA_FULL_CONFIG[period]);
  setDeltaHeader("sessions-col-plan-full-header", PERIOD_PLAN_FULL_CONFIG[period]);
  // Plan to date is always visible (like volume).
  const planHeader = document.getElementById("sessions-col-plan-header");
  if (planHeader) planHeader.hidden = false;
}

const SESSIONS_PLAN_TO_DATE = {
  wtd: "plan_week",
  mtd: "plan_month",
  ytd: "plan_year",
  all: "plan_year",
};

export function renderSessionsTable(results, period = "all", comparisons = {}, onDeltaToggle = null) {
  const tbody = document.getElementById("sessions-table-body");
  const inner = document.getElementById("sessions-table-inner");
  if (!tbody) return;

  const deltaCfg = PERIOD_DELTA_CONFIG[period] || null;
  const deltaFullCfg = PERIOD_DELTA_FULL_CONFIG[period] || null;
  const planFullCfg = PERIOD_PLAN_FULL_CONFIG[period] || null;
  const planKey = SESSIONS_PLAN_TO_DATE[period] || "plan_year";

  updateSessionsDeltaHeader(period);
  tbody.replaceChildren();

  const colCount =
    4 + (deltaCfg ? 1 : 0) + (deltaFullCfg ? 1 : 0) + 1 + (planFullCfg ? 1 : 0);

  const appendEmptyDeltaCells = (tr) => {
    if (deltaCfg) {
      const td = document.createElement("td");
      td.className = "volume-col-delta";
      tr.appendChild(td);
    }
    if (deltaFullCfg) {
      const td = document.createElement("td");
      td.className = "volume-col-delta volume-col-delta-full";
      tr.appendChild(td);
    }
    const planTd = document.createElement("td");
    planTd.className = "volume-col-delta";
    tr.appendChild(planTd);
    if (planFullCfg) {
      const td = document.createElement("td");
      td.className = "volume-col-delta volume-col-delta-full";
      tr.appendChild(td);
    }
  };

  if (results.length) {
    const totalTr = document.createElement("tr");
    totalTr.className = "volume-row-total";

    const rankTd = document.createElement("td");
    rankTd.className = "volume-col-rank";
    rankTd.textContent = "1";

    const labelTd = document.createElement("td");
    labelTd.textContent = "Total";

    const countTd = document.createElement("td");
    countTd.colSpan = 2;
    countTd.textContent = `${results.length} session${results.length === 1 ? "" : "s"}`;
    totalTr.append(rankTd, labelTd, countTd);

    const currentCount = results.length;
    // Unit not used for session counts in absolute mode — show raw count diffs.
    const unit = "KG";
    if (deltaCfg) {
      totalTr.appendChild(
        makeDeltaCell(currentCount, comparisons[deltaCfg.key], unit, onDeltaToggle)
      );
    }
    if (deltaFullCfg) {
      const cell = makeDeltaCell(currentCount, comparisons[deltaFullCfg.key], unit, onDeltaToggle);
      cell.classList.add("volume-col-delta-full");
      totalTr.appendChild(cell);
    }
    totalTr.appendChild(
      makeDeltaCell(currentCount, comparisons[planKey], unit, onDeltaToggle)
    );
    if (planFullCfg) {
      const cell = makeDeltaCell(currentCount, comparisons[planFullCfg.key], unit, onDeltaToggle);
      cell.classList.add("volume-col-delta-full");
      totalTr.appendChild(cell);
    }

    tbody.appendChild(totalTr);
  }

  for (let i = 0; i < results.length; i += 1) {
    const row = results[i];
    const tr = document.createElement("tr");
    const rankTd = document.createElement("td");
    rankTd.className = "volume-col-rank";
    rankTd.textContent = String(i + 2);
    const dateTd = document.createElement("td");
    dateTd.textContent = String(row.date ?? "");
    const numTd = document.createElement("td");
    numTd.textContent = String(row.workout_number ?? "");
    const splitTd = document.createElement("td");
    splitTd.textContent = row.workout_split || "—";
    tr.append(rankTd, dateTd, numTd, splitTd);
    appendEmptyDeltaCells(tr);
    tbody.appendChild(tr);
  }

  if (inner) inner.style.display = results.length ? "" : "none";
  void colCount;
}

export function renderVolumeDailyTimeSeries(dailyRows, exerciseName, type, unit = "KG") {
  const canvas = document.getElementById("volume-daily-canvas");
  if (!canvas) return;
  destroyChart(getCanvasId(canvas));

  // Collapse dates with nothing registered at all — only real data points get a
  // slot on the axis, so bars/points for the dates in between sit right next to
  // each other instead of leaving dead space for days with no actuals or plan.
  const rows = dailyRows.filter(
    (r) => (Number(r.actuals_volume) || 0) > 0 || (Number(r.plan_volume) || 0) > 0
  );

  const labels = rows.map((r) => String(r.date));
  const actualsValues = rows.map((r) => Number(r.actuals_volume) || 0);
  const planValues = rows.map((r) => Number(r.plan_volume) || 0);

  const t = type || "line";
  const box = document.getElementById("volume-daily-chart-inner");
  const sizeEl = document.getElementById("volume-daily-chart-size");
  const scrollEl = document.getElementById("volume-daily-chart-scroll");
  // Size the canvas from the point count alone (no forced stretch to fill the
  // container) so sparse data doesn't get spread thin across the full width —
  // that's what was making bars look far apart. Bars need more room per point
  // than a line does, since two grouped bars (actuals + plan) share each slot.
  const minPxPerPoint = t === "bar" ? 34 : 14;

  if (box) {
    box.style.display = "";
    box.style.height = "280px";
  }
  if (sizeEl && scrollEl && labels.length) {
    const contentW = labels.length * minPxPerPoint;
    // Bars: size to content only, so a handful of points don't get stretched
    // across the whole container (that's what created the wide dead gaps).
    // Line: keep filling the container for a smooth, non-cramped curve.
    const width = t === "bar" ? Math.max(contentW, 120) : Math.max(scrollEl.clientWidth || 400, contentW);
    sizeEl.style.width = width + "px";
    sizeEl.style.height = "280px";
  }

  const plugins = typeof ChartDataLabels !== "undefined" ? [ChartDataLabels] : [];
  // Dedicated chart tokens (not --accent/--accent-secondary, which are both purple
  // in this theme) so Actuals and Plan are always visually distinct colors.
  // Actuals = purple, Plan = cyan.
  const actualColor = getCssVar("--chart-actuals", "#a78bfa");
  const planColor = getCssVar("--chart-plan", "#22d3ee");
  const textMuted = getCssVar("--text-muted", "#71717a");
  const legendTextColor = getCssVar("--text-primary", "#f4f4f5");
  const legendColors = [actualColor, planColor];

  const ctx = canvas.getContext("2d");
  const actualGradient = ctx.createLinearGradient(0, 0, 0, 280);
  if (t === "line") {
    actualGradient.addColorStop(0, "rgba(167, 139, 250, 0.35)");
    actualGradient.addColorStop(1, "rgba(167, 139, 250, 0)");
  } else {
    actualGradient.addColorStop(0, "rgba(167, 139, 250, 0.95)");
    actualGradient.addColorStop(1, "rgba(124, 58, 237, 0.65)");
  }

  const planGradient = ctx.createLinearGradient(0, 0, 0, 280);
  if (t === "line") {
    planGradient.addColorStop(0, "rgba(34, 211, 238, 0.28)");
    planGradient.addColorStop(1, "rgba(34, 211, 238, 0)");
  } else {
    planGradient.addColorStop(0, "rgba(34, 211, 238, 0.85)");
    planGradient.addColorStop(1, "rgba(34, 211, 238, 0.55)");
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
    borderRadius: t === "bar" ? 6 : 0,
    borderSkipped: false,
    // Bars fill their whole slot (no category/bar gap) so consecutive points touch.
    categoryPercentage: t === "bar" ? 1 : undefined,
    barPercentage: t === "bar" ? 0.9 : undefined,
    maxBarThickness: t === "bar" ? 40 : undefined,
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
          position: "bottom",
          labels: {
            // --text-primary flips white/black with theme (unlike --text-secondary,
            // which is a mid-gray too close to the dark background to read well).
            color: legendTextColor,
            usePointStyle: true,
            pointStyle: "circle",
            boxWidth: 8,
            boxHeight: 8,
            padding: 16,
            generateLabels(chart) {
              // Chart.js only fills in fontColor from labels.color inside its own
              // default generateLabels — since we override it, each item needs its
              // own fontColor or the legend text silently falls back to Chart.js's
              // built-in dark-gray default (unreadable in dark mode).
              return chart.data.datasets.map((ds, i) => ({
                text: ds.label,
                fillStyle: legendColors[i],
                fontColor: legendTextColor,
                strokeStyle: "transparent",
                lineWidth: 0,
                hidden: !chart.isDatasetVisible(i),
                datasetIndex: i,
                pointStyle: "circle",
              }));
            },
          },
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
