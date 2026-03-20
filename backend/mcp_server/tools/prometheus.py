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

@mcp.tool()
def get_container_resources() -> list[dict]:
    """Get current CPU and memory usage for all Docker containers."""
    cpu_resp = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": 'rate(container_cpu_usage_seconds_total{name!=""}[5m]) * 100'},
        timeout=10,
    )
    cpu_data = cpu_resp.json().get("data", {}).get("result", [])

    mem_resp = httpx.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": 'container_memory_usage_bytes{name!=""} / 1024 / 1024'},
        timeout=10,
    )
    mem_data = mem_resp.json().get("data", {}).get("result", [])

    cpu_by_name = {
        r["metric"].get("name", "unknown"): round(float(r["value"][1]), 2)
        for r in cpu_data
    }
    mem_by_name = {
        r["metric"].get("name", "unknown"): round(float(r["value"][1]), 2)
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
