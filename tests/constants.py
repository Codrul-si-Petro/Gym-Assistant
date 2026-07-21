"""
This file should just be used to store constants somewhere and reuse them across files.
"""

import os

FRONTEND_URL: str | None = os.getenv("FRONTEND_URL")
BACKEND_URL: str | None = os.getenv("BACKEND_URL")
if not BACKEND_URL or not FRONTEND_URL:
    raise RuntimeError("URL variables have not been correctly loaded")


E2E_DASHBOARD_WORKOUT_SPLIT = "e2e-test-data"
# Dedicated split for the Today → Log flow E2E (plan + actuals cleaned up each run).
E2E_TODAY_FLOW_SPLIT = "e2e-today-flow"
# Future-dated plan created in test_plan_mode_stamps_future_dates.
E2E_FUTURE_PLAN_LABEL = "e2e-future-plan"
E2E_FUTURE_PLAN_DATE = "2026-12-01"
E2E_FUTURE_PLAN_EXERCISE_ID = 2  # Triceps extension (seed data)
# Fixed date for the persistent E2E user seed workouts (dashboard + history).
E2E_SEED_WORKOUT_DATE = "2026-04-09"

# user that gets deleted after each test sesh
SHORTLIVED_E2E_TESTER_NAME = "MosquitoJoe"
SHORTLIVED_E2E_TESTER_PASS = "MosquitoJoeDeadlifts300#"
if not SHORTLIVED_E2E_TESTER_NAME or not SHORTLIVED_E2E_TESTER_PASS:
    raise RuntimeError("Tester credential variables have not been correctly loaded")

_e2e_tester_name = os.getenv("UI_TESTER_USERNAME")
if not _e2e_tester_name:
    raise RuntimeError("UI_TESTER_USERNAME has not been correctly loaded")
E2E_TESTER_NAME: str = _e2e_tester_name

_e2e_tester_pass = os.getenv("UI_TESTER_PASS")
if not _e2e_tester_pass:
    raise RuntimeError("UI_TESTER_PASS has not been correctly loaded")
E2E_TESTER_PASS: str = _e2e_tester_pass
