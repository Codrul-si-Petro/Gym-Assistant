from collections.abc import Callable
from typing import Any

from django.core.cache import cache

ANALYTICS_CACHE_TTL = 60 * 10


# actually since these change only upon dbt model update, maybe I clear the cache whenever dbt finishes running.
# LocMemCache is process-local — requires a single gunicorn worker (see settings.CACHES).
def _analytics_version(
    user_id: int,
) -> int:
    return cache.get(f"analytics:v:{user_id}", 0)


def invalidate_user_analytics(user_id: int) -> None:
    version = _analytics_version(user_id)
    cache.set(f"analytics:v:{user_id}", version + 1, None)


def analytics_cache_key(user_id: int, endpoint: str, **params: Any) -> str:
    version = _analytics_version(user_id)
    parts = [f"analytics:{user_id}:v{version}:{endpoint}"]
    for key, value in sorted(params.items()):
        parts.append(f"{key}={value}")
    return ":".join(parts)


def get_cached_analytics(user_id: int, endpoint: str, params: dict, fetch_fn: Callable[[], Any]) -> Any:
    key = analytics_cache_key(user_id, endpoint, **params)
    cached = cache.get(key)
    if cached is not None:
        return cached
    result = fetch_fn()
    cache.set(key, result, ANALYTICS_CACHE_TTL)
    return result
