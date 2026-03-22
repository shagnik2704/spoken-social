from mcp_server.core import mcp
import httpx
import os
from datetime import datetime, timezone, timedelta

LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100")

@mcp.tool()
def search_logs(query: str, minutes: int = 30, limit: int = 50) -> list[dict]:
    """Search logs using a LogQL query against Loki. Useful example query: '{container=~".*backend.*"}'"""
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)

    response = httpx.get(
        f"{LOKI_URL}/loki/api/v1/query_range",
        params={
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "limit": limit,
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for stream in data.get("data", {}).get("result", []):
        labels = stream.get("stream", {})
        for ts, line in stream.get("values", []):
            results.append({
                "labels": labels,
                "timestamp": ts,
                "line": line,
            })

    return results

@mcp.tool()
def get_log_volume(minutes: int = 60) -> dict:
    """Get log volume by severity level over the last N minutes."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=minutes)
    time_params = {
        "start": start.isoformat(),
        "end": end.isoformat(),
    }

    counts = {}
    for level in ["INFO", "WARN", "ERROR"]:
        resp = httpx.get(
            f"{LOKI_URL}/loki/api/v1/query",
            params={
                **time_params,
                # Use regex match for container to catch '/spoken-social-backend-1' and 'backend'
                "query": f'count_over_time({{container=~".*backend.*"}} |= "{level}" [{minutes}m])',
            },
            timeout=10,
        )
        result = resp.json().get("data", {}).get("result", [])
        counts[level.lower()] = int(result[0]["value"][1]) if result else 0

    return {
        "window_minutes": minutes,
        "counts": counts,
        "total": sum(counts.values()),
    }
