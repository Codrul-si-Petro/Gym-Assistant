# Workout plans and metrics time slicing

Handoff document for LLMs and contributors. Describes the **plan vs actuals** split, analytics behaviour, and dashboard UX rules.

> **Persistence note (Cursor):** switching AI models *within this same chat* does not lose
> context — the full conversation is passed to whichever model is selected. Context is only
> lost when a **new chat** is started. This file exists so a fresh chat / different LLM can
> reconstruct the plan without needing the old conversation.

## Goals

1. **Plans** — Users define a template set and stamp it onto multiple future dates without mixing that flow into day-of logging.
2. **Actuals** — Gym-floor logging stays on a dedicated page: one date, one set at a time, no multi-day UI.
3. **Metrics** — Total volume table supports **All + From/To** and **WTD / MTD / YTD** chips with vs prior week / month / year columns. Daily charts show **actuals** and **plan** as separate series.

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

**All period/calendar math lives in dbt, computed via `ref()` chains. The API only filters
and joins precomputed, dated facts — it does no date-window arithmetic.**

```
total_daily_volume  (atomic, dated: user, exercise, date, scenario)
        │
        ├── ref() ──> volume_to_date     (dated: WTD/MTD/YTD flags as-of current_date)
        ├── ref() ──> volume_prev_week   (aggregated: complete prior Mon–Sun week)
        ├── ref() ──> volume_prev_month  (aggregated: complete prior calendar month)
        └── ref() ──> volume_prev_year   (aggregated: complete prior calendar year)
```

| Model | Grain | Role |
|-------|-------|------|
| `total_daily_volume` | user, exercise, **date_id**, scenario | Atomic daily volume. Backs `period=all` directly — no separate "all" aggregate exists. |
| `volume_to_date` | user, exercise, **date_id**, scenario, `is_wtd`, `is_mtd`, `is_ytd` | Dated rows (not pre-summed) for the current week/month/year-to-date windows. A date can satisfy more than one flag. |
| `volume_prev_week` | user, exercise, scenario | Complete prior ISO week, aggregated. **Its own model.** |
| `volume_prev_month` | user, exercise, scenario | Complete prior calendar month, aggregated. **Its own model.** |
| `volume_prev_year` | user, exercise, scenario | Complete prior calendar year, aggregated. **Its own model.** |

Why three separate `prev_*` models instead of one: each is a distinct grain/boundary
(week vs month vs year), each should be independently testable/documented, and each is
literally `ref('total_daily_volume')` filtered to its own window — that's the idiomatic
dbt shape. A single UNION-ALL "do everything" model was rejected as not dbt-like.

Rebuild after new workouts land (uses `current_date` at dbt run time):

```bash
cd db/transformation && dbt run -s tag:analytics
```

---

## API extract (thin — filters and joins only)

`GET /api/v1/total-volume?period=all|wtd|mtd|ytd`

| `period` | Current total source | Comparison source |
|----------|----------------------|--------------------|
| `all` | `total_daily_volume`, filtered by optional `start_date`/`end_date` (both nullable = full history) | `volume_prev_week` / `volume_prev_month` / `volume_prev_year` |
| `wtd` \| `mtd` \| `ytd` | `volume_to_date`, filtered by `is_wtd`/`is_mtd`/`is_ytd` | same three prev models |

SQL files:

- `get_total_volume_periods.sql` — wtd/mtd/ytd path; joins `volume_to_date` + all three `volume_prev_*` models by `exercise_id`
- `get_total_volume_custom_range.sql` — all path; sums `total_daily_volume` for the (nullable) date range
- `get_volume_prev_periods.sql` — comparison columns for the all path; joins the three `volume_prev_*` models

App code (`backend/core/analytics/crud/crud.py::get_total_volume`) only does hierarchy
rollup (`rollup_exercise_total_volume`) after the SQL returns — no date_trunc, no
timedelta period-boundary math in Python.

### Contract

```
?period=wtd
?period=mtd&parent_id=7
?period=all
?period=all&start_date=2026-04-01&end_date=2026-04-30
```

Frontend: `fetchTotalVolume({ period, parentId, startDate, endDate })` — options object, never positional args (a prior bug sent `start_date=wtd&parent_id=<date>` from mixed-up positional args — don't reintroduce that).

---

## Other APIs

### Log / plan

- `POST /api/workouts/` — actuals, single date
- `POST /api/workouts/plan-batch/` — stamp plan onto multiple dates
- `GET /api/workouts/?scenario=actuals|plan|all`

### Daily chart

`GET /api/v1/total-volume-daily?exercise_id=&start_date=&end_date=` → `{ date, actuals_volume_kg, plan_volume_kg }[]` (reads `total_daily_volume` directly, grouped by scenario).

---

## Frontend

| Page | Purpose |
|------|---------|
| `workouts_input.html` | Actuals only |
| `workouts_plan.html` | Multi-date plan stamp |
| `workouts_table.html` | Actuals / Plan filter |
| `dashboard.html` | Volume chips + From/To + daily chart |

### Dashboard UX

- **All** (default) — lifetime from the dated fact; set From/To for a custom range
- **WTD / MTD / YTD** — snap From/To for visibility; API request only ever sends `period=`
- Manual date change → chip resets to **All**
- Hard-refresh after deploys (`chart-controller.js?v=…`, `data-fetch.js`)

---

## Tests

Assert structure/contract, not hardcoded calendar dates:

- `tests/unit/test_volume_periods.py`:
  - time-filter constants are stable
  - each `volume_prev_*` dbt model exists, uses `ref('total_daily_volume')`, and aggregates
  - `volume_to_date` is dated (`date_id`) and carries the three flags
  - extract SQL touches only the fact tables/params expected, with no `date_trunc`/`INTERVAL` (i.e. no window math leaking into the API layer)
- `tests/unit/test_analytics.py` — `period` query param round-trip via the live API/DB

---

## Implementation map

| Area | Files |
|------|-------|
| Daily fact | `db/transformation/models/analytics/total_daily_volume.sql` |
| To-date fact | `db/transformation/models/analytics/volume_to_date.sql` |
| Prev-period facts | `volume_prev_week.sql`, `volume_prev_month.sql`, `volume_prev_year.sql` |
| Extract SQL | `get_total_volume_periods.sql`, `get_total_volume_custom_range.sql`, `get_volume_prev_periods.sql` |
| CRUD | `backend/core/analytics/crud/crud.py` (`get_total_volume`) |
| Constants | `backend/core/workout_constants.py` |

---

## Quick verify

```bash
cd db/transformation && dbt run -s total_daily_volume volume_to_date volume_prev_week volume_prev_month volume_prev_year
# hard-refresh Metrics
# Network: GET /api/v1/total-volume?period=wtd   (not start_date=wtd)
```
