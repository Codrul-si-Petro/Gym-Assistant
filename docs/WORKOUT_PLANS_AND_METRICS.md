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
        ├── ref() ──> volume_to_date      (dated rows + time_filter: WTD|MTD|YTD)
        ├── ref() ──> volume_prev_week     (aggregated: complete prior Mon–Sun week)
        ├── ref() ──> volume_prev_month    (aggregated: complete prior calendar month)
        └── ref() ──> volume_prev_year     (aggregated: complete prior calendar year)
```

| Model | Grain | Role |
|-------|-------|------|
| `total_daily_volume` | user, exercise, **date_id**, scenario | Atomic daily volume. Backs `period=all` directly. |
| `volume_to_date` | user, exercise, **date_id**, scenario, **`time_filter`** | One row per date per applicable slice (`WTD`, `MTD`, `YTD`). A date in all three windows appears on three rows. |
| `volume_prev_week` | user, exercise, scenario | Complete prior ISO week, aggregated. **Its own model.** |
| `volume_prev_month` | user, exercise, scenario | Complete prior calendar month, aggregated. **Its own model.** |
| `volume_prev_year` | user, exercise, scenario | Complete prior calendar year, aggregated. **Its own model.** |

Rebuild after new workouts land (uses `current_date` at dbt run time):

```bash
cd db/transformation && dbt run -s tag:analytics
```

---

## API extract (thin — filters and joins only)

`GET /api/v1/total-volume?period=all|wtd|mtd|ytd`

| `period` | Current total source | Comparison source |
|----------|----------------------|-------------------|
| `all` | `total_daily_volume`, optional `start_date`/`end_date` (empty From = full history) | `volume_prev_*` models (joined but UI hides vs column on All) |
| `wtd` \| `mtd` \| `ytd` | `volume_to_date` WHERE `time_filter = UPPER(period)` | matching `volume_prev_*` for vs column |

SQL: `get_total_volume_periods.sql` filters `time_filter = UPPER(%(time_filter)s)` on `volume_to_date`.

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

- **All** (default) — lifetime from dated fact; clears From/To to full history on chip click; **no vs column**
- **WTD / MTD / YTD** — snaps From/To for visibility; shows **one** vs column (W / M / Y respectively)
- vs cell shows **percent by default**; **tap any vs cell** toggles table-wide to absolute kg/lbs diff
- Color: green = above baseline, red = below, purple = equal / no baseline
- Manual date change → chip resets to **All**

### Dashboard UX — daily chart

- Opens from table chart button; **hides period chips** while open (chart uses From/To only)
- Title = exercise name only (not "Volume by day: …")
- **← Back** tab on the left (replaces × close)
- Legend at **bottom**, circle markers, no border, solid colors
- **Actuals** = cyan (`--accent`), **Plan** = purple (`--accent-secondary`); same line/bar treatment as main branch

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
cd db/transformation && dbt run -s total_daily_volume volume_to_date volume_prev_week volume_prev_month volume_prev_year
uv run pytest tests/unit/test_volume_periods.py -q
```

Hard-refresh Metrics after frontend deploy. Open a daily chart → back tab, bottom legend, chips hidden. WTD → only vs W; All → no vs column, dates reset.
