# The Leaderboard Cache-Coherence Bug — Explained

This document is a post-mortem of a family of bugs in the leaderboard, all of which
share **one root cause**: the leaderboard was served from a Redis copy of data whose
source of truth lives in Postgres, and the copy was allowed to drift from the
original.

It is written for someone new to the codebase. If you remember one sentence, make it
this: **every bug below is the same bug wearing a different hat — a second copy of the
truth that nobody kept in sync.**

Audited and fixed 2026-08-02 / 03. Numbers in this document were measured against
production.

---

## Table of Contents

1. [How the leaderboard worked](#1-how-the-leaderboard-worked)
2. [Why a cache is a liability, not just a feature](#2-why-a-cache-is-a-liability)
3. [Bug 1 — the NULL filter that hid 2,441 students](#3-bug-1--the-null-filter)
4. [Bug 2 — forum XP that never reached the board](#4-bug-2--forum-xp-never-synced)
5. [Bug 3 — stale entries that were never pruned](#5-bug-3--no-pruning)
6. [Bug 4 — the silently-empty board](#6-bug-4--silent-failure)
7. [What was fixed](#7-what-was-fixed)
8. [What is still recommended](#8-what-is-still-recommended)

---

## 1. How the leaderboard worked

The public leaderboard (`GET /api/leaderboard`) did **not** read from Postgres. It read
from Redis. Two structures in [`leaderboard_cache.py`](../backend/leaderboard_cache.py)
held the data:

- `lb:xp` — a Redis **sorted set** (ZSET) mapping `user_id → xp_total`. Sorted sets keep
  members ordered by score, so "top 100 by XP" is a single `ZREVRANGE lb:xp 0 99`.
- `lb:meta:<user_id>` — one **hash** per user holding display name, username, level, and
  level title (the fields the board renders but doesn't rank by).

The cache had exactly three moments where it was written:

1. **Startup seed** — `seed_from_db()`, called from the FastAPI lifespan in
   [`main.py`](../backend/main.py), loaded every eligible student and populated both
   structures.
2. **Incremental update** — after a student earned tutorial XP, the route pushed the new
   total to Redis.
3. **Read** — `get_top()` did the `ZREVRANGE` plus a pipelined batch of `HGETALL`s.

Postgres remained the source of truth: `users.xp_total` is the real number. Redis was a
**mirror** of it, maintained by hand. The mirror is where every bug lived.

```
  Postgres  ──(hand-written sync)──▶  Redis  ──(read)──▶  /api/leaderboard
 (the truth)                        (a copy)
```

---

## 2. Why a cache is a liability

The purpose of the Redis mirror was speed: "top 100 by XP" from a sorted set is O(log N).
That reasoning is sound in the abstract. The problem is what it costs you.

A cache introduces a **second source of truth**, and now you own a new, permanent job:
keeping the two in agreement on **every** path that changes the data. Miss one path and
the copy drifts. The drift is silent — the board still returns 100 rows, they're just the
**wrong** 100 rows, and nothing errors. You find out weeks later during an audit, not
seconds later from a stack trace.

Measured cost of the thing the cache was buying us: at 5,446 students, the equivalent
Postgres query —

```sql
SELECT id, display_name, username, xp_total, level
FROM users
WHERE role = 'student' AND is_test_account IS NOT TRUE
ORDER BY xp_total DESC
LIMIT 100;
```

— runs in **0.11 ms** on an index scan of `idx_users_xp_total`, and takes the *same*
0.11 ms at 100,000 students (a `LIMIT 100` on a descending index never looks past row
100). The cache was saving us a fraction of a millisecond we did not need to save, in
exchange for four bugs.

Hold that trade-off in mind while reading the four bugs. Each one is a coherence failure
that a direct query could not have had.

---

## 3. Bug 1 — the NULL filter

**The symptom.** 77 of the true top-100 students were missing from the public
leaderboard. The board padded the empty ranks with 0-XP accounts. Entire colleges'
strongest students simply weren't there.

**Why it happened.** `seed_from_db()` filtered eligible students with:

```python
select(User).filter(User.role == "student", User.is_test_account != True)
```

SQLAlchemy renders `!= True` as SQL `is_test_account != true`. Under SQL's **three-valued
logic**, `NULL != true` evaluates to `NULL`, not `true` — so **every row where
`is_test_account` was NULL was silently excluded** from the `WHERE` clause.

And 2,441 students *were* NULL. The `is_test_account` column was added nullable with only
a Python-side default, so the entire Feb–May 2026 legacy cohort — imported by bulk SQL
that never set the flag — held NULL rather than `false`. These were real students, all
with emails, colleges, and progress records.

Critically: **a restart did not fix this.** The filter re-excluded them on every seed. The
incremental-update path used Python truthiness (`not user.is_test_account`, where `None`
is falsy), so it *would* have pushed a NULL student — but only if they earned new XP,
which none of the archived cohort had done since May.

The two writers disagreed about what NULL meant. That is the signature of a coherence
bug.

**The fix.** Fixed at the schema level, not by patching the filter. Migration
[`a1b2c3d4e5f6`](../backend/alembic/versions/a1b2c3d4e5f6_backfill_is_test_account_not_null.py)
backfills every NULL to `false` and makes the column `NOT NULL DEFAULT false`. Once NULL
cannot exist, `!= True` is correct everywhere by construction, and a future bulk import
cannot reintroduce the bug. This mattered beyond the leaderboard: the same `!= True`
idiom appears ~15 times across admin and coordinator routes, and **19 colleges were
rendering completely empty** on their coordinator dashboards for the same reason.

---

## 4. Bug 2 — forum XP never synced

**The symptom.** XP a student earned by asking or answering forum questions did not appear
on the leaderboard — until the next backend restart happened to reseed the whole cache
from Postgres.

**Why it happened.** Two code paths changed `users.xp_total`, and only one of them told
Redis:

- The **tutorial** route pushed to Redis after awarding XP. ✅
- The **forum** service (`_award_forum_xp` / `_revoke_forum_xp`) updated
  `users.xp_total` in Postgres and **never called the Redis update**. ❌

So Postgres was right and Redis was stale. The board lagged reality by however long it had
been since the last restart. This is the purest form of the coherence problem: a new
write path was added, and the obligation to update the mirror was forgotten — because the
compiler cannot enforce "and also update the other copy."

**The fix.** See §7 — a single `sync_user()` helper now owns this, called from *every*
path that moves XP.

---

## 5. Bug 3 — no pruning

**The symptom.** A student who was deleted, demoted from `student`, or flagged as a test
account could remain on the leaderboard indefinitely.

**Why it happened.** `seed_from_db()` only ever **added** members (`ZADD`). It never
cleared `lb:xp` first. So the sorted set was append-only in practice: the write-path
filters could stop *new* writes for an ineligible user, but nothing removed an entry that
was already there. The mirror could hold members the source of truth no longer considered
eligible.

**The fix.** A direct query has no pruning problem — an ineligible student simply fails
the `WHERE` clause on the next read and is gone. If the ZSET is kept, the seed must build
into a temporary key and `RENAME` over the live one (atomic replace), so removals take
effect. See §8.

---

## 6. Bug 4 — silent failure

**The symptom.** If Redis was slow or down, the leaderboard returned **empty** — an
ordinary-looking blank board, no error.

**Why it happened.** `get_top()` wrapped its Redis calls in a broad `try/except` that
logged a warning and `return []`. A blank leaderboard is indistinguishable from "no data
yet," so an outage looked like a normal, if boring, state. Failures should be **loud**;
this one was silent.

**The fix.** A direct Postgres query surfaces a real error if the database is
unreachable, rather than fabricating a plausible empty result. (If the cache is retained,
the fallback on a cache miss should be to query Postgres, not to return `[]`.)

---

## 7. What was fixed

Two commits addressed the drift directly, and one addressed the schema root cause.

**Schema (`a1b2c3d4e5f6`)** — `is_test_account` backfilled and made `NOT NULL DEFAULT
false`, killing Bug 1 at the source. Also fixed 19 empty coordinator dashboards.

**One writer, one eligibility rule** — a single `sync_user(user)` helper in
[`leaderboard_cache.py`](../backend/leaderboard_cache.py) now owns write-path eligibility
(real students only) and is called **post-commit** from all three XP writers: the tutorial
route, the forum webhook, and the background XP worker. Previously the eligibility rule was
copy-pasted in one place and absent in two. Post-commit ordering is deliberate — the cache
must never get ahead of the database.

**Forum XP awarded at event time** — the webhook path used to tick the dashboard flag and
defer the XP to a worker sweep that, in practice, almost never ran (production held 4 forum
XP events against 4,930 flagged tutorial rows — a ~49k XP shortfall for the legacy cohort).
Awarding now happens inline through `recompute_tutorial_xp`, so the flag and the XP move in
one transaction and Bug 2 cannot recur. (Full detail: the forum-XP back-pay is documented
separately.)

After the fix, the served board matched the database top-100 exactly, with zero score,
name, or level mismatches and zero 0-XP padding.

---

## 8. What is still recommended

The fixes above make the mirror correct. The stronger move is to question whether the
mirror should exist at all.

**Recommendation: serve the leaderboard directly from Postgres**, optionally behind the
existing 60-second TTL cache helper ([`cache.py`](../backend/cache.py)). The query is
0.11 ms at 20× current scale (§2). Doing so **deletes an entire class of bug** rather than
adding machinery to manage it:

| Bug | Why it becomes impossible |
|-----|---------------------------|
| NULL filter (Bug 1) | The eligibility filter lives in one query, not a separate seed path. |
| Forum XP unsynced (Bug 2) | Nothing to push, so nothing to forget to push. |
| No pruning (Bug 3) | Ineligible rows fail the `WHERE` on the next read automatically. |
| Silent empty board (Bug 4) | A failed query surfaces an error instead of a fake empty result. |

Doing this removes ~90 lines of sync code (`update_user_xp`, `sync_user`, `seed_from_db`,
the lifespan hook, and the three post-commit call sites) and the startup-reseed dependency
("restart the backend to fix the leaderboard").

**When a Redis ZSET would genuinely earn its place again:** if you need each student's own
rank among all N (`ZREVRANK` is O(log N); the SQL equivalent is a window function over the
full table), or live rank updates pushed to clients. Neither exists today. If a "your rank:
#247" feature appears, revisit — with a measurement, not a reflex.

**If the ZSET is kept anyway** (it is legitimate real-time infrastructure), then the
coherence obligations must be met explicitly:

- eligibility defined in exactly one place (`sync_user` — done);
- every XP writer calls it post-commit (done);
- the seed builds into a temp key and `RENAME`s over the live key, so pruning works;
- cache-miss and Redis-down fall back to a Postgres query, never to `[]`.

---

## The one-paragraph takeaway

A cache is a copy, and a copy is a promise to keep two things equal on every write path,
forever. That promise is invisible — the type system can't hold you to it, and a broken
promise doesn't throw, it just serves slightly-wrong data that looks completely normal.
Before adding one, price the thing it buys you (here: 0.11 ms) against the bug class it
creates (here: four bugs, found months late). Often the fastest *correct* system is the
one with fewer copies of the truth.
