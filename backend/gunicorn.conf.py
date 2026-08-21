"""Gunicorn config for Gym Assistant.

Keep workers=1 while LocMemCache backs analytics invalidation
(see backend.settings.CACHES and backend.core.analytics.cache_utils).
Threads share that process memory, so concurrency comes from gthread,
not from extra worker processes.

Prod start (Render): gunicorn -c backend/gunicorn.conf.py backend.wsgi:application
"""

bind = "0.0.0.0:8000"
workers = 1
threads = 4
worker_class = "gthread"
