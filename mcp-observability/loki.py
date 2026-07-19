"""
Loki access for the observability MCP server.

Deliberately mirrors prom.py — same envelope-unwrapping job, different service.
(In a production refactor you'd share one HTTP helper between them; kept separate
here so each file reads standalone while you're learning.)

Endpoints we need:

  GET /loki/api/v1/query_range        — the main one: log lines over a time window
  GET /loki/api/v1/labels             — which label NAMES exist
  GET /loki/api/v1/label/<name>/values— which VALUES a given label has

⚠️ Two differences from Prometheus that will bite you:

  1. TIMESTAMPS ARE NANOSECONDS, not seconds.
     Prometheus: 1784445826.36      Loki: 1784445826360000000
     So: int(time.time() * 1e9)

  2. In a Loki result, `values` is a list of [timestamp, LOG LINE] — the second
     element is the raw log string, not a number.
"""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

# Local dev: Loki is published on the host at 3100.
# On the VPS (Phase 5) this becomes http://loki:3100 (a Docker service name).
LOKI_URL = os.getenv("LOKI_URL", "http://localhost:3100")


async def loki_get(path: str, params: dict | None = None) -> dict | list:
    """GET a Loki API path and return the unwrapped `data` field."""
    url = f"{LOKI_URL}{path}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, params=params or {})
    except httpx.RequestError as exc:
        raise ValueError(
            f"Could not reach Loki at {LOKI_URL}. Is the observability stack "
            f"running? ({exc.__class__.__name__})"
        ) from exc

    if response.status_code >= 400:
        # Loki returns plain-text errors (e.g. LogQL parse failures), not JSON.
        raise ValueError(f"Loki rejected the query: {response.text[:300]}")

    payload = response.json()
    if payload.get("status") != "success":
        raise ValueError(f"Loki error: {payload}")

    # Loki OMITS "data" entirely when a query matches nothing in the requested
    # window — it returns a bare {"status":"success"}. Indexing payload["data"]
    # would raise a bare KeyError('data'), which tells the caller nothing.
    # Default to an empty list so callers hit their own "no results" handling.
    return payload.get("data", [])
