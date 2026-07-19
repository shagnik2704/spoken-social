"""
Database access for the observability MCP server.

Design note (the important part): this module deliberately does NOT import your
app's SQLAlchemy models or engine. It opens its own connection as the
`mcp_readonly` Postgres role, which has SELECT-only grants, forced read-only
transactions, and a 5s statement timeout. Safety is enforced by the *database*,
so no amount of bad Python here can write to your data.
"""
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Note the distinct name: this is NOT your app's DATABASE_URL (which is read-write).
MCP_DATABASE_URL = os.getenv("MCP_DATABASE_URL")

# A connection pool, created lazily on first use. Reusing connections is much
# cheaper than opening a new one per tool call.
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Return the shared connection pool, creating it on first call."""
    global _pool
    if _pool is None:
        if not MCP_DATABASE_URL:
            raise RuntimeError(
                "MCP_DATABASE_URL is not set. Create a .env file in mcp-observability/ "
                "(see .env.example)."
            )
        _pool = await asyncpg.create_pool(MCP_DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def fetch(query: str, *args) -> list[dict]:
    """
    Run a SELECT and return rows as a list of plain dicts.

    Always pass user-supplied values as *args (which become $1, $2, ... placeholders),
    NEVER by f-string interpolation into `query` — that's how SQL injection happens.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]
