# Testing

Tests live under `tests/unit/`, `tests/meta/`, and `tests/e2e/`.

## Unit + meta tests

```bash
source utils/load django dev   # loads .env.dev (DATABASE_URL, etc.)
uv run pytest tests/unit/ tests/meta/ -v
```

E2E helpers live in `tests/e2e/helpers.py` (`login`, `goto_core_page`, `open_home`, `clear_auth_state`). Auth UI uses the header **Get started** / **Log in** links and a **profile menu** (`.profile-trigger`, `#profile-logout-btn`) — not legacy `#signup-link` / `#logout-link`.

Most E2E tests share one login per session: `e2e_storage_state` in `tests/e2e/conftest.py` logs in once and injects JWT/localStorage into each test’s browser context. Only `@pytest.mark.no_auth` tests (signup/login) start logged out.

## E2E tests (Playwright)

E2E tests start Django on `:8000` and a static frontend server on `:5500` automatically (`tests/conftest.py`). You need the dev env loaded and Playwright’s browser installed once:

```bash
source utils/load django dev
uv run playwright install chromium
uv run pytest tests/e2e/ -v --tb=short
```

Required env vars (from `.env.dev` via `load django dev`):

- `DATABASE_URL`
- `FRONTEND_URL` (e.g. `http://127.0.0.1:5500`)
- `BACKEND_URL` (e.g. `http://127.0.0.1:8000`)
- `UI_TESTER_USERNAME` / `UI_TESTER_PASS` — long-lived user; bootstrap only inserts seed workouts when the `e2e-test-data` split is missing (existing data is not deleted or recreated)

Dashboard metrics read dbt materialized tables. After the first seed (or schema changes), refresh analytics once:

```bash
source utils/load django dev
cd db/transformation && uv run dbt run -s tag:analytics
```

### Watch tests in the browser

Run headed with a short delay so you can follow each step:

```bash
source utils/load django dev
uv run pytest tests/e2e/ -v --headed --slowmo=400
```

Single file or test:

```bash
uv run pytest tests/e2e/test_dashboard.py -v --headed --slowmo=400
uv run pytest tests/e2e/test_workout_history.py::test_workout_history_table_filters_edit_and_info -v --headed
```

Debug one test with Playwright inspector (pauses on failures / breakpoints):

```bash
PWDEBUG=1 uv run pytest tests/e2e/test_dashboard.py -v --headed
```
