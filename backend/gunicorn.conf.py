"""Gunicorn config for Gym Assistant.

Keep workers=1 while LocMemCache backs analytics invalidation.
Threads share that process memory, so concurrency comes from gthread.
"""

bind = "0.0.0.0:8000"
workers = 1
threads = 4
worker_class = "gthread"
