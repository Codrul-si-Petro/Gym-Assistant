# Workout plans and metrics time slicing

Handoff document for LLMs and contributors. Describes the **plan vs actuals** split, analytics behaviour, and dashboard UX rules.

> **Persistence note (Cursor):** switching AI models *within this same chat* does not lose
> context — the full conversation is passed to whichever model is selected. Context is only
> lost when a **new chat** is started. This file exists so a fresh chat / different LLM can
> reconstruct the plan without needing the old conversation.

## Goals

1. **Plans** — Users define a template set and stamp it onto multiple future dates without mixing that flow into day-of logging.
2. **Actuals** — Gym-floor logging stays on a dedicated page: one date, one set at a time, no multi-day UI.
3. **Metrics** — Total volume table supports **All + From/To** and **WTD / MTD / YTD** chips with a single contextual vs-column. Daily charts show **actuals** and **plan** as separate series.

---

## Data model

### `core.fact_workouts.scenario`

- Postgres enum `core.workout_scenario`: `actuals` | `plan`
- Migration: `db/alembic/versions/009_add_workout_scenario.py`
- Index: `(user_id, scenario, date_id)`
- Django ORM: `CharField` default `"actuals"` (DB column is enum)

### Constants

`backend/core/workout_constants.py`:

- Scenarios: `SCENARIO_ACTUALS`, `SCENARIO_PLAN`
- Time filters: `TIME_FILTER_CURRENT` = `all|wtd|mtd|ytd`, `TIME_FILTER_PREV` = `prev_week|prev_month|prev_year`

### Session guards (actuals only)

- `get_next_workout`, `get_next_set_number`, delete-last — filter `scenario=actuals`
- See `backend/core/workout_validations.py`

---

## Analytics fact layer (dbt)

**All period/calendar math lives in dbt under `models/analytics/volumes/`. The API only filters
and joins precomputed facts — it does no date-window arithmetic.**

```
analytics/volumes/total_daily_volume  (atomic, dated: user, exercise, date, scenario)
        │
        ├── ref() ──> volume_to_date              (dated rows + time_filter: WTD|MTD|YTD; any scenario)
        │
        ├── ref() ──> volume_prev_week             (aggregated: complete prior Mon–Sun week)
        ├── ref() ──> volume_prev_week_to_date      (aggregated: prior week, capped at same weekday)
        ├── ref() ──> volume_prev_month            (aggregated: complete prior calendar month)
        ├── ref() ──> volume_prev_month_to_date     (aggregated: prior month, capped at same day-of-month)
        ├── ref() ──> volume_prev_year             (aggregated: complete prior calendar year)
        ├── ref() ──> volume_prev_year_to_date      (aggregated: prior year, capped at same month/day)
        │
        ├── ref() ──> volume_current_week_full      (aggregated: entire current Mon–Sun week, incl. future days)
        ├── ref() ──> volume_current_month_full      (aggregated: entire current calendar month, incl. future days)
        └── ref() ──> volume_current_year_full       (aggregated: entire current calendar year, incl. future days)
```

Every "prior period" comparison has two variants, and the UI shows both side by side:
- **to date** — apples-to-apples: this-month-so-far vs the *same elapsed days* last month.
- **full** — this-month-so-far vs the *entire* prior month (or, for plan, vs the entire *current*
  week/month/year's plan target, not just the plan-to-date).

| Model | Grain | Role |
|-------|-------|------|
| `total_daily_volume` | user, exercise, **date_id**, scenario | Atomic daily volume. Backs `period=all` directly. |
| `volume_to_date` | user, exercise, **date_id**, scenario, **`time_filter`** | One row per date per applicable slice (`WTD`, `MTD`, `YTD`). A date in all three windows appears on three rows. Also backs plan-to-date (`scenario='plan'`). |
| `volume_prev_week(_to_date)` | user, exercise, scenario | Complete prior ISO week / same-weekday-capped prior week, aggregated. |
| `volume_prev_month(_to_date)` | user, exercise, scenario | Complete prior calendar month / same-day-of-month-capped prior month, aggregated. |
| `volume_prev_year(_to_date)` | user, exercise, scenario | Complete prior calendar year / same-month-day-capped prior year, aggregated. |
| `volume_current_{week,month,year}_full` | user, exercise, scenario | Entire *current* week/month/year (including future dates) — only used for `scenario='plan'`, to get the full-period plan target. |

Rebuild after new workouts land (uses `current_date` at dbt run time):

```bash
cd db/transformation && dbt run -s tag:analytics
```

---

## API extract (thin — filters and joins only)

`GET /api/v1/total-volume?period=all|wtd|mtd|ytd`

| `period` | Current total source | Comparison source |
|----------|----------------------|-------------------|
| `all` | `total_daily_volume`, optional `start_date`/`end_date` (empty From = full history) | `volume_prev_*` models (joined but UI hides all vs-prior/vs-plan-full columns on All — no enclosing week/month/year for a custom range) |
| `wtd` \| `mtd` \| `ytd` | `volume_to_date` WHERE `time_filter = UPPER(period)` | matching `volume_prev_week/month/year` (+ `_to_date` variant) and `volume_current_week/month/year_full` (plan only) |

SQL: `get_total_volume_periods.sql` filters `time_filter = UPPER(%(time_filter)s)` on `volume_to_date`.

Row shape (all periods; unused fields are `0` rather than omitted):

| Field | Meaning |
|-------|---------|
| `total_volume_kg` | Current window's actuals (WTD/MTD/YTD-to-date, or custom range for `all`) |
| `plan_volume_kg` | Plan for the *same* current window (to-date) |
| `plan_{week,month,year}_full_volume_kg` | Plan for the *entire* current week/month/year (0 for `all`) |
| `prev_{week,month,year}_volume_kg` | Complete prior week/month/year, actuals |
| `prev_{week,month,year}_to_date_volume_kg` | Prior week/month/year capped at the same relative day, actuals |

Frontend: `fetchTotalVolume({ period, parentId, startDate, endDate })` — options object only.

---

## Frontend pages

| Page | Purpose |
|------|---------|
| `workouts_input.html` | Actuals only |
| `workouts_plan.html` | Multi-date plan stamp |
| `workouts_table.html` | Actuals / Plan filter |
| `dashboard.html` | Volume table + chips + daily chart |

### Dashboard UX — volume table

- **All** (default) — lifetime from dated fact; clears From/To to full history on chip click; **only the Plan to date vs column** — no prior-period or full-plan columns (no enclosing week/month/year for a custom range)
- **WTD / MTD / YTD** — snaps From/To for visibility; shows **four** vs columns: `vs P{W,M,Y}` (prior period, to-date, apples-to-apples), `vs Full P{W,M,Y}` (complete prior period), `Plan to date`, `Plan full week/month/year` (entire current period's plan target)
- All comparison columns stay visible on mobile — the table scrolls horizontally (mobile is the primary surface)
- vs cell shows **percent by default**; **tap any vs cell** toggles table-wide to absolute kg/lbs diff
- Color: green = above baseline, red = below, purple = equal / no baseline
- Manual date change → chip resets to **All**

### Dashboard UX — daily chart

- Opens from table chart button; **hides period chips** while open (chart uses From/To only)
- Title = exercise name only (not "Volume by day: …")
- **← Back** tab on the left (replaces × close)
- Legend at **bottom**, circle markers, no border, solid colors
- **Actuals** = purple (`--chart-actuals`), **Plan** = cyan (`--chart-plan`)

---

## Implementation map

| Area | Files |
|------|-------|
| Volume facts | `db/transformation/models/analytics/volumes/*.sql` |
| Extract SQL | `backend/core/analytics/sql/get_total_volume_periods.sql`, `get_total_volume_custom_range.sql`, `get_volume_prev_periods.sql` |
| CRUD | `backend/core/analytics/crud/crud.py` |
| Dashboard JS | `frontend/js/core/charts/chart-controller.js`, `chart-renderers.js`, `data-fetch.js` |
| Dashboard CSS | `total-volume-dashboard.css`, `total-volume-chart.css` |

---

## Tests

- `tests/unit/test_volume_periods.py` — model paths under `volumes/`, `time_filter` column, extract SQL contract
- `tests/unit/test_analytics.py` — API round-trip

---

## Quick verify

```bash
cd db/transformation && dbt run -s tag:analytics
uv run pytest tests/unit/test_volume_periods.py -q
```

Hard-refresh Metrics after frontend deploy (bump `?v=` on any changed JS/CSS — internal
ES module imports need their own `?v=`, not just the `<script>` tag's). Open a daily
chart → back tab, bottom legend, chips hidden. WTD → vs PW / vs Full PW / Plan to date / Plan
full week; All → only Plan to date, dates reset.
