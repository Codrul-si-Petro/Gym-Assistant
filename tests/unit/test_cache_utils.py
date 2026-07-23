"""Unit tests for analytics version-based cache invalidation."""

from django.core.cache import cache

from backend.core.analytics.cache_utils import (
    analytics_cache_key,
    get_cached_analytics,
    invalidate_user_analytics,
)


def test_get_cached_analytics_returns_cached_value_until_invalidated():
    cache.clear()
    user_id = 42
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return {"volume": calls["n"]}

    first = get_cached_analytics(user_id, "home-summary", {}, fetch)
    second = get_cached_analytics(user_id, "home-summary", {}, fetch)
    assert first == {"volume": 1}
    assert second == {"volume": 1}
    assert calls["n"] == 1

    invalidate_user_analytics(user_id)

    third = get_cached_analytics(user_id, "home-summary", {}, fetch)
    assert third == {"volume": 2}
    assert calls["n"] == 2


def test_analytics_cache_key_changes_after_invalidation():
    cache.clear()
    user_id = 7
    before = analytics_cache_key(user_id, "total-volume", period="ytd")
    invalidate_user_analytics(user_id)
    after = analytics_cache_key(user_id, "total-volume", period="ytd")
    assert before != after
    assert ":v0:" in before
    assert ":v1:" in after
