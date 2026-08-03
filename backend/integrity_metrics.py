"""Publishes XP integrity results to Prometheus.

The check runs in the worker but Prometheus scrapes the backend, and
prometheus_client gauges live in the process that sets them. Redis carries the
result across: the worker writes one key, the backend reads it at scrape time.

Recomputing the check on every scrape would mean running it every 15 seconds
against the whole users and user_tutorials tables, which is why the value is
cached rather than measured on demand.
"""

import json
import logging
import os
import time

import redis.asyncio as redis
from prometheus_client.core import GaugeMetricFamily

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
RESULT_KEY = "integrity:xp"

GAUGES = {
    "tutorial_rows_off": "Tutorial rows whose xp_earned disagrees with their flags",
    "user_totals_off": "Students whose xp_total disagrees with the sum of their rows",
    "xp_drift": "Signed XP that would move if the system were reconciled now",
    "levels_off": "Students whose level disagrees with their xp_total",
    "impossible_totals": "Students holding an XP total the rules cannot produce",
    "impossible_rows": "Tutorial rows holding XP outside the achievable range",
    "null_test_flags": "Users with a NULL is_test_account, which filters drop silently",
}


async def publish(result: dict) -> None:
    """Store a check result for the backend to expose. Never raises — a metrics
    outage must not fail the integrity check that produced the numbers."""
    try:
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        await client.set(RESULT_KEY, json.dumps({**result, "checked_at": time.time()}))
        await client.aclose()
    except Exception as exc:
        logger.warning("Could not publish integrity metrics: %s", exc)


class IntegrityCollector:
    """Yields the last stored result as gauges. Registered on the backend."""

    def collect(self):
        raw = _read_sync()
        if raw is None:
            return
        for name, description in GAUGES.items():
            if name in raw:
                yield GaugeMetricFamily(f"xp_integrity_{name}", description, value=raw[name])
        yield GaugeMetricFamily(
            "xp_integrity_healthy",
            "1 when every XP invariant holds, 0 otherwise",
            value=1 if raw.get("healthy") else 0,
        )
        yield GaugeMetricFamily(
            "xp_integrity_age_seconds",
            "Seconds since the last integrity check completed",
            value=max(0.0, time.time() - raw.get("checked_at", 0)),
        )


def _read_sync():
    """Prometheus scrapes synchronously, so this uses the sync redis client."""
    try:
        import redis as sync_redis

        client = sync_redis.Redis.from_url(REDIS_URL, decode_responses=True)
        raw = client.get(RESULT_KEY)
        client.close()
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.warning("Could not read integrity metrics: %s", exc)
        return None
