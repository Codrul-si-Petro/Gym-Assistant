# Gym Assistant

SaaS intended for gym goers to get insights from their workouts through charts and interactive views.
Forget pen and paper and slow, clunky Excels you forget to update then have to spend extra 30 minutes remembering what you have done.
Use the Gym Assistant app consistently and take a deep look into your trends to figure out your weak and strong points.

## Contributor set up

You will need the following tools depending on which part of the application you touch:
- [Python](https://www.python.org/downloads/) -- check pyproject.toml to see which version is in use
- [uv](https://docs.astral.sh/uv/) -- ultra fast Python package manager
- pre-commit install -- pre-commit hook to have tests check your code in each commit (less annoying when it fails locally than when it fails in the pull request, trust me)

## To set up your Python environment:

- uv sync  -- syncs your project based on the uv.lock file
- source .venv/bin/activate -- standard .venv activation for your Python virtual environment ( what uv did earlier )

We have two sets of environment variables for now, one which sits in .env.dev and one in .env.prod.
To easily access them based on our needs, there is the load sh script in the utils/ directory.

You can set up this command in your .zshrc/.bashrc or PowerShell dotfile ( though you will have to figure that out yourself ) like below:
```

## Environment Configuration

Load environment variables using the `load django [dev/prod]` command:

```bash
# Development
source utils/load django dev

**Tip:** Add this to your `~/.zshrc` for a shortcut:
```bash
load() {
  source ~/<pathtothelocalrepo>/Gym-Assistant/utils/load "$@"
}
```

Then just use:
```bash
load django dev
```

### Environment Files
You have to ask for them, sorry. The first main

## Running the Django server

```bash
load django dev
python manage.py runserver
```

Serve the static frontend separately from `frontend/` (plain HTML/JS/CSS — no build step). Open pages under `frontend/pages/` against the running API.

## Contribution conventions

Prefer small, readable diffs that match what is already in the repo. A few habits that keep reviews cheap:

- **Reuse before inventing.** Mirror existing page modules under `frontend/js/core/`, shared UI under `frontend/js/general-components/`, and theme tokens in `frontend/css/general-components/theme.css` (`--accent`, `--success`, `--danger`, etc.). Avoid new design systems or frameworks.
- **Frontend-first when reasonable.** Display concerns (units, colors, tooltips, layout) should stay in JS/CSS when the API already returns the raw numbers. Analytics volume is computed in kg server-side; convert for display with `user-preferences.js`.
- **Cache-bust static assets.** Bump the `?v=` query on `<script>` / `<link>` tags (and on ES module imports that already use `?v=`) whenever you edit those files — there is no bundler.
- **Copy and help text.** Page/area blurbs live in `frontend/js/general-components/info-content.js` and are shown via the ⓘ popover. Prefer extending that over one-off help UI.
- **Workout plans.** One `PlanSeries` = one workout template + a recurrence schedule. Plan **name** is required; optional **description** and optional **workout split** (from the user’s Profile split list). If split is blank, the plan name is stamped onto scheduled set rows as `workout_split`.
- **User splits.** Optional labels live in Django table `UserWorkoutSplit` (auth migrations). Prefer extending `auth/preferences/` / `current-user` over new endpoints when the consumer is Profile + Plan.
- **Database ownership.** Django migrations = `authentication` only. Alembic = `core` fact/plan tables. dbt = dimensions and analytics marts. See [db/README.md](db/README.md). Prefer extending existing SQL extracts or Python helpers over new tables when the data is already there.
- **APIs.** Keep ownership as `filter(user=request.user)` + assign `user` on create. Reuse `EndpointThrottle` on write-heavy endpoints. Prefer extending an existing response (e.g. `home-summary`) over a new endpoint when the consumer is the same page.
- **Tests.** Update unit contracts when response shapes change (`tests/unit/`). Prefer Playwright e2e only for user-visible flows (`tests/e2e/`).
- **Scope.** Prefer the smallest viable change. If a simpler alternative exists (datalist vs enum column, `title=` vs new tooltip component), take it and note the trade-off in the PR.

## Database Migrations

**Django** manages auth tables only. **Alembic** manages core schema tables (`fact_workouts`, `plan_series`, etc.). **dbt** manages dimensions and analytics marts. See [db/README.md](db/README.md) for the full split.

Auth (Django):

```bash
python manage.py makemigrations authentication
python manage.py migrate
```

Core (Alembic):

```bash
cd db/
alembic revision -m "your message here"   # edit the generated file, then:
alembic upgrade head
```

## dbt

```bash
# from project root
cd db/transformation
dbt build -s tag:seeds && dbt build -s tag:models
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/swagger/

## Services used

The app is hosted on [Render](https://render.com) for free (and most likely it will stay like that)

A cron job on [cron-job.org](https://cron-job.org) pings the server every 14 minutes to keep it alive. (because Render sleeps inactive services using its' free tier)

**Gunicorn workers:** Run with a single worker (`gunicorn backend.wsgi:application --workers 1`). Analytics responses are cached in Django's in-process `LocMemCache`; bumping workers without switching to a shared cache backend would leave stale analytics after writes.

**Error tracking:** Optional. Set `SENTRY_DSN` in Doppler (synced to GitHub/Render env) to enable [Sentry](https://sentry.io). When unset, the SDK is not initialized.


# Links to service specific documentation:

- [DRF API](https://www.youtube.com/watch?v=dQw4w9WgXcQ)
- [Alembic](db/README.md)
- [dbt](db/transformation/README.md)


# This documentation is a work in progress. If you encounter any issues or there are things that would be nice to be added here, please let the repo owners know.
