"""
This file should just be used to store constants somewhere and reuse them across files.
"""

import os

FRONTEND_URL: str | None = os.getenv("FRONTEND_URL")
BACKEND_URL: str | None = os.getenv("BACKEND_URL")
if not BACKEND_URL or not FRONTEND_URL:
    raise RuntimeError("URL variables have not been correctly loaded")


E2E_DASHBOARD_WORKOUT_SPLIT = "e2e-test-data"
