#!/usr/bin/env python3
"""Check that intentional API endpoints have a unit test asserting 200/201.

Usage (from repo root):
  uv run python scripts/check_endpoint_coverage.py

Exits non-zero when any covered route lacks a matching success-status assert
in tests/unit/.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS_UNIT = ROOT / "tests" / "unit"

INTENTIONAL_ENDPOINTS: list[tuple[str, str]] = [
    ("POST", "/api/auth/login/"),
    ("POST", "/api/auth/signup/"),
    ("POST", "/api/auth/logout/"),
    ("GET", "/api/auth/current-user/"),
    ("DELETE", "/api/auth/delete-account/"),
    ("POST", "/api/auth/change-password/"),
    ("PATCH", "/api/auth/update-username/"),
    ("PATCH", "/api/auth/preferences/"),
    ("POST", "/api/auth/password-reset/"),
    ("POST", "/api/auth/password-reset/confirm/"),
    ("POST", "/api/token/"),
    ("POST", "/api/token/refresh/"),
    ("GET", "/api/workouts/"),
    ("POST", "/api/workouts/"),
    ("GET", "/api/workouts/{id}/"),
    ("PUT", "/api/workouts/{id}/"),
    ("PATCH", "/api/workouts/{id}/"),
    ("GET", "/api/plan-series/"),
    ("POST", "/api/plan-series/"),
    ("GET", "/api/plan-series/{id}/"),
    ("PUT", "/api/plan-series/{id}/"),
    ("PATCH", "/api/plan-series/{id}/"),
    ("DELETE", "/api/plan-series/{id}/"),
    ("GET", "/api/exercises/"),
    ("GET", "/api/attachments/"),
    ("GET", "/api/muscles/"),
    ("GET", "/api/equipment/"),
    ("GET", "/api/v1/rest-days"),
    ("GET", "/api/v1/favourite-exercises"),
    ("GET", "/api/v1/total-volume"),
    ("GET", "/api/v1/total-volume-daily"),
    ("GET", "/api/v1/workout-splits"),
    ("GET", "/api/v1/gym-weekdays"),
    ("GET", "/api/v1/workout-sessions"),
    ("GET", "/api/v1/home-summary"),
]

SUCCESS_STATUS = re.compile(r"HTTP_20[01]_OK|HTTP_201_CREATED|status_code,\s*20[01]|==\s*20[01]\b")
CLIENT_METHOD = re.compile(
    r"""(?:self\.client|api_client|authenticated_client|other_client)\.(get|post|put|patch|delete)\s*\(""",
    re.IGNORECASE,
)


def _expand_urls_in_chunk(chunk: str, base_url: str) -> list[tuple[str, str]]:
    """Return (METHOD, path) pairs found in a success-asserting test chunk."""
    found: list[tuple[str, str]] = []
    methods = [m.group(1).upper() for m in CLIENT_METHOD.finditer(chunk)]
    if not methods:
        return found

    paths: list[str] = []

    # Absolute /api/... string literals
    for m in re.finditer(r'["\'](/api/[^"\']+)["\']', chunk):
        paths.append(m.group(1))

    # Bare BASE_URL as the path argument: client.post(BASE_URL, ...)
    if base_url and re.search(r"""\.(?:get|post|put|patch|delete)\(\s*BASE_URL\b""", chunk):
        paths.append(base_url if base_url.endswith("/") else base_url + "/")

    # f"{BASE_URL}/login/" or f"{BASE_URL}{created['workout_id']}/"
    # Nested quotes inside {…} break a simple [^"']* pattern, so scan with a
    # brace-aware suffix extractor after '{BASE_URL}'.
    if base_url:
        for m in re.finditer(r"""f(["'])\{BASE_URL\}""", chunk):
            quote = m.group(1)
            i = m.end()
            suffix_chars: list[str] = []
            depth = 0
            while i < len(chunk):
                ch = chunk[i]
                if ch == "{":
                    depth += 1
                    suffix_chars.append(ch)
                elif ch == "}":
                    depth = max(0, depth - 1)
                    suffix_chars.append(ch)
                elif ch == quote and depth == 0:
                    break
                else:
                    suffix_chars.append(ch)
                i += 1
            suffix = "".join(suffix_chars).split("?", 1)[0]
            suffix = re.sub(r"\{[^}]+\}", "{id}", suffix)
            if suffix.startswith("{id}") or suffix.startswith("/"):
                paths.append(base_url.rstrip("/") + "/" + suffix.lstrip("/"))
            else:
                paths.append(base_url + suffix)

    # Normalize
    normalized = []
    for p in paths:
        p = re.sub(r"/+", "/", p)
        p = re.sub(r"/\{[^}]+\}", "/{id}", p)
        if not p.startswith("/"):
            p = "/" + p
        normalized.append(p)

    # Pair each client call method with paths that appear in the same chunk
    # (order-insensitive: any method used in chunk covers any path in chunk)
    for method in set(methods):
        for path in normalized:
            found.append((method, path))
    return found


def _collect_covered() -> set[tuple[str, str]]:
    covered: set[tuple[str, str]] = set()
    for path in TESTS_UNIT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        base_match = re.search(r"""BASE_URL\s*=\s*["']([^"']+)["']""", text)
        base_url = base_match.group(1) if base_match else ""
        chunks = re.split(r"\n(?=def |\s{4}def )", text)
        for chunk in chunks:
            if not SUCCESS_STATUS.search(chunk):
                continue
            for item in _expand_urls_in_chunk(chunk, base_url):
                covered.add(item)
    return covered


def _norm(path: str) -> str:
    return path.rstrip("/")


def main() -> int:
    if not TESTS_UNIT.is_dir():
        print(f"Missing tests dir: {TESTS_UNIT}", file=sys.stderr)
        return 2

    covered = _collect_covered()
    missing: list[tuple[str, str]] = []
    for method, path in INTENTIONAL_ENDPOINTS:
        target = _norm(path)
        if any(cm == method and _norm(cp) == target for cm, cp in covered):
            continue
        missing.append((method, path))

    print(f"Checked {len(INTENTIONAL_ENDPOINTS)} intentional endpoints against {TESTS_UNIT}")
    print(f"Detected {len(covered)} (method, path) pairs near 200/201 asserts")
    if not missing:
        print("All intentional endpoints have a nearby 200/201 assert in tests/unit/.")
        return 0

    print(f"Missing coverage ({len(missing)}):")
    for method, path in missing:
        print(f"  {method:6} {path}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
