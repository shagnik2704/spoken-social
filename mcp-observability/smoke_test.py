"""
Phase 1 smoke test — a tiny MCP *client* that drives our server over stdio.

This exists so you can see BOTH sides of the protocol in plain Python before touching
Claude Desktop. It performs the exact sequence a real client does:

    1. launch server.py as a subprocess (stdio transport)
    2. `initialize`  — the handshake
    3. `tools/list`  — discover what the server can do
    4. `tools/call`  — actually invoke a tool

Run it with the venv's python:  `venv/bin/python smoke_test.py`
"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    # Tell the client how to launch our server (same interpreter that's running this).
    server = StdioServerParameters(command=sys.executable, args=["server.py"])

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Handshake
            init = await session.initialize()
            print(f"connected to server: {init.serverInfo.name} v{init.serverInfo.version}")

            # 2. Discover tools (this is what Claude reads to know your tools exist)
            listed = await session.list_tools()
            print("\ntools/list ->")
            for t in listed.tools:
                params = list((t.inputSchema or {}).get("properties", {}).keys())
                print(f"  - {t.name}({', '.join(params)}): {t.description.splitlines()[0]}")

            # 3. Call a no-arg tool
            pong = await session.call_tool("ping", {})
            print(f"\ntools/call ping -> {pong.content[0].text}")

            # 4. Call a tool with an argument
            echoed = await session.call_tool("echo", {"message": "hello MCP"})
            print(f"tools/call echo -> {echoed.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())
