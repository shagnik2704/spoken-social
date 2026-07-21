"""
Connection check for the read-only DB role.

Confirms three things, without ever printing your password:
  1. we can connect as mcp_readonly
  2. reads work
  3. writes are refused (the failure is the success signal)

Run:  venv/bin/python test_db.py
"""
import asyncio

from db import fetch, get_pool


async def main() -> None:
    # 1. connect + read
    rows = await fetch("SELECT current_user AS who, count(*) AS users FROM users")
    print(f"connected as : {rows[0]['who']}")
    print(f"users table  : {rows[0]['users']} rows")

    # 2. confirm the write path is blocked
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute("CREATE TABLE should_fail (x int)")
            print("write test   : !! WRITE SUCCEEDED — role is NOT read-only, fix this")
        except Exception as e:
            print(f"write test   : blocked as expected ({type(e).__name__})")


if __name__ == "__main__":
    asyncio.run(main())
