# Building the Observability MCP Server — Build Journal

_A record of building Spoken Social's read-only observability MCP server: what was
built, why each decision was made, every bug hit along the way, and what each one
taught. Written so that future-you (or a new teammate) can pick this up cold._

**Goal:** ask an AI client for raw database records, application/infrastructure
metrics, and logs — without SSH-ing into the server or hand-writing queries.

---

## 1. Architecture

Once Prometheus and Loki are in place, the MCP server never touches the host,
reads a file, or runs `htop`. Everything is already aggregated behind HTTP APIs,
so the server becomes a **thin translator over three query backends**:

```
                    ┌─────────────────────────────┐
   "show me…"  →    │      Spoken Social MCP       │
   (AI client)      │  (FastMCP, Python container) │
                    └──────────────┬──────────────┘
             ┌─────────────────────┼─────────────────────┐
         PromQL                  LogQL                   SQL
             ▼                     ▼                       ▼
     Prometheus HTTP API     Loki HTTP API        Postgres (mcp_readonly)
   (app + cAdvisor + node)   (container logs)      SELECT-only role
```

**Design principle: the server queries, it does not compute.** p95 latency is
calculated by Prometheus via `histogram_quantile()`, not in Python. Keeping the
server thin means each backend stays the authority on its own data.

### Files

| Path | Purpose |
|---|---|
| `mcp-observability/server.py` | all 12 tools; transport selection |
| `mcp-observability/db.py` | Postgres pool + `fetch()` (read-only role) |
| `mcp-observability/prom.py` | Prometheus HTTP client + envelope unwrapping |
| `mcp-observability/loki.py` | Loki HTTP client + envelope unwrapping |
| `mcp-observability/Dockerfile` | container image |
| `mcp-observability/smoke_test.py` | stdio MCP client for local verification |
| `mcp-observability/test_db.py` | proves the DB role is read-only |
| `observability/prometheus/prometheus.yml` | scrape config |
| `observability/loki/loki-config.yml` | Loki storage/schema |
| `observability/promtail/promtail-config.yml` | log shipper |
| `docker-compose.yml` | one file, all environments |

---

## 2. The 12 tools

| Domain | Tool | Purpose |
|---|---|---|
| — | `ping`, `echo`, `add` | Phase 1 warm-ups; verify the protocol works |
| **Postgres** | `list_tables` | discover tables (`information_schema`) |
| | `describe_table(table_name)` | column names, types, nullability |
| | `run_query(sql, limit)` | arbitrary guarded read-only SQL |
| **Prometheus** | `list_metrics(contains)` | discover metric names |
| | `prom_query(promql)` | instant value ("right now") |
| | `prom_query_range(promql, minutes, step)` | a series over a window |
| **Loki** | `list_log_labels(label)` | label names, or one label's values |
| | `query_logs(logql, minutes, limit)` | arbitrary LogQL search |
| | `recent_errors(minutes, limit)` | curated: errors/tracebacks/5xx |

**Each domain follows the same shape:** a *discovery* tool (what exists?), a
*generic* tool (ask anything), and where useful a *curated* tool (encodes domain
knowledge so the caller needs no query language).

### Why both generic and curated tools

`query_logs` is powerful but requires the caller to know LogQL. Asked "any errors
in the last hour?", a model with only `query_logs` will guess something like
`|= "ERROR"` — and silently miss every `Traceback` line, then report "no errors
found." That is **worse than no answer**. `recent_errors` encodes what an error
actually looks like in *these* logs, once, correctly, in code.

Good MCP servers ship both.

### Shaping output for a language model

Every backend returns something nested; every tool flattens it:

| Tool | Raw shape | Returned |
|---|---|---|
| `run_query` | asyncpg `Record` | `[{col: val}]` |
| `prom_query` | `{"metric":{…},"value":[ts,"1"]}` | `{"labels":{…},"value":"1"}` |
| `query_logs` | grouped by stream, `values:[[ns,"line"]]` | one flat dict **per line** |

The consumer is an LLM context window, not a terminal. Grouped JSON forces the
model to mentally re-join records and invites mistakes; flat self-describing
records are cheaper in tokens and unambiguous. Loki's labels are deliberately
**duplicated onto every line** for this reason.

---

## 3. The security model

The rule that shaped everything: **the database is the security boundary, not
Python.**

### The read-only role

```sql
CREATE ROLE mcp_readonly LOGIN PASSWORD '<generated>';
GRANT CONNECT ON DATABASE spoken_social TO mcp_readonly;
GRANT USAGE  ON SCHEMA public TO mcp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mcp_readonly;

ALTER ROLE mcp_readonly SET default_transaction_read_only = on;
ALTER ROLE mcp_readonly SET statement_timeout = '5s';
```

Three independent layers, all enforced by Postgres:
1. **SELECT-only grants** — no INSERT/UPDATE/DELETE/DDL exists for this role
2. **`default_transaction_read_only`** — blocks writes smuggled inside a CTE
3. **`statement_timeout`** — no query can hammer the database

> ⚠️ Run the `GRANT`s **while connected to the application database**. They are
> per-database; run them against `postgres` and they silently apply to the wrong
> schema, surfacing later as "permission denied" with no obvious cause.

Verification — *the failure is the success signal*:
```sql
SET ROLE mcp_readonly;
SELECT count(*) FROM users;         -- returns a number
CREATE TABLE should_fail (x int);   -- MUST error
RESET ROLE;
```

### Why the Python checks exist anyway

`run_query` also rejects non-`SELECT`/`WITH` statements, blocks stacked
statements, and caps rows. **None of this is the security boundary** — the role
is. The Python layer exists for:

1. **Fast, readable failures** — "Only SELECT and WITH queries are allowed" beats
   a raw privilege error
2. **Context-window protection** — `SELECT * FROM users` is 2,300 rows going into
   an LLM's context. A normal DB client doesn't care; an MCP tool must.

> **Do not write a SQL sanitizer.** You cannot reliably parse SQL with string
> checks, and a half-clever regex gives false confidence. Keep the checks dumb on
> purpose. The accepted cost: `SELECT 'a;b'` is falsely rejected because of the
> semicolon check. That trade is correct — the alternative is a real SQL parser
> (`sqlglot`/`pglast`), never a smarter regex.

### Network exposure

- Every published port binds `127.0.0.1` — host nginx reaches services over
  loopback; the internet cannot
- Redis, node-exporter and cAdvisor publish **no host port at all**
- The MCP endpoint sits behind nginx with a bearer-token gate

---

## 4. Phase by phase

### Phase 1 — Hello MCP
Minimal FastMCP server (`ping`, `echo`, `add`) over **stdio**.

MCP is JSON-RPC 2.0. Every client does the same dance: `initialize` →
`tools/list` → `tools/call`. FastMCP turns a plain function into a tool by
reading **type hints** (→ input JSON Schema) and the **docstring** (→ the
description the model reads when deciding which tool to call).

### Phase 2 — Postgres
Read-only role, then `list_tables` / `describe_table` / `run_query`.

Deliberately **raw SQL, not the app's SQLAlchemy models**: the goal is arbitrary
ad-hoc questions, the app's engine is read-write (importing it would grant write
powers), and enforcing read-only at the database layer is far stronger than
sandboxing in Python.

### Phase 3 — Prometheus
`prometheus-fastapi-instrumentator` exposes `/metrics`; Prometheus scrapes the
app, node-exporter (host) and cAdvisor (containers).

Prometheus is **pull-based** — nothing pushes to it. Metric types: counters
(only rise), gauges (rise and fall), histograms (bucketed).

> **Never read a counter raw.** `http_requests_total` = 4,182,915 is useless.
> `rate(http_requests_total[5m])` gives per-second change. This is the single
> most common PromQL mistake.

Histograms use cumulative `le` ("less than or equal") buckets, which is how
`histogram_quantile()` derives p95/p99 without storing raw durations.

### Phase 4 — Loki
Loki + Promtail, then `query_logs` / `list_log_labels` / `recent_errors`.

> **Loki indexes labels, not log content.** Select a stream by labels, *then*
> grep inside it: `{job="x"} |= "error"`. The stream selector is mandatory.
>
> **Never put high-cardinality values (user IDs, request IDs) in labels.** Each
> unique label combination creates a separate stream. Keep labels coarse; put
> details in the line, where grep handles them free. This is the opposite
> instinct from SQL indexing, which is why it catches people out.

Loki timestamps are **nanoseconds** (Prometheus uses float seconds).

### Phase 5 — Deployment
Dual transport, containerisation, compose merge, nginx + TLS + token.

`MCP_TRANSPORT` selects `stdio` or `streamable-http`. **One codebase, one image,
the environment decides** — stdio stays the default so local tooling keeps
working unchanged.

---

## 5. Every bug, and what it taught

The most valuable section. Each of these cost real time.

### Stdout is sacred in stdio transport
`mcp dev` launched the server through `uv run --with mcp`, which built an
environment missing `typer`. The resulting `Error: typer is required…` went to
**stdout**, and the client died with `SyntaxError: Unexpected token 'E'... is not
valid JSON`.

> In stdio transport, stdout carries JSON-RPC and nothing else. Any stray
> `print()`, warning or error banner corrupts the stream. **Log to stderr.** This
> is the #1 cause of "my MCP server mysteriously won't connect."

### Placeholders are values, not code
`SELECT * FROM ( $1 ) AS _capped` → `PostgresSyntaxError: syntax error at or
near "$1"`. Postgres parses structure *first*, then fills values, so `$1` can
never become a subquery, table name, or column name.

> When you genuinely cannot parameterise, you must interpolate — and that is
> precisely *why* the read-only role has to exist. The final query does both
> correctly: `SELECT * FROM ( {sql} ) AS _capped LIMIT $1` — interpolation for
> **code**, placeholder for the **value**.

### Never mutate the SQL you execute
`sql = sql.upper()` uppercased the *query being run*, not just the validation
copy. `WHERE email='Student42@…'` became `'STUDENT42@…'`, silently matching zero
rows. Validate on a throwaway copy; execute the original.

### Naming prevents bugs
```python
for result in data[result]:            # NameError — the key is "result", the loop var isn't
    ...
return result                          # returns the loop variable, not the accumulator
```
Two bugs from one collision between `result`, `results`, and `"result"`. Renaming
the loop variable to `series` made both impossible to write.

### Verify your config actually took effect
```python
FastMCP("name", MCP_HOST, MCP_PORT)    # host/port are KEYWORD-ONLY
```
The 2nd and 3rd positional slots are `instructions` and `website_url`. Python
raised no error; host/port silently kept their defaults. Two lines of
introspection caught on the desk what would have been an hour of "nginx gets
connection refused" on the VPS.

> Symptom would only appear **in the container**. Assume nothing about config —
> print it back.

### `localhost` inside a container is the container
```
MCP_DATABASE_URL=postgresql://…@localhost:5432/…      → connection refused
MCP_DATABASE_URL=postgresql://…@host.docker.internal…  → works
```
Three cases, all needed: `localhost` = this container · `prometheus:9090` = a
sibling container via Docker DNS · `host.docker.internal` = the host machine
(needs `extra_hosts` on Linux; Docker Desktop provides it).

### Binding loopback inside a container makes you unreachable
FastMCP defaults to `host='127.0.0.1'` — correct on a dev machine, fatal in a
container, where it means "only I can reach me." Hence `MCP_HOST=0.0.0.0` in the
Dockerfile. **Safe default, permissive override.**

### Standardising configs can flatten load-bearing differences
The local compose hardcoded `DEV_BYPASS_ENABLED: "true"`; beta omitted it.
Committing the local file verbatim would have **enabled the built-in dev login
accounts on a public box**. Fixed with `${DEV_BYPASS_ENABLED:-false}`.

> When merging drifted configs, every difference is a *decision* until proven
> otherwise. Default to the safe value; let environments opt in.

### Floating image tags are scheduled outages
`FROM nginx:alpine` — a rebuild pulled nginx 1.31.3 on bleeding-edge Alpine,
which failed on beta's CentOS 7 kernel (3.10) with
`pwrite() "/run/nginx.pid" failed (Operation not permitted)`. Modern images issue
syscalls old kernels lack; Docker's seccomp returns EPERM, surfacing as nonsense
errors.

The stack proved the diagnosis itself: `postgres:16-alpine` and `redis:7-alpine`
were fine — **because their tags pin a version**. Pin everything.

### Ports get shadowed silently
A container from an unrelated project published `127.0.0.1:8001`, shadowing a
natively-run backend on the same port. `/metrics` returned 404 with no
indication why. `lsof -nP -iTCP:<port> -sTCP:LISTEN` shows who really owns a port.

### The `000` that wasn't about MCP
`curl` returned `000` for `/mcp` right after editing the `/mcp` nginx block —
implying we'd broken it. We hadn't.

The diagnostic chain that mattered — **isolate by layer**:

| Step | Command | Finding |
|---|---|---|
| Is it HTTP at all? | `%{http_code}` = `000` | no response received — below HTTP |
| Is the port open? | `nc -z host 443` | open → nginx alive |
| Why no response? | `curl -S` (show errors) | `certificate has expired` |
| How bad? | `openssl s_client … \| openssl x509 -dates` | expired **47 days** ago |
| **Is anything else broken?** | `curl -k` (skip validation) | `/` → 200, `/mcp` → **401** |

That last step reframed everything: with TLS validation bypassed, the site and
the token gate were **already working perfectly**. Only the certificate was
broken, and it was masking a healthy system.

### Why the certificate had silently died
Renewal failed because the ACME HTTP-01 challenge was answered by a *different
site*:
```
http://beta.social.edupyramids.org/.well-known/acme-challenge/…
  → 301 → https://beta.spoken-tutorial.org/.well-known/… → 404
```
`social.conf` had a **443 block only**. With no `server_name` match on port 80,
nginx fell through to that port's `default_server` — another vhost — which
redirected everything to itself.

Fix: a port-80 block serving the challenge *before* redirecting.
```nginx
server {
    listen 95.216.73.143:80;                    # explicit IP beats a generic default_server
    listen [2a01:4f9:2b:9ef::2]:80;
    server_name beta.social.edupyramids.org;

    location ^~ /.well-known/acme-challenge/ {  # ^~ wins over any regex location
        root /var/www/certbot;
    }
    location / { return 301 https://$host$request_uri; }
}
```
nginx matches `address:port` specificity **before** `server_name` — hence the
explicit IPs. The `^~` modifier is the classic reason ACME "randomly" fails.

> Certbot had been failing into a log nobody reads for months. The cert stayed
> valid until it didn't. **Automated renewal needs a liveness check**, not trust.

### nginx `if` is fussy — use `map`
`if ($http_authorization !="token")` → `invalid condition`. Two faults: no space
before the value, and comparing against the bare token when the header contains
`Bearer <token>`.

```nginx
map $http_authorization $mcp_denied {     # http context, outside server{}
    default              1;
    "Bearer <token>"     0;
}
# inside location /mcp:
if ($mcp_denied) { return 401; }
```
A bare `if ($var)` is the one unambiguously safe form, the token lives in one
place, and rotation is a one-line edit.

### Reverse-proxying MCP: four load-bearing directives
```nginx
proxy_pass http://127.0.0.1:8090;   # NO trailing slash — a slash strips /mcp → 404s
proxy_buffering off;                # Streamable HTTP may be SSE; buffering hangs it
proxy_read_timeout 3600s;           # MCP sessions are long-lived; 60s default drops them
proxy_http_version 1.1;             # + Connection "" — HTTP/1.0 breaks keepalive/streaming
```

### Claude Desktop cannot send a static bearer token
Adding the endpoint as a custom connector fails with *"Couldn't register with …
sign-in service."* Desktop receives the 401, assumes OAuth per the MCP spec,
attempts Dynamic Client Registration, and finds no authorization server.

**Desktop understands "open" or "OAuth" — nothing in between.** Workaround: the
`mcp-remote` bridge runs locally over stdio and injects the header:

```json
{
  "mcpServers": {
    "spoken-social-observability": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://beta.social.edupyramids.org/mcp",
               "--header", "Authorization:Bearer ${MCP_TOKEN}"],
      "env": { "MCP_TOKEN": "…" }
    }
  }
}
```
> `Authorization:Bearer` — **no space after the colon**; `mcp-remote` splits
> `--header` on the first space.

A separately-hosted agent can send the header natively, so the token gate remains
the right design. Desktop is the awkward client, not the architecture.

---

## 6. Runbook

### Local development
```bash
# stdio (default) — what Claude Desktop uses locally
cd mcp-observability && ./venv/bin/python server.py

# HTTP transport
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8080 ./venv/bin/python server.py

# verify the protocol end to end
./venv/bin/python smoke_test.py

# verify the DB role is genuinely read-only
./venv/bin/python test_db.py

# visual protocol inspector (bypasses `mcp dev`'s uv launcher — see bug above)
npx @modelcontextprotocol/inspector ./venv/bin/python server.py
```

### Observability stack only (no app Postgres collision)
```bash
docker compose up -d prometheus loki promtail node-exporter cadvisor mcp-server
```

### Deploy
```bash
git pull
docker compose up -d --build            # or: --build mcp-server, to be surgical
```

**Three things `git pull` cannot bring you** (one-time, per box):
1. `.env` — gitignored by design
2. the `mcp_readonly` role — lives in the database
3. nginx config — lives in `/etc/nginx/`, outside Docker

### Verify a deployment
```bash
curl -s -o /dev/null -w '%{http_code}\n' localhost:8090/mcp        # 406 = MCP alive
curl -s -o /dev/null -w '%{http_code}\n' https://<host>/mcp        # 401 = gate closed
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $TOKEN" https://<host>/mcp             # 406 = authed reaches MCP

# full handshake — the real proof
curl -i -X POST https://<host>/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
       "protocolVersion":"2025-06-18","capabilities":{},
       "clientInfo":{"name":"curl","version":"1.0"}}}'
```
Success: HTTP 200, an `mcp-session-id` header, and `serverInfo` in the body.

**Status-code cheat sheet:** `406` = reached MCP, wrong `Accept` header (healthy) ·
`401` = token gate working · `000` = below HTTP — TLS or connection, not MCP ·
`connection refused` = wrong bind address.

---

## 7. Known gaps

| # | Gap | Impact |
|---|---|---|
| 1 | **Promtail still tails a file path** | Loki is empty on the VPS — the backend now logs to Docker, so Promtail needs Docker log collection (container discovery + relabelling) |
| 2 | **`:latest` tags** on Prometheus/Loki/Promtail/node-exporter/cAdvisor | same class of failure as the nginx outage; pin to the versions currently running |
| 3 | **Postgres port 5432 open to the internet on beta** | binding to loopback closes it on deploy; needs team confirmation that nobody connects remotely (they'd switch to `ssh -L`) |
| 4 | **`beta.quality.edupyramids.org` has no port-80 block** | its certificate will expire the same way |
| 5 | **Debug `print()` of user emails** in `dependencies.py` / `routes/user.py` | fires on every authenticated request; those emails land in Loki, and `query_logs` would serve them |
| 6 | **Certbot renewal unverified** | run `certbot renew --dry-run` and check the timer, rather than waiting 60 days |

---

## 8. Decisions worth remembering

- **Query, don't compute.** Percentiles come from PromQL, not Python.
- **The database is the security boundary.** Python checks are UX and
  context-window protection, not security.
- **Shape output for the consumer** — here, a language model. Flatten, rename
  cryptic keys, normalise units, duplicate labels where it aids clarity.
- **Write tool errors for the model that reads them.** A silent `[]` invites
  hallucination; "no table named X, use list_tables()" does not.
- **Config decides, not code.** One image, one compose file; environments differ
  only in `.env`.
- **Safe defaults, explicit opt-in.** `127.0.0.1` over `0.0.0.0`;
  `DEV_BYPASS_ENABLED` off unless asked.
- **Pin every image tag.** A floating tag is an unscheduled upgrade.
- **Verify, don't assume** — that config applied, that a port is yours, that
  renewal works, that read-only is read-only.
