from fastmcp import FastMCP

mcp = FastMCP(
    name="spoken-social-monitoring",
    instructions="""
    You are a monitoring agent for the Spoken Social platform.
    This platform serves ~2,488 students learning through Spoken Tutorials.
    Use the available tools to investigate system health, detect anomalies,
    and report issues. Peak hours are 10AM-4PM IST.
    """,
)
