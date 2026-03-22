from mcp_server.core import mcp
import httpx
import os

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")

@mcp.tool()
def query_prometheus(promql: str) -> dict:
    """Execute a PromQL instant query against Prometheus."""
    response = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": promql},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    return {
        "status": data.get("status"),
        "result_type": data.get("data", {}).get("resultType"),
        "results": data.get("data", {}).get("result", []),
    }

def _get_container_label(metric: dict) -> str:
    """Extract a friendly container identifier from cAdvisor metric labels.

    Prefers 'name' label (available on Linux Docker), falls back to
    the last segment of the 'id' label (e.g. '/docker/abc123' -> 'abc123[:12]').
    """
    name = metric.get("name")
    if name:
        return name
    cid = metric.get("id", "unknown")
    # Extract container ID from path like /docker/<hash>
    short = cid.rsplit("/", 1)[-1]
    return short[:12] if len(short) > 12 else short


@mcp.tool()
def get_container_resources() -> list[dict]:
    """Get current CPU and memory usage for all Docker containers."""
    # Use id=~"/docker/.+" to match only container-level cgroups,
    # works on both Linux (has 'name') and macOS Docker Desktop (no 'name').
    cpu_resp = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": 'rate(container_cpu_usage_seconds_total{id=~"/docker/.+"}[5m]) * 100'},
        timeout=10,
    )
    cpu_data = cpu_resp.json().get("data", {}).get("result", [])

    mem_resp = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": 'container_memory_usage_bytes{id=~"/docker/.+"} / 1024 / 1024'},
        timeout=10,
    )
    mem_data = mem_resp.json().get("data", {}).get("result", [])

    cpu_by_name = {
        _get_container_label(r["metric"]): round(float(r["value"][1]), 2)
        for r in cpu_data
    }
    mem_by_name = {
        _get_container_label(r["metric"]): round(float(r["value"][1]), 2)
        for r in mem_data
    }

    containers = []
    for name in sorted(set(cpu_by_name) | set(mem_by_name)):
        containers.append({
            "container": name,
            "cpu_percent": cpu_by_name.get(name, 0),
            "memory_mb": mem_by_name.get(name, 0),
        })

    return containers
