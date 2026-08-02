"""
Safety guard for destructive scripts.

seed_from_csv.py, reseed.py and clear_db.py all DELETE every row in the
database before doing their work. They take whatever DATABASE_URL happens to be
in the environment, with no check on where it points — so a stale .env, a wrong
shell, or an SSH session on the server is all it takes to wipe production.

`require_local_db()` refuses to proceed unless the target host is loopback.
Set ALLOW_REMOTE_DB_WIPE=1 to override deliberately (e.g. resetting a scratch
database on a remote host) — the override still prints what it is about to hit.
"""

import os
import sys
from urllib.parse import urlparse

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "", None}


def _describe(url: str) -> str:
    """Host/database of the target, with credentials stripped — safe to print."""
    try:
        p = urlparse(url)
        return f"{p.hostname or '<none>'}:{p.port or 5432}{p.path or ''}"
    except Exception:
        return "<unparseable DATABASE_URL>"


def require_local_db(script_name: str) -> None:
    """Abort unless DATABASE_URL points at a local database."""
    url = os.getenv("DATABASE_URL")

    if not url:
        print(f"❌  {script_name}: DATABASE_URL is not set. Refusing to run.")
        sys.exit(1)

    host = urlparse(url).hostname
    target = _describe(url)

    if os.getenv("ALLOW_REMOTE_DB_WIPE") == "1":
        print(f"⚠️   {script_name}: ALLOW_REMOTE_DB_WIPE=1 — proceeding against {target}")
        return

    if host not in LOCAL_HOSTS:
        print(f"❌  {script_name}: refusing to run — this script DELETES every row.")
        print(f"    Target is not local: {target}")
        print(f"    If you really mean it, re-run with ALLOW_REMOTE_DB_WIPE=1")
        sys.exit(1)

    print(f"✅  {script_name}: target is local ({target}) — proceeding.")
