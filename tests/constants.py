"""
This file should just be used to store constants somewhere and reuse them across files.
"""

import os

FRONTEND_URL: str | None = os.getenv("FRONTEND_URL")
BACKEND_URL: str | None = os.getenv("BACKEND_URL")
if not BACKEND_URL or not FRONTEND_URL:
    raise RuntimeError("URL variables have not been correctly loaded")


E2E_DASHBOARD_WORKOUT_SPLIT = "e2e-test-data"
# Fixed date for the persistent E2E user seed workouts (dashboard + history).
E2E_SEED_WORKOUT_DATE = "2026-04-09"

# user that gets deleted after each test sesh
SHORTLIVED_E2E_TESTER_NAME = "MosquitoJoe"
SHORTLIVED_E2E_TESTER_PASS = "MosquitoJoeDeadlifts300#"
if not SHORTLIVED_E2E_TESTER_NAME or not SHORTLIVED_E2E_TESTER_PASS:
    raise RuntimeError("Tester credential variables have not been correctly loaded")

E2E_TESTER_NAME: str | None = os.getenv("UI_TESTER_USERNAME")
assert E2E_TESTER_NAME is not None
E2E_TESTER_PASS: str | None = os.getenv("UI_TESTER_PASS")
assert E2E_TESTER_PASS is not None
