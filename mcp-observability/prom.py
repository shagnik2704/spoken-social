"""
Prometheus access for the observability MCP server.

Prometheus has a small HTTP API. We only need three endpoints:

  GET /api/v1/query                 — instant query: the value "right now"
  GET /api/v1/query_range           — range query: a series over a time window
  GET /api/v1/label/__name__/values — every metric name Prometheus knows about

Every response is JSON with the same envelope:

  {"status": "success", "data": {...}}          <- what we want is in "data"
  {"status": "error",   "error": "..."}         <- PromQL syntax errors land here

Note what this module does NOT do: it doesn't calculate rates, percentiles, or
averages. Prometheus does all of that via PromQL. Our job is only to pass the
query along and unwrap the response — the same "query, don't compute" split we
used for Postgres.
"""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

# Local dev: Prometheus is published on the host at 9090.
# On the VPS (Phase 5) this becomes http://prometheus:9090 (a Docker service name).
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")


async def prom_get(path: str, params: dict | None = None) -> dict | list:
    """
    GET a Prometheus API path and return the unwrapped `data` field.

    Raises ValueError with Prometheus's own message when a query is invalid, so the
    caller sees "parse error: unexpected identifier" rather than a bare 400.
    """
    url = f"{PROMETHEUS_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params or {})
    except httpx.RequestError as exc:
        raise ValueError(
            f"Could not reach Prometheus at {PROMETHEUS_URL}. Is the observability "
            f"stack running? ({exc.__class__.__name__})"
        ) from exc

    payload = response.json()
    if payload.get("status") != "success":
        raise ValueError(f"Prometheus rejected the query: {payload.get('error', 'unknown error')}")

    return payload["data"]
