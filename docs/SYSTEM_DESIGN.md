# 🏗️ Spoken Social — System Design for Scale

> **Target**: 500 colleges → 100K+ concurrent students → millions of events/day

---

## Table of Contents

1. [Current Architecture Audit](#1-current-architecture-audit)
2. [Identified Bottlenecks](#2-identified-bottlenecks)
3. [Target Scale Numbers](#3-target-scale-numbers)
4. [High-Level Scaled Architecture](#4-high-level-scaled-architecture)
5. [Database Layer](#5-database-layer)
6. [Caching Layer (Redis)](#6-caching-layer-redis)
7. [Backend (API) Layer](#7-backend-api-layer)
8. [Real-Time Layer](#8-real-time-layer)
9. [Social Feed Architecture](#9-social-feed-architecture)
10. [Gamification Engine](#10-gamification-engine)
11. [Search Architecture](#11-search-architecture)
12. [File Storage & CDN](#12-file-storage--cdn)
13. [Frontend Scaling](#13-frontend-scaling)
14. [Observability & Monitoring](#14-observability--monitoring)
15. [Infrastructure & Deployment](#15-infrastructure--deployment)
16. [Security at Scale](#16-security-at-scale)
17. [Phased Migration Roadmap](#17-phased-migration-roadmap)

---

## 1. Current Architecture Audit *(updated August 2026)*

> This section originally audited the February 2026 prototype — synchronous SQLAlchemy,
> an in-process APScheduler, an in-memory SSE manager, and Python-side dashboard
> aggregation. That system no longer exists: the July–August 2026 overhaul resolved most
> of what Section 2 identified (each row there now carries a status). Sections 3–17 are
> the forward-looking scale roadmap and are intentionally left as written.

### What Exists Today

```
┌──────────────┐      ┌────────────────────┐      ┌────────────────┐
|  React SPA   |─────▸|  FastAPI (async)   |─────▸|  PostgreSQL 16 |
|  Vite / TS   |      |  asyncpg + pooling |      |  27 tables     |
|  Zustand +   |      |  36 endpoints      |      |  30 indexes    |
|  TanStack Q  |      |  10 routers        |      |  19 migrations |
└──────────────┘      └─────────┬──────────┘      └───────▲────────┘
                                |  Redis 7                |
                      ┌─────────▼──────────┐              |
                      |  arq worker        |──────────────┘
                      |  - forum XP sweep  |
                      |    (15 min, 24 h   |
                      |    verify window)  |
                      |  - nightly XP      |
                      |    invariants      |
                      └────────────────────┘

  Observability: Prometheus + node-exporter + cAdvisor (cardinality-tuned),
  Loki + Grafana Alloy (log shipping), 12-tool read-only MCP server.
  All services run from one docker-compose.yml on a single cloud VM.
```

| Component | Current State (Aug 2026) | Notes |
|-----------|--------------------------|-------|
| **Database** | PostgreSQL 16, async engine (`asyncpg`), pool_size 10 / max_overflow 5 / pre-ping | Sync engine retained only for offline scripts |
| **ORM** | SQLAlchemy 2.0 async sessions via FastAPI dependency | One session per request; no leaks |
| **API Server** | Async FastAPI behind nginx (Compose) | 36 REST endpoints across 10 routers |
| **Scheduler** | arq worker in its own container | Forum-XP sweep every 15 min; integrity check nightly 02:00 IST |
| **Real-time** | None (SSE removed) | Gamification feedback is optimistic-UI + cache invalidation |
| **Coordinator / Admin** | All aggregation in SQL (`CASE` + grouped subqueries) | Per-college summary: 3 queries regardless of college count; platform summary: 1 aggregate query |
| **Leaderboard** | `RANK()` over covering descending indexes, straight from PostgreSQL | 0.11 ms/read measured; deliberately uncached — see `docs/leaderboard-cache-coherence.md` |
| **XP engine** | Single-writer idempotent recompute + append-only `xp_events` journal | Nightly invariants generated from the rules; exposed as Prometheus gauges |
| **Caching** | Redis cache-aside, 120–300 s TTLs on analytics endpoints | Fail-open: a Redis outage degrades to direct reads |
| **Auth** | External Spoken Tutorial credential verification; JWT HS256 (24 h) with real + effective identity for impersonation | No local password storage; impersonation audit-logged |
| **Frontend** | React 19 + TS strict; Zustand + TanStack Query; 5 lazy route chunks | Optimistic XP updates wired to query-cache invalidation |
| **Observability** | Prometheus / Loki / Alloy / exporters + MCP server | `/metrics` excluded from its own instrumentation; exporter cardinality deliberately reduced |

### Current Data Model Strengths ✅
- UUIDs as primary keys (horizontally scalable)
- 30 declared indexes, including covering indexes (`INCLUDE` columns) for course-XP sums and composite descending indexes for college leaderboards
- `is_test_account` NOT NULL by migration — a schema constraint, after NULL three-valued logic silently hid students from filters
- Append-only `xp_events` journal with source attribution — windowed leaderboards and audits derive from it
- JSONB for flexible fields (feedback reasons, login telemetry)

---

## 2. Identified Bottlenecks *(status as of August 2026)*

### 🔴 Critical (Breaks at ~1K users)

| # | Bottleneck | Status (Aug 2026) |
|---|-----------|-------------------|
| 1 | **Sync DB driver** blocking the event loop | ✅ **Resolved** — async engine over asyncpg; pool tuned (10 + 5 overflow, pre-ping) |
| 2 | **In-memory SSE** | ✅ **Resolved by removal** — SSE deleted; no real-time channel is currently needed |
| 3 | **Feed: no cursor pagination** | ⬜ Open — the feed itself is disabled in the UI; revisit before launch |
| 4 | **Coordinator: Python-side filtering** | ✅ **Resolved** — single two-level SQL aggregate for all colleges (was 2 + 3N queries) |
| 5 | **Admin: Python dict aggregation** | ✅ **Resolved** — platform summary is one aggregate SQL query (PR #25) |

### 🟡 High (Breaks at ~10K users)

| # | Bottleneck | Status (Aug 2026) |
|---|-----------|-------------------|
| 6 | **No connection pool** | ✅ **Resolved** — explicit pool configuration |
| 7 | **N+1 in `to_api_dict()`** | ✅ **Resolved** — 5 scalar subqueries in a single SELECT |
| 8 | **No caching** | ✅ **Resolved where warranted** — Redis TTL cache-aside on analytics; the leaderboard is *deliberately* uncached after measurement (0.11 ms) and a cache-coherence post-mortem |
| 9 | **Single in-process scheduler** | ✅ **Resolved** — APScheduler replaced by an arq worker in its own container |
| 10 | **Hardcoded `course_id == "linux"`** | ✅ **Resolved** — programmes → courses → batches hierarchy (May–June 2026 refactor) |

### 🟢 Medium (Breaks at ~100K users)

| # | Bottleneck | Status (Aug 2026) |
|---|-----------|-------------------|
| 11 | **No read replicas** | ⬜ Open — not needed at current load; constant-query-count design defers this |
| 12 | **No CDN** | ⬜ Open — static bundle served by nginx |
| 13 | **No rate limiting** | ⬜ Open — highest-priority remaining item |
| 14 | **No background workers** | ✅ **Resolved** — arq worker (forum XP, nightly integrity) |

---

## 3. Target Scale Numbers

| Metric | Current | Phase 1 (6mo) | Phase 2 (1yr) | Phase 3 (2yr) |
|--------|---------|---------------|---------------|---------------|
| **Colleges** | 5 (seed) | 50 | 200 | 500+ |
| **Students** | ~200 | 5,000 | 50,000 | 200,000+ |
| **Coordinators** | 5 | 100 | 500 | 1,500+ |
| **Concurrent Users** | 10 | 500 | 5,000 | 20,000+ |
| **Posts/day** | 20 | 2,000 | 20,000 | 100,000+ |
| **API req/sec** | 5 | 200 | 2,000 | 10,000+ |
| **XP events/day** | 100 | 10,000 | 100,000 | 1,000,000+ |
| **DB size** | 50MB | 2GB | 20GB | 100GB+ |

---

## 4. High-Level Scaled Architecture

```
                            ┌─────────────────────────┐
                            │         CDN             │
                            │   (CloudFront / BunnyCDN) │
                            │   Static + Media Assets  │
                            └────────────┬────────────┘
                                         │
                            ┌────────────▼────────────┐
                            │       Nginx / ALB        │
                            │   SSL + Rate Limiting    │
                            │   + Load Balancing       │
                            └───┬──────────────────┬───┘
                                │                  │
                   ┌────────────▼──┐    ┌──────────▼──────────┐
                   │  React SPA    │    │   API Gateway        │
                   │  (S3 / CDN)   │    │   /api/* → FastAPI   │
                   │               │    │   /ws/*  → WS Server │
                   └───────────────┘    └──┬─────┬─────┬──────┘
                                           │     │     │
                    ┌──────────────────────▼┐   │    ┌▼──────────────────┐
                    │   FastAPI Workers      │   │    │  Celery Workers   │
                    │   (Gunicorn + Uvicorn) │   │    │  (Background Jobs)│
                    │   × 4-8 workers       │   │    │                   │
                    │                       │   │    │  • XP batching    │
                    │  • REST API           │   │    │  • Reports (PDF)  │
                    │  • Auth middleware     │   │    │  • Notifications  │
                    │  • Pydantic schemas   │   │    │  • Data sync      │
                    └──┬───────────┬────────┘   │    │  • Email dispatch │
                       │           │            │    └──────┬────────────┘
                       │           │            │           │
            ┌──────────▼──┐  ┌─────▼─────┐  ┌──▼───────────▼──┐
            │ PostgreSQL  │  │  Redis     │  │  RabbitMQ /     │
            │ Primary     │  │  Cluster   │  │  Redis Streams  │
            │             │  │            │  │  (Task Queue)   │
            │  + Read     │  │  • Cache   │  └─────────────────┘
            │    Replica  │  │  • Sessions│
            │             │  │  • SSE Pub │
            │  + PgBouncer│  │    /Sub    │
            │    (pooler) │  │  • Leaderb.│
            └─────────────┘  │  • Rate lim│
                             └────────────┘


            ┌───────────────────────────────────────────┐
            │             Object Storage                │
            │   MinIO (self-hosted) / AWS S3             │
            │   Avatars, Attachments, Certificates      │
            └───────────────────────────────────────────┘
```

---

## 5. Database Layer

### 5.1 Async SQLAlchemy (Immediate Priority)

**Current Problem**: Sync `create_engine()` blocks the ASGI event loop.

**Solution**: Migrate to async SQLAlchemy 2.0:

```python
# database.py — SCALED VERSION
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,           # base connections
    max_overflow=10,        # burst capacity
    pool_timeout=30,        # wait for conn
    pool_recycle=1800,      # recycle after 30min
    pool_pre_ping=True,     # verify conn is alive
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### 5.2 Connection Pooling with PgBouncer

```
FastAPI Workers (8) ──▸ PgBouncer (port 6432) ──▸ PostgreSQL (port 5432)
                        pool_mode=transaction
                        max_client_conn=200
                        default_pool_size=25
```

### 5.3 Read Replicas

```
                 ┌──────────────┐
    Writes ─────▸│  Primary DB  │
                 │  (RW)        │──── Streaming Replication
                 └──────────────┘           │
                                   ┌───────▼────────┐
    Reads ────────────────────────▸│  Read Replica  │
    (Leaderboard, Feed,            │  (RO)          │
     Coordinator Dashboard,        └────────────────┘
     Admin Analytics)
```

**Routing logic**:
```python
# Use read replica for heavy read queries
async def get_read_db():
    """Read-only session routed to replica."""
    async with ReadReplicaSession() as session:
        yield session

@router.get('/leaderboard')
async def get_leaderboard(db: AsyncSession = Depends(get_read_db)):
    ...
```

### 5.4 Critical Index Additions

```sql
-- Feed: cursor-based pagination
CREATE INDEX idx_posts_cursor ON posts (created_at DESC, id DESC);

-- Coordinator: college-scoped student queries
CREATE INDEX idx_users_college_role ON users (college_id, role);

-- XP History: time-range queries
CREATE INDEX idx_xp_events_user_time ON xp_events (user_id, created_at DESC);

-- Feedback: aggregation queries
CREATE INDEX idx_feedback_user ON tutorial_feedback (user_id, created_at DESC);
CREATE INDEX idx_feedback_tutorial ON tutorial_feedback (tutorial_id);

-- Tutorial progress: composite for common join
CREATE INDEX idx_user_tutorials_composite ON user_tutorials (user_id, tutorial_id);

-- Full-text search on posts
CREATE INDEX idx_posts_content_trgm ON posts USING gin (content gin_trgm_ops);
```

### 5.5 Table Partitioning (Phase 3)

```sql
-- Partition xp_events by month (time-series data)
CREATE TABLE xp_events (
    id UUID DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    xp_delta INT NOT NULL,
    source_type VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

CREATE TABLE xp_events_2026_01 PARTITION OF xp_events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE xp_events_2026_02 PARTITION OF xp_events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- Auto-create partitions via pg_partman

-- Partition notifications (grows fastest, mostly cold data)
CREATE TABLE notifications (...) PARTITION BY RANGE (created_at);
```

---

## 6. Caching Layer (Redis)

### 6.1 Cache Strategy Matrix

| Data | TTL | Strategy | Invalidation |
|------|-----|----------|-------------|
| **Leaderboard (top 100)** | 5 min | Sorted Set (`ZREVRANGE`) | Rebuild on XP change (debounced) |
| **User Profile** | 2 min | Hash | Invalidate on profile update |
| **College Summary** | 10 min | JSON string | Invalidate on student progress change |
| **Tutorial Count** | 1 hr | Simple key | Invalidate when tutorials added |
| **Feed (hot posts)** | 1 min | List | Push on new post, trim old |
| **Auth Session** | 15 min | Hash | Invalidate on logout |
| **Rate Limit** | 1 min | Counter | Auto-expire via TTL |

### 6.2 Leaderboard with Redis Sorted Sets

```python
# services/leaderboard_service.py

LEADERBOARD_KEY = "leaderboard:global"
LEADERBOARD_TTL = 300  # 5 minutes

class LeaderboardService:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_top(self, limit=100) -> list[dict]:
        """O(log(N) + M) — near-instant even at 1M users."""
        cached = await self.redis.zrevrange(
            LEADERBOARD_KEY, 0, limit - 1, withscores=True
        )
        if cached:
            return [{"user_id": uid, "xp": int(score)} for uid, score in cached]

        # Cache miss: rebuild from DB
        return await self._rebuild()

    async def update_xp(self, user_id: str, new_xp: int):
        """Update a single user's score — O(log N)."""
        await self.redis.zadd(LEADERBOARD_KEY, {user_id: new_xp})

    async def get_rank(self, user_id: str) -> int:
        """Get user's rank — O(log N)."""
        rank = await self.redis.zrevrank(LEADERBOARD_KEY, user_id)
        return (rank + 1) if rank is not None else -1
```

### 6.3 Caching Coordinator Dashboard

```python
async def get_college_summary_cached(redis: Redis, db: AsyncSession, college_id: str):
    cache_key = f"college:summary:{college_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    summary = await _build_college_summary(db, college_id)
    await redis.setex(cache_key, 600, json.dumps(summary))  # 10 min TTL
    return summary
```

---

## 7. Backend (API) Layer

### 7.1 Production Server Configuration

```bash
# Run with Gunicorn + Uvicorn workers
gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --graceful-timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 100
```

### 7.2 Fix: Coordinator Pagination in SQL

```python
# BEFORE: Load all, filter in Python (current code)
all_rows = q.all()  # ← loads ALL students into RAM

# AFTER: SQL-side WINDOW functions + pagination
q = db.query(
    User.id,
    User.display_name,
    User.xp_total,
    watched_sub,
    completed_sub,
    # Compute status in SQL using CASE
    case(
        (completed_sub >= total_tutorials, literal("completed")),
        (watched_sub > total_tutorials * 0.3, literal("active")),
        (watched_sub > 0, literal("at_risk")),
        else_=literal("inactive"),
    ).label("status"),
).outerjoin(...)
.filter(User.college_id == college_id, User.role == "student")
.group_by(User.id)

# Filter by status in SQL
if status_filter != "all":
    q = q.having(status_column == status_filter)

# Sort + paginate in SQL
q = q.order_by(sort_column.desc()).offset((page - 1) * limit).limit(limit)
```

### 7.3 Fix: Feed with Cursor-Based Pagination

```python
@router.get('/feed')
async def get_feed(
    cursor: Optional[str] = None,  # ISO timestamp of last post seen
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    query = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.likes),
        selectinload(Post.comments),
    ).order_by(Post.created_at.desc(), Post.id.desc())

    if cursor:
        cursor_time = datetime.fromisoformat(cursor)
        query = query.where(Post.created_at < cursor_time)

    query = query.limit(limit + 1)  # fetch 1 extra to know if there's more
    result = await db.execute(query)
    posts = result.scalars().unique().all()

    has_more = len(posts) > limit
    posts = posts[:limit]

    return {
        "posts": [p.to_api_dict() for p in posts],
        "nextCursor": posts[-1].created_at.isoformat() if has_more else None,
        "hasMore": has_more,
    }
```

### 7.4 Fix: Eliminate N+1 in `User.to_api_dict()`

```python
# BEFORE: 4 separate COUNT queries per user call
followers_count = db.query(func.count()).filter(Follow.following_id == self.id).scalar()
following_count = db.query(func.count()).filter(Follow.follower_id == self.id).scalar()
posts_count = db.query(func.count()).filter(Post.user_id == self.id).scalar()
# ... 2 more XP queries

# AFTER: Denormalize counts into the User table
class User(Base):
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)

# Update counts atomically via triggers or on write:
async def follow_user(follower_id, target_id, db):
    db.add(Follow(follower_id=follower_id, following_id=target_id))
    await db.execute(
        update(User).where(User.id == target_id)
        .values(followers_count=User.followers_count + 1)
    )
    await db.execute(
        update(User).where(User.id == follower_id)
        .values(following_count=User.following_count + 1)
    )
```

### 7.5 Background Task Processing (Celery)

```python
# tasks/xp_tasks.py
from celery import Celery

celery_app = Celery("spoken_social", broker="redis://localhost:6379/1")

@celery_app.task
def process_xp_batch(events: list[dict]):
    """Batch-process XP events instead of one-at-a-time."""
    # Group by user, sum deltas, single UPDATE per user
    ...

@celery_app.task
def generate_coordinator_report(college_id: str, format: str):
    """Generate PDF/Excel report in background."""
    ...

@celery_app.task
def send_notification_batch(user_ids: list[str], payload: dict):
    """Fan-out notifications to many users."""
    ...

@celery_app.task
def sync_spoken_tutorial_data():
    """Periodic sync from spoken-tutorial.org API."""
    ...
```

---

## 8. Real-Time Layer

### 8.1 Replace In-Memory SSE with Redis Pub/Sub

```python
# sse.py — SCALED VERSION (horizontally scalable)
import redis.asyncio as redis

class ScalableSSEManager:
    def __init__(self):
        self.redis = redis.from_url("redis://localhost:6379/0")
        self.channel = "sse:global"

    async def broadcast(self, data: dict):
        """Publish to Redis — all API workers receive it."""
        await self.redis.publish(self.channel, json.dumps(data))

    async def subscribe(self):
        """Each SSE client subscribes via Redis Pub/Sub."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.channel)
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield f"data: {message['data'].decode()}\n\n"
```

### 8.2 WebSocket for Messaging (Phase 4)

```
Client A ──WS──▸ API Worker 1 ──PUBLISH──▸ Redis Channel "chat:conv_123"
Client B ──WS──▸ API Worker 3 ──SUBSCRIBE──▸ Redis Channel "chat:conv_123"
```

---

## 9. Social Feed Architecture

### 9.1 Fan-Out-On-Write (Recommended for our scale)

```
User creates post
       │
       ▼
┌──────────────┐    ┌─────────────────────────┐
│ Write to DB  │───▸│ Celery: fan_out_post    │
│ posts table  │    │                         │
└──────────────┘    │ For each follower:       │
                    │   LPUSH feed:{user_id}  │
                    │   post_id               │
                    │   LTRIM to 500          │
                    └─────────────────────────┘
```

**Why fan-out-on-write for Spoken Social?**
- Average user follows ~50 people (small fan-out)
- Read-heavy: users check feed 10x more than they post
- Feed reads become O(1) Redis lookups instead of complex SQL JOINs

### 9.2 Hybrid Approach for Large Accounts

Coordinators/admins with 1000+ followers → fan-out-on-read:
```python
async def get_feed(user_id: str, redis: Redis, db: AsyncSession):
    # 1. Get pre-computed feed from Redis
    post_ids = await redis.lrange(f"feed:{user_id}", 0, 19)

    # 2. Merge with posts from "celebrity" accounts (fan-out-on-read)
    celebrity_posts = await get_recent_celebrity_posts(db, user_id)

    # 3. Merge, sort by time, return
    return merge_and_sort(post_ids, celebrity_posts)
```

---

## 10. Gamification Engine

### 10.1 XP Processing Pipeline

```
Tutorial Completed
       │
       ▼
┌──────────────────┐     ┌──────────────────┐     ┌────────────────┐
│ API: Validate    │────▸│ Redis: INCRBY    │────▸│ Celery (async) │
│ + quick response │     │ user:{id}:xp     │     │                │
│ (optimistic)     │     │ ttl=60s          │     │ • Flush to DB  │
└──────────────────┘     └──────────────────┘     │ • Check badges │
                                                   │ • Check level  │
                                                   │ • SSE broadcast│
                                                   │ • Update board │
                                                   └────────────────┘
```

### 10.2 Badge Evaluation Engine

```python
# services/badge_engine.py
BADGE_RULES = {
    "first_tutorial": lambda ctx: ctx["tutorials_completed"] >= 1,
    "python_pro":     lambda ctx: ctx["course_python_completed"] == True,
    "streak_7":       lambda ctx: ctx["current_streak"] >= 7,
    "streak_30":      lambda ctx: ctx["current_streak"] >= 30,
    "social_butterfly": lambda ctx: ctx["posts_count"] >= 10,
    "helpful_answer": lambda ctx: ctx["answers_upvoted"] >= 10,
}

async def evaluate_badges(user_id: str, trigger_event: str, db, redis):
    """Run after any XP/progress change. Efficient: only checks relevant rules."""
    context = await build_user_context(user_id, db, redis)
    for badge_id, rule_fn in BADGE_RULES.items():
        if badge_id not in context["earned_badges"] and rule_fn(context):
            await award_badge(user_id, badge_id, db)
            await sse_manager.broadcast({"type": "badge_earned", ...})
```

---

## 11. Search Architecture

### Phase 1: PostgreSQL Full-Text Search
```sql
-- Use pg_trgm + GIN indexes for fast LIKE searches
ALTER TABLE users ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        to_tsvector('english', coalesce(display_name,'') || ' ' || coalesce(username,'') || ' ' || coalesce(bio,''))
    ) STORED;

CREATE INDEX idx_users_search ON users USING gin(search_vector);

-- Query
SELECT * FROM users WHERE search_vector @@ plainto_tsquery('english', 'python developer');
```

### Phase 2: Meilisearch / Typesense (>50K users)
```
Write path:  PostgreSQL ──CDC──▸ Meilisearch (near real-time sync)
Read path:   Frontend ──▸ Meilisearch API (< 50ms results)
```

---

## 12. File Storage & CDN

```
Upload Flow:
  Client ──presigned URL──▸ MinIO/S3 ──webhook──▸ API (save reference)

Serving Flow:
  Client ──▸ CDN (CloudFront) ──origin──▸ MinIO/S3
                │
                └── Image variants (thumbnails) generated by Lambda/worker
```

---

## 13. Frontend Scaling

### 13.1 Performance Optimizations

| Technique | Implementation |
|-----------|---------------|
| **Code Splitting** | Already using `React.lazy()` ✅ — extend to all heavy components |
| **Virtual Scrolling** | Use `@tanstack/react-virtual` for student tables (1000+ rows) |
| **Optimistic Updates** | TanStack Query `onMutate` for instant UI feedback |
| **Service Worker** | Workbox for offline dashboard data + push notifications |
| **Image Optimization** | WebP format, lazy loading, blur-up placeholders |
| **Bundle Analysis** | `vite-plugin-visualizer` to find heavy imports |
| **Prefetching** | Prefetch routes on hover, prefetch next page of feed |

### 13.2 PWA Configuration

```json
// manifest.json
{
  "name": "Spoken Social",
  "short_name": "Spoken",
  "start_url": "/dashboard",
  "display": "standalone",
  "background_color": "#0F172A",
  "theme_color": "#4F46E5",
  "icons": [...]
}
```

---

## 14. Observability & Monitoring

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Prometheus  │   │   Grafana    │   │    Sentry    │
│  (Metrics)   │──▸│  (Dashboards)│   │  (Errors)    │
└──────┬───────┘   └──────────────┘   └──────┬───────┘
       │                                      │
  ┌────▼─────────────────────────────────────▼────┐
  │              FastAPI Middleware                 │
  │  • Request duration histogram                  │
  │  • Endpoint hit counter                        │
  │  • Error rate by route                         │
  │  • DB query duration                           │
  │  • Active SSE connections gauge                │
  └────────────────────────────────────────────────┘

Key Alerts:
  • API p95 latency > 500ms
  • Error rate > 1%
  • DB connection pool exhaustion
  • Redis memory > 80%
  • SSE client count spike
```

---

## 15. Infrastructure & Deployment

### 15.1 Docker Compose (Production)

```yaml
services:
  api:
    build: ./backend
    command: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    deploy:
      replicas: 2
      resources:
        limits: { cpus: '2', memory: 2G }
    depends_on: [postgres, redis]

  celery-worker:
    build: ./backend
    command: celery -A tasks worker --loglevel=info --concurrency=4
    deploy:
      replicas: 2

  celery-beat:
    build: ./backend
    command: celery -A tasks beat --loglevel=info
    deploy:
      replicas: 1  # MUST be exactly 1

  postgres:
    image: postgres:16
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_SHARED_BUFFERS: 256MB
      POSTGRES_WORK_MEM: 16MB
      POSTGRES_MAX_CONNECTIONS: 200

  pgbouncer:
    image: edoburu/pgbouncer
    environment:
      DATABASE_URL: postgres://...
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 200
      DEFAULT_POOL_SIZE: 25

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: [./nginx/nginx.conf:/etc/nginx/nginx.conf]
```

---

## 16. Security at Scale

| Concern | Solution |
|---------|----------|
| **Rate Limiting** | Redis-backed sliding window: 100 req/min per user, 10 req/min for auth |
| **Input Validation** | Pydantic V2 strict mode on all endpoints |
| **SQL Injection** | SQLAlchemy parameterized queries (already safe) |
| **XSS** | Sanitize post content server-side (bleach library) |
| **CORS** | Environment-based allowed origins |
| **JWT Security** | Short-lived access tokens (15 min) + refresh tokens (7 days) |
| **Secrets** | Use `python-dotenv` + Docker secrets (never commit `.env`) |
| **XP Manipulation** | Server-side XP calculation only; rate-limit XP endpoints |

---

## 17. Phased Migration Roadmap

### 🟢 Phase 1: Foundation Fixes (Weeks 1-4)
> **Goal**: Handle 5,000 users reliably

- [ ] **Async SQLAlchemy migration** — Replace sync engine with `asyncpg`
- [ ] **Connection pooling** — Add PgBouncer
- [ ] **Redis integration** — Cache leaderboard, college summaries, auth sessions
- [ ] **Cursor-based feed pagination** — Replace `LIMIT 50` with cursor
- [ ] **Fix coordinator SQL** — Move filtering/sorting into SQL, eliminate Python-side `all()`
- [ ] **Fix `to_api_dict()` N+1** — Denormalize follower/post counts into `users` table
- [ ] **Production Uvicorn** — Gunicorn with 4 Uvicorn workers
- [ ] **Add critical indexes** — See §5.4

### 🟡 Phase 2: Horizontal Scaling (Weeks 5-10)
> **Goal**: Handle 50,000 users

- [ ] **Redis Pub/Sub SSE** — Replace in-memory SSE manager
- [ ] **Celery workers** — Offload XP batching, notifications, reports
- [ ] **Read replica** — Route heavy reads to replica
- [ ] **CDN setup** — Static assets + user-uploaded media
- [ ] **Rate limiting middleware** — Redis-backed per-user rate limits
- [ ] **Monitoring stack** — Prometheus + Grafana + Sentry
- [ ] **Docker Compose production** — Multi-container orchestration

### 🔴 Phase 3: Scale & Optimize (Weeks 11-20)
> **Goal**: Handle 200,000+ users

- [ ] **Fan-out-on-write feed** — Redis-backed personalized feed
- [ ] **Table partitioning** — Partition `xp_events` and `notifications` by month
- [ ] **Full-text search** — PostgreSQL `tsvector` → Meilisearch migration
- [ ] **PWA + Service Worker** — Offline dashboard, push notifications
- [ ] **WebSocket messaging** — Redis Pub/Sub backed real-time chat
- [ ] **Badge evaluation engine** — Rule-based async badge processing
- [ ] **Kubernetes migration** — Auto-scaling, rolling deployments
- [ ] **Load testing** — k6/Locust targeting 10K concurrent users

---

## Quick Reference: Before vs After

| Area | Before (Current) | After (Scaled) |
|------|-------------------|----------------|
| DB Driver | Sync `psycopg2` | Async `asyncpg` |
| Connection Pool | Default (5) | PgBouncer (200) |
| Feed | `LIMIT 50`, no pagination | Cursor-based + Redis cache |
| Leaderboard | Full table scan per request | Redis Sorted Set, O(log N) |
| SSE | In-memory Python list | Redis Pub/Sub |
| Coordinator | Load all → Python filter | SQL `HAVING` + `OFFSET/LIMIT` |
| User Profile | 4 COUNT queries per call | Denormalized columns |
| Background Jobs | In-process APScheduler | Celery + Redis broker |
| Caching | None | Redis with TTL strategy |
| Monitoring | `print()` / `logger` | Prometheus + Grafana + Sentry |
| Deployment | Single `uvicorn --reload` | Gunicorn (4 workers) + Docker |

---

*Last updated: 2026-03-01*
*Author: System Design Review*
