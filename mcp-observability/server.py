"""
Spoken Social — Observability MCP server.

Phase 1: the smallest useful MCP server, built to *learn the protocol end to end*.

An MCP server exposes "tools" (callable actions), "resources" (readable data),
and "prompts" (templates). We start with just two tools so nothing is hidden.

FastMCP (from the official `mcp` Python SDK) turns a plain Python function into an
MCP tool: it reads your type hints to generate the tool's input JSON Schema, reads
your docstring for the tool's description, and handles all the JSON-RPC + transport
plumbing. What you write below is *all* the server logic there is.
"""
from mcp.server.fastmcp import FastMCP
import os
from db import fetch
from prom import prom_get
from loki import loki_get
import time

# This name is what the client sees during the `initialize` handshake, and how the
# server shows up in Claude Desktop's tool list. Keep it stable + descriptive.

MCP_TRANSPORT=os.getenv("MCP_TRANSPORT","stdio")
MCP_HOST=os.getenv("MCP_HOST","127.0.0.1")
MCP_PORT=os.getenv("MCP_PORT",8080)
MCP_PORT=int(MCP_PORT)

mcp = FastMCP("spoken-social-observability",host=MCP_HOST,port=MCP_PORT)

@mcp.tool()
def ping() -> str:
    """Health check — returns 'pong' so you can confirm the MCP server is reachable."""
    return "pong"


@mcp.tool()
def echo(message: str) -> str:
    """
    Echo back a message. Exists purely to demonstrate how an input parameter works:
    the `message: str` type hint becomes a required string field in this tool's
    auto-generated input JSON Schema — that schema is what the client reads from
    `tools/list` to know how to call this tool.
    """
    return f"You said: {message}"

@mcp.tool()
def add(a:int,b:int)->int:
    """
    Takes two integers a and b and returns their sum
    """
    return a+b



# ── Database tools ───────────────────────────────────────────────────────────
# Everything below queries Postgres as the read-only `mcp_readonly` role (see db.py).


@mcp.tool()
async def list_tables() -> list[str]:
    """List every table in the spoken_social database."""
    rows = await fetch(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
    )
    return [r["table_name"] for r in rows]

@mcp.tool()
async def describe_table(table_name:str)->list[dict]:
    """List all the columns in the table given by the user"""
    rows=await fetch(
        """
        SELECT column_name,data_type,is_nullable,ordinal_position
        FROM information_schema.columns
        WHERE table_name=$1 AND table_schema='public'
        ORDER BY ordinal_position
        """,table_name
    )
    if not rows:
        raise ValueError(f"No table named {table_name}, kindly use list_tables() to see available tables")
    return rows

@mcp.tool()
async def run_query(sql:str,limit:int=100)->list[dict]:
    """This tool allows user to run read-only SQL queries on the database,limits no.of rows to maximum 1000 to reduce context bloat."""
    sql=sql.strip()
    if sql.endswith(";"):
        sql=sql[:-1].strip()
    sql_upper=sql.upper()
    if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
        raise ValueError("Only SELECT and WITH queries are allowed")
    if ";" in sql:
        raise ValueError("Multiple statements not allowed, only a single read-only query")
    limit=max(1,min(limit,1000))
    rows=await fetch(f"""
        SELECT * FROM (
        {sql}
        ) AS _capped
        LIMIT $1
        """
        ,limit)
    return rows




# ── Metrics tools (Prometheus) ───────────────────────────────────────────────


@mcp.tool()
async def prom_query(promql: str) -> list[dict]:
    """
    Run an instant PromQL query — the value of a metric right now.

    Examples:
      up                                        which scrape targets are healthy (1/0)
      sum(rate(http_requests_total[5m]))        requests per second, last 5 minutes
      http_request_duration_seconds_count       total completed requests per handler
    """
    data = await prom_get("/api/v1/query", {"query": promql})

    # An instant query returns a "vector": one entry per matching time series, each
    # with its labels and a single [timestamp, value] pair.
    results = []
    for series in data.get("result", []):
        _timestamp, value = series["value"]
        results.append({"labels": series["metric"], "value": value})

    if not results:
        raise ValueError(
            f"No data for query {promql!r}. The metric may not exist yet, or nothing "
            f"has scraped it — check available names with list_metrics()."
        )
    return results


@mcp.tool()
async def list_metrics(contains:str="")->list[str]:
    """
    List all the metrics in Prometheus, optionally filtered by substring.If user defined string is empty returns all the strings
    Use this to discover all the metrics before calling prom_query.
    """
    names= await prom_get("/api/v1/label/__name__/values")
    if contains:
        needle=contains.lower()
        names=[n for n in names if needle in n.lower()]
        if not names:
            raise ValueError(
                f"No metric names matching {contains!r}. Try a broader filter,"
                f"or call list_metrics() with no argument to see everything."
            )
    if not names:
        raise ValueError("Prometheus returned no metrics")
    
    return sorted(names)


@mcp.tool()
async def prom_query_range(promql:str,minutes:int=60,step:str="1m")->list[dict]:
    """Query prometheus to find metric data over a given time period"""
    end=time.time()
    minutes=max(1,min(minutes,1440))
    start=end-minutes*60
    data=await prom_get("/api/v1/query_range",{"start":start,"end":end,"step":step,"query":promql})
    results=[]
    for series in data["result"]:
        results.append({"metric":series["metric"],"values":series["values"]})
    if not results:
        raise ValueError(
            f"No data for query {promql!r} over the last {minutes} minutes. "
            f"Check the metric name with list_metrics()."
        )
    return results




# ── Log tools (Loki) ─────────────────────────────────────────────────────────


@mcp.tool()
async def query_logs(logql: str, minutes: int = 60, limit: int = 100) -> list[dict]:
    """
    Search logs with a LogQL query over the last N minutes, newest first.

    A LogQL query MUST start with a stream selector in braces, optionally followed
    by filters:
      {job="spoken-social-backend"}                    all backend logs
      {job="spoken-social-backend"} |= "404"           lines containing "404"
      {job="spoken-social-backend"} |= "ERROR" != "healthcheck"
      {job="spoken-social-backend"} |~ "5[0-9]{2}"     regex: 5xx status codes

    Use list_log_labels() first to discover which streams exist.
    """
    minutes = max(1, min(minutes, 1440))
    limit = max(1, min(limit, 1000))

    # Loki wants NANOSECOND timestamps (Prometheus wanted float seconds).
    end_ns = int(time.time() * 1_000_000_000)
    start_ns = end_ns - minutes * 60 * 1_000_000_000

    data = await loki_get(
        "/loki/api/v1/query_range",
        {
            "query": logql,
            "start": start_ns,
            "end": end_ns,
            "limit": limit,
            "direction": "backward",  # newest first — what you want when debugging
        },
    )

    entries = []
    for stream in data.get("result", []):
        for timestamp_ns, line in stream.get("values", []):
            entries.append({
                "timestamp": int(timestamp_ns) / 1_000_000_000,  # back to seconds
                "labels": stream.get("stream", {}),
                "line": line,
            })

    if not entries:
        raise ValueError(
            f"No log lines matched {logql!r} in the last {minutes} minutes. "
            f"Check the stream labels with list_log_labels(), or widen the window."
        )

    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return entries


@mcp.tool()
async def list_log_labels(label:str="")->list[str]:
    """ 
    Returns the list of names of all labels if called without an argument 
    and returns that labels values if called with a label name.
    """
    if not label:
        data = await loki_get("/loki/api/v1/labels")
        if not data:
            raise ValueError("No labels found")
    else:
        data = await loki_get(f"/loki/api/v1/label/{label}/values")
        if not data:
            raise ValueError("No values for given label found")
    
    return sorted(data)

@mcp.tool()
async def recent_errors(minutes:int=60,limit:int=100)->list[dict]:
    """Recent errors, tracebacks and 5xx responses from the backend, newest first."""
    logql='{job="spoken-social-backend"} |~ "(?i)(error|traceback|exception| 5[0-9][0-9] )"'
    data = await query_logs(logql,minutes,limit)
    return data
    


if __name__ == "__main__":
    # Default transport is stdio: the client (the MCP Inspector, or Claude Desktop)
    # launches this file as a subprocess and exchanges JSON-RPC messages over
    # stdin/stdout. In Phase 5 we'll switch this one line to Streamable HTTP.

    if MCP_TRANSPORT=="stdio":
        mcp.run()
    else:
        mcp.run(transport="streamable-http")
        
    
