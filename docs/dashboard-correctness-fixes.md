# Dashboard Correctness Fixes — Explained

This document walks through a batch of **correctness** fixes to the admin/coordinator
dashboards and the XP system. These are not performance fixes — they're cases where the
app was showing **wrong numbers** or had a **security hole**.

It's written for someone new to the codebase. Each fix follows the same shape:

- **The symptom** — what a user would actually see going wrong.
- **Why it happened** — the root cause, in plain terms.
- **The fix** — what changed and why that's correct.

A quick mental model of how XP and progress flow through this app, which most of these
bugs touch:

```
Student ticks "watched/practiced" on a tutorial
        │
        ▼
PUT /api/me/courses/{course}/tutorials/{tut}   ← update_tutorial()
        │   recomputes UserTutorial.xp_earned from the checkboxes
        │   and adds the delta to User.xp_total
        ▼
Dashboards read it back two different ways:
  • per-course aggregates  → SUM(UserTutorial.xp_earned)   (what a course "cost")
  • global lifetime total  → User.xp_total                  (all courses + forum)
```

The single biggest source of bugs below is that **the same idea ("a student's XP") is
stored and summed in several different ways**, and different screens picked different
ones — so two tabs can show two different numbers for the same student. This batch fixes
the clear-cut cases; the deeper "unify XP into one definition" work is tracked separately.

---

## Fix C1 — Anyone could give themselves unlimited XP (`POST /api/me/xp`)

**The symptom.** A student could jump to #1 on the public leaderboard instantly, hit the
max level, and permanently inflate every admin XP chart — without cheating any real task.

**Why it happened.** There was an endpoint, `POST /api/me/xp`, that took a number from the
request body and added it straight to the caller's XP:

```python
# BEFORE — routes/user.py
async def add_xp(body: XPUpdate, user = Depends(get_current_user), db = ...):
    user.xp_total += body.amount        # body.amount is whatever the client sends
    db.add(XPEvent(user_id=user.id, xp_delta=body.amount, ...))
    await update_user_xp(...)            # ← pushes to the public leaderboard
```

Two problems: (1) `Depends(get_current_user)` means **any logged-in user** (i.e. any
student) could call it; (2) `body.amount` was unbounded. And the app never actually calls
this endpoint — students earn XP only by ticking tutorial steps (`update_tutorial`) or via
the forum worker. So it was a door nobody used but anyone could walk through.

> **Beginner note.** In web apps, the *client* (the browser) can send any request it wants —
> you can't trust it to "only send reasonable numbers." Every value that changes data must
> be checked on the *server*. "The UI never sends a bad value" is not a defense, because an
> attacker doesn't use your UI; they call the endpoint directly.

**The fix.** Lock the door: require an admin, and bound the inputs.

```python
# AFTER — routes/user.py
async def add_xp(body: XPUpdate, user = Depends(require_admin), db = ...):
    if not body.source or len(body.source) > 50:      # avoid a DB error too (column is 50 chars)
        raise HTTPException(400, "source must be 1–50 characters")
    if abs(body.amount) > 1000:
        raise HTTPException(400, "amount must be within -1000..1000")
    ...
```

`Depends(require_admin)` makes a student's call return **403 Forbidden**. The bounds stop
even an admin from injecting a wild number. (Since nothing calls this endpoint, deleting it
outright would also be reasonable — locking it is the reversible choice.)

Verified: student → 403, admin sending 999999 → 400, admin sending 50 → 200.

---

## Fix H1 — The Comparison tab mixed *fake* data into *real* data

**The symptom.** On the Comparison tab, an admin could see one real programme bar sitting
right next to invented bars ("ILW: 520 students, 85% progress, 2450 avg XP") that looked
exactly as real. Filtering by a state not in the demo set made *every* number on screen a
scaled fabrication. There was no way to tell real from fake.

**Why it happened.** The endpoint has a legitimate "demo mode" (hardcoded sample numbers)
for showing off the UI on an empty database. But it also **spliced that demo data in
per-programme**: if a real programme happened to have no batches or no students, it quietly
dropped a mock entry into the otherwise-real response.

```python
# BEFORE — routes/admin.py, inside the loop over real programmes
if not prog_batches:
    mock_prog = next(p for p in mock_data["programmes"] if p["id"] == prog.id)
    programmes_list.append(mock_prog)   # ← fake numbers, no flag, next to real ones
    continue
```

> **Beginner note.** Demo/placeholder data is fine — but it must be *clearly separated*
> from real data, never blended into the same response unlabeled. Otherwise the person
> reading the screen makes decisions on numbers that were never real.

**The fix.** When a real programme has no data, show it **truthfully as zero**, not as mock:

```python
# AFTER
if not prog_batches:
    programmes_list.append({
        "id": prog.id, "name": prog.name, "color": ...,
        "metrics": {"colleges": 0, "students": 0, "progress": 0, "avgXP": 0},
        "courses": [],
    })
    continue
```

Now an empty programme reads "0 students" (honest). The whole-app demo mode (when the DB is
genuinely empty, or the explicit Demo toggle is on) is untouched.

Verified: with real data, FDP shows 2,280 real students while Swayam Plus / ILW show a real
`0` — no `850`/`2450` mock values anywhere.

---

## Fix H4 — The admin Feedback tab ignored the batch selector

**The symptom.** Every admin tab is filtered by the selected batch — except Feedback. Pick
"Jan 2026" and the Feedback tab still shows all batches' entries, so its totals silently
disagree with every neighboring tab (and with the coordinator's feedback view, which *does*
filter by batch).

**Why it happened.** A subtle one. The frontend *sends* a `batch_id` query parameter, but
the backend function never *declared* it:

```python
# BEFORE — routes/admin.py
async def get_feedback_summary(course_id=..., tutorial_id=..., step_type=...,
                               reason=..., college_id=..., user=..., db=...):
    # no batch_id parameter here → FastAPI just drops the ?batch_id=... it receives
```

> **Beginner note.** In FastAPI, a request only "sees" the query parameters you list in the
> function signature. Anything else the client sends is silently ignored — no error. So a
> filter can *look* wired up on the frontend yet do nothing, because the backend never
> agreed to receive it.

**The fix.** Declare the parameter and apply it the same way the coordinator endpoint does —
join the student's enrollment for this course and filter by batch:

```python
# AFTER
async def get_feedback_summary(..., batch_id: Optional[str] = Query(None), ...):
    ...
    if batch_id:
        base_query = base_query.join(
            UserCourse,
            (UserCourse.user_id == TutorialFeedback.user_id) & (UserCourse.course_id == course_id),
        ).filter(UserCourse.batch_id == batch_id)
```

(`UserCourse`'s primary key is `(user_id, course_id)`, so this join matches at most one row
per feedback entry — it filters, it doesn't duplicate rows.) The batch is also added to the
cache key so batch-filtered and unfiltered results don't overwrite each other in Redis.

---

## Fix H6 — Coordinator status chips counted only the current page

**The symptom.** A coordinator opens a college with 200 learners. The filter chips read
"All (10)". Click "Active" and the "Completed" chip flips to "(0)". Every chip count is
wrong except by luck.

**Why it happened.** The table is *paginated* — the server sends 10 students at a time. But
the chip counts were computed by counting that 10-row page in the browser:

```tsx
// BEFORE — CoordinatorDashboard.tsx
{ id: 'all',    count: details?.students.length }                                  // = 10
{ id: 'active', count: details?.students.filter(s => s.status === 'active').length }
```

`details.students` is only the current page (and it's already filtered by the active chip),
so counting it can never give the true cohort totals.

> **Beginner note.** With server-side pagination, the browser only ever holds a slice of the
> data. Any "how many total?" question must be answered by the **server** (which can see all
> the rows), not by counting the slice you happen to have.

**The fix.** The server already computes the whole-cohort breakdown for its summary, so we
expose it as a `statusCounts` object and the chips read from that:

```python
# AFTER — routes/coordinator.py (get_college_details response)
"statusCounts": {
    "all": s["totalStudents"],
    "active": s["activeStudents"] - s["completedStudents"],  # summary "active" includes completed
    "completed": s["completedStudents"],
    "at_risk": s["atRiskStudents"],
    "inactive": s["inactiveStudents"],
},
```
```tsx
// AFTER — CoordinatorDashboard.tsx
{ id: 'all',    count: details?.statusCounts?.all }
{ id: 'active', count: details?.statusCounts?.active }
```

One gotcha worth understanding: the summary's `activeStudents` already *includes* completed
students (it's `active + completed`), so the "Active" chip subtracts `completed` back out to
show the strict active bucket. Verified: the four buckets sum exactly to `all`, regardless of
page size.

---

## Fix M5 — The MiniTask export didn't match the MiniTask screen

**The symptom.** The MiniTasks table shows 40 opt-ins for the selected batch. Click Export
and the downloaded spreadsheet has 130 rows — different batches, plus students not even
enrolled in the course. The report you exported doesn't reconcile with the screen you
exported it from.

**Why it happened.** The on-screen analysis and the export are two different queries that
drifted apart. The analysis joins `UserCourse` (enrolled students only) and honors the batch
filter; the export did neither:

```python
# BEFORE — export query
.join(UserTutorial, ...).join(Tutorial, ...)
.filter(User.role == "student", UserTutorial.minitask_opted == True,
        Tutorial.course_id == course_id)      # no enrollment join, no batch_id
```

> **Beginner note.** When two features are supposed to show "the same data" (a screen and
> its export button), they should ideally share **one** query. When they don't, they drift —
> someone fixes a filter in one place and forgets the other. Matching their filters exactly
> is the minimum; sharing a helper is the real fix.

**The fix.** Give the export the same enrollment join and batch filter, and pass the batch
from the frontend:

```python
# AFTER
.join(UserCourse, UserCourse.user_id == User.id)
.filter(..., UserCourse.course_id == course_id)
if batch_id:
    query = query.filter(UserCourse.batch_id == batch_id)
```
```tsx
// AFTER — AdminDashboard.tsx export button
const batchParam = activeBatchId ? `&batch_id=${activeBatchId}` : '';
api.get(`/api/admin/minitask-students/export?course_id=${activeCourseId}${batchParam}`, ...)
```

Now the export population equals the screen population.

---

## Fix M2 — Test accounts appeared on the public leaderboard

**The symptom.** Auto-generated "Test Student" placeholder accounts — invisible on every
admin/coordinator tab — could occupy ranks on the public, student-facing leaderboard.

**Why it happened.** The leaderboard is seeded from the database at startup, filtering by
role but not by the test-account flag:

```python
# BEFORE — leaderboard_cache.py
result = await db.execute(select(User).filter(User.role == "student"))
```

Every other aggregate in the app excludes `is_test_account`; the leaderboard seed forgot to.

**The fix.** Add the same exclusion everything else uses:

```python
# AFTER
result = await db.execute(
    select(User).filter(User.role == "student", User.is_test_account != True)
)
```

Verified: the startup seed dropped from 2,284 to 2,280 students — exactly the 4 test
accounts, now excluded.

> **Known limitation (follow-up).** This fixes the *seed*. There's a second, smaller leak:
> `update_user_xp` is called on every XP write regardless of who the user is, so a coordinator
> or admin who triggers an XP change can still be added to the live leaderboard set, and
> nothing ever removes stale entries. Closing that needs a role guard at the call sites plus a
> cleanup pass — tracked separately, not in this batch.

---

## Summary

| Fix | Severity | What a user saw | One-line change in spirit |
|-----|----------|-----------------|---------------------------|
| C1 | Critical (security) | Anyone could mint unlimited XP | Require admin + bound the inputs |
| H1 | High (trust) | Fake bars beside real ones on Comparison | Show real zeros, never splice mock |
| H4 | High | Feedback tab ignored the batch filter | Declare + apply the `batch_id` param |
| H6 | High | Chip counts were the 10-row page, not the cohort | Serve whole-cohort `statusCounts` |
| M5 | Medium | Export ≠ on-screen table | Match enrollment + batch filter |
| M2 | Medium | Test accounts on public leaderboard | Exclude `is_test_account` in the seed |

### Not in this batch (bigger, needs a decision)

The audit found deeper issues that are **not** simple fixes because they require a product
decision on *what the number should mean*:

- **One canonical XP definition.** Today "a student's XP" is computed 4 ways (course-scoped
  `xp_earned`, all-course `xp_earned`, global `xp_total`, and `XPEvent` sums), so Overview,
  Colleges, Analytics, and Comparison can each show a different XP for the same student. And
  two writers (`update_tutorial` recomputing from checkboxes vs. the forum worker adding)
  fight over the same `xp_earned` column, causing drift. Fixing this well means choosing one
  definition and one writer — a design task, not a patch.
- **The weekly leaderboard** ("This Week" tab) sorts by `xp_last_week`, a field nothing ever
  recomputes — so it shows frozen/zero data. It should be hidden until a weekly rollup job
  exists.
- **The daily-XP chart** sums XP events that aren't course-tagged and averages over only the
  students active that day; making it truthful needs a course tag on `XPEvent` (a schema
  change) and a denominator decision.

---

# Round 2 — the XP unification (the root-cause fix)

The single biggest theme in the audit was that **"a student's XP" was computed several
different ways**, so different tabs disagreed. This round makes one definition and fixes the
two writers that were corrupting the underlying number. Decisions taken with the product
owner: **course dashboards show course-scoped XP** (only the selected course's XP); the
**leaderboard and profile keep global lifetime XP**; and **forum XP counts once per tutorial
per activity type** (asked / answered), not per post.

## Part A — One writer for `xp_earned` (stop the drift)

**The symptom.** A student's XP could briefly double, then snap back down later — leaving a
fake "reversion" in their XP history and making every course dashboard's XP unreliable.

**Why it happened.** Two functions wrote the same column, `UserTutorial.xp_earned`, with
**incompatible models**:

- `update_tutorial` (when you tick a step) **recomputed** it from the checkboxes:
  `xp_earned = sum of XP_MAP over the true flags`.
- `_award_forum_xp` (when the forum worker verifies a post) **incremented** it:
  `xp_earned += amount`.

Because `forum_asked` / `forum_answered` are *also* in the checkbox map, the sequence
"student self-marks answered → worker verifies the same post → student later toggles
anything" went `10 → 20 (double) → 10 (recompute wipes it, logs a -10 'reversion')`.

> **Beginner note.** If two pieces of code write the same field, they must agree on *what
> the field means*. "Recompute from scratch" and "add to what's there" are two different
> contracts; mixing them means whoever runs last wins, and the value oscillates. The cure is
> a **single source of truth**: one function that both callers use.

**The fix.** A new `services/xp.py` owns the definition, and both writers call it:

```python
# services/xp.py — xp_earned is ALWAYS a pure function of the flags
def recompute_tutorial_xp(ut) -> int:
    old = ut.xp_earned or 0
    ut.xp_earned = sum(XP_MAP[col] for col in XP_MAP if getattr(ut, col) is True)
    return ut.xp_earned - old      # delta to apply to the user's global xp_total
```

`update_tutorial` and `_award_forum_xp` (and the delete/revoke path) now all set the flag,
call `recompute_tutorial_xp`, and apply the returned delta. Since it's recompute-not-add,
the worker verifying an already-counted answer returns delta `0` — no double-count — and
there's no later "reversion". A second forum answer on the same tutorial also returns `0`
(that's the "once per type" rule; you can't farm XP by spamming posts).

Verified with the exact audit scenario: self-tick → worker-verify → toggle now goes
`+10 → +0 → +10` (stable at 20), and a second answer adds `+0`.

## Part B — Course-scope the dashboard XP (make the tabs agree)

**The symptom.** The same college showed a different "avg XP" on the Overview tab vs the
Analytics tab vs the Comparison tab. A student who did nothing in Linux but earned XP in
Python still counted toward the *Linux* dashboards.

**Why it happened.** The per-student XP was summed like this at four sites:

```python
func.sum(UserTutorial.xp_earned)          # every tutorial the student ever did — all courses
```

The query *joined* the course's tutorials, but summing `xp_earned` over the un-restricted
`UserTutorial` rows still pulled in other courses' XP. (One site — the Colleges summary —
was already course-scoped from earlier work, which is exactly why it disagreed with the
others.)

> **Beginner note.** In a `LEFT JOIN`, filtering the *joined* table (here, restricting
> `tutorials` to one course) does **not** remove rows from the *driving* table — it just
> leaves the joined columns `NULL`. So `SUM(user_tutorials.xp_earned)` still adds up every
> row. To scope the sum, you must put the condition *inside* the SUM.

**The fix.** Use the same course-scoped pattern everywhere (only sum XP when the tutorial
actually belongs to this course):

```python
func.sum(case((Tutorial.id.isnot(None), UserTutorial.xp_earned), else_=0))
```

Applied to all four remaining sites: `platform-summary` (Overview/Analytics), the Colleges
student table (`_get_student_rows`), `get_college_analytics`, and `comparison-metrics`
(which had used the *global* `User.xp_total` — now a course-scoped sum). A bonus: the
"Inactive vs Not-started" split keys on XP, so it's now course-accurate too.

The leaderboard and profile were **left alone** — they intentionally show global lifetime XP.

Verified: avg XP now matches across Overview / Analytics / the student table for the same
college; and concrete leaks closed — e.g. a student with 1065 XP across courses but 400 in
Linux now shows **400** on Linux dashboards (was 1065), while the leaderboard still shows
1065.

## Two small related fixes (same round)

- **Weekly leaderboard tab hidden.** The "This Week" tab sorted by `xp_last_week`, a field
  nothing ever recomputes — so it showed frozen/zero data. The tab is removed until a real
  weekly-rollup job exists. (The all-time board is unaffected.)
- **Daily-XP chart relabeled.** Its XP isn't course-scoped (XPEvents aren't tagged by
  course), so calling it "Daily Average XP by College" for a specific course was misleading.
  It's now "Daily XP Activity by College *(all activity, not course-specific)*" — honest
  about what it shows until XPEvents carry a course tag.

## Round-2 summary

| Fix | What a user saw | The change in spirit |
|-----|-----------------|----------------------|
| XP-A | XP doubled then snapped back, phantom "reversions" | One recompute-from-flags writer for `xp_earned` |
| XP-B | Same college's avg XP differed across tabs; Python XP counted toward Linux | Course-scope the SUM at all four sites |
| Weekly tab | "This Week" showed frozen/zero ranks | Hide it until a weekly job feeds it |
| Daily-XP label | Course chart secretly included other-course XP | Relabel as overall activity |

---

# Round 3 — remaining correctness bugs

Four smaller, unambiguous fixes.

## M3 — Profile progress bar could exceed 100%

**Symptom.** A level-1 student at 450 XP saw a progress bar at **112%** — full and overflowing — without leveling up.

**Why.** `xpForNextLevel` used `100 · (level+1)²` = 400 for level 1, but the student actually
levels up at **500** (the real thresholds are 500 / 1500 / 3500 / 7000 / 12000). So
`450 / 400 = 112%`.

**Fix.** `xpForNextLevel` is now the next *real* milestone from `services/xp` (`450 → 500`,
so the bar reads a coherent 90%), returning the current XP at max level (100%). Backend-only —
the frontend already renders `xpTotal / xpForNextLevel`.

## M4 — Feedback totals included test/placeholder accounts

**Symptom.** The Feedback tab could report more "affected students" than the college has real
learners, because QA/test accounts' feedback was counted.

**Why.** Every other aggregate filters `role == "student"` and `is_test_account != True`; the
feedback queries (both dashboards, plus the reason dropdowns) didn't.

**Fix.** Added the same filter to all four feedback queries.

## Pagination — a student could appear twice, or vanish, between pages

**Symptom.** Paging a college's student list, the same student could show on page 1 *and* page 2,
or be skipped.

**Why.** The sort ordered by a single non-unique column (e.g. `progress DESC`). Most students sit
at 0% progress, so ties had **no defined order** — and Postgres is free to return tied rows in a
different order on each query, which shifts the page boundaries.

> **Beginner note.** Pagination (`LIMIT/OFFSET`) only works if the total order is *deterministic*.
> Any sort on a non-unique column needs a unique **tiebreaker** (here, the student id) so "row 11"
> is always the same row.

**Fix.** Every sort branch now appends `, sub.c.id` as a unique tiebreaker. Verified: page 1 is
identical across repeated calls and never overlaps page 2.

## Invalid student id returned 500

`GET /students/{id}/feedback` did `uuid.UUID(id)` unguarded, so a malformed id raised an uncaught
`ValueError` → HTTP 500. Now it's a clean **400 Bad Request**.

## M7 — XP charts were a day off for Indian users

**Symptom.** The daily-XP chart and a student's XP-history graph attributed activity to the
**wrong calendar day** for anything earned between midnight and 5:30am IST, and events on the
1st before 5:30am IST could disappear from the month entirely.

**Why.** `created_at` is stored as `timestamptz` (an absolute instant). Casting it to a date
uses the database session's timezone — **UTC** — but the audience is in **IST** (UTC+5:30).
So a post at 02:00 IST on the 5th (= 20:30 UTC on the 4th) was bucketed to the 4th.

> **Beginner note.** A timestamp and a *calendar day* are different things: which day an
> instant falls on depends on the timezone you view it in. For day-grouped charts you must
> convert to the **audience's** timezone before extracting the date.

**Fix.** Both queries now convert to IST before bucketing —
`func.timezone(APP_TIMEZONE, created_at)` — for the day extraction *and* the month
boundaries, so they stay consistent. `APP_TIMEZONE` lives in `config.py` (defaults to
`Asia/Kolkata`, overridable by env) — change that one value to re-bucket every chart.

## M6 — "Active" meant two different things

**Symptom.** A fully-finished college showed "50 active or completed" — wait, it showed
"**50 active** on platform" — directly above a status pie where the **Active** slice was 0
and **Completed** was 50.

**Why.** The college summary's `activeStudents` is deliberately `active + completed`
("engaged"), but the label just said "active", contradicting the pie/chips that treat them
as separate buckets.

**Fix (decision: keep the number, fix the label).** The card now reads "**active or
completed**" and the Excel column is "**Active + Completed**", so the number is honest about
what it counts. (We kept the combined count rather than splitting it, per product choice.)

## Cosmetic cleanups (same round)

- **"Need attention" badge** showed the length of a list capped at 10 (so always "10");
  it now shows the true `totalAtRisk + totalInactive`.
- **Comparison legend dots** used the course index for color while the bars used a running
  per-batch index — so a dot's color didn't match its bar when a course had multiple batches.
  The legend now uses the same running index as the bars.
- **MiniTask "Total"** column relabeled "**Total Opt-ins**" (it sums opt-ins across tutorials,
  so a learner in several tutorials is counted once per tutorial — not unique learners).
- **XP graph** showed "Peak (Day 0)" for an empty month; now shows "No activity yet".
- **State filter** compared case-sensitively client-side (`.includes`) while the server used
  case-insensitive `ILIKE`; the client is now case-insensitive too, so the summary cards and
  the table below them agree.

## Still open after Round 3

Genuinely deferred, needing a schema change or a scheduled job (not a quick patch):
- **Runtime leaderboard pollution** — coordinators/admins can still be added via any XP write,
  and stale entries are never removed (needs role guards at the call sites + a cleanup pass).
- **Weekly leaderboard rollup job** — to un-hide the "This Week" tab.
- **`XPEvent.course_id`** — to make the daily-XP chart truly course-scoped (it's honestly
  labeled "all activity" for now) and to fix its "average over active-that-day students"
  denominator.
- **`totalCourseStudents`** is a copy of `totalStudents` (no real enrollment-vs-signup
  distinction exists in the data) — two cards show the same number; resolving it is a
  data-model decision, not a display fix.

---

# Round 4 — acting on the product decisions

After a plain-language review, we resolved the remaining items.

## Deleted the unused `/me/xp` endpoint + guarded the leaderboard

The locked-down `/me/xp` endpoint had no caller, so it's **removed** entirely — no reason to
keep dead attack surface. And the leaderboard now only accepts **real students**: the
"push to leaderboard" step skips admins/coordinators and test/placeholder accounts (e.g. a
test student driven while an admin is impersonating). Combined with the earlier seed fix,
the public board is students-only.

## Removed the weekly leaderboard

The "This Week" tab, the trend arrows, and the "vs last week" text are **gone** from the UI,
and the backend no longer returns or populates the weekly/trend fields. The feature never
worked (nothing computed weekly XP) and it's cleaner to remove than to fake.

> **Note left for you:** the underlying `xp_last_week` database column is now unused but
> still present. Fully dropping it would mean editing ~10 seed/setup scripts and a leftover
> weekly-calculation SQL file — a lot of churn to delete a harmless empty field — so I left
> it as dead-but-safe. Say the word if you want it swept out.

## Removed the duplicate count card

The coordinator view no longer shows two cards ("Registered for Course" / "Registered on
Spoken Social") that always held the identical number. It's now a single, honest
"Registered Learners".

## The daily-XP chart is now genuinely course-specific

This is the "label the points with their course" work. Every points-diary entry
(`XPEvent`) now records **which course** it was earned in, set at each write path (tutorial
completion, forum award/revoke). The daily chart filters on that, so a course's chart shows
**only that course's points** — matching every other metric.

> **Beginner note.** We couldn't retro-fill old points: past diary entries never recorded a
> course, and their leftover ids don't reliably map back to one. So the chart is course-true
> from now on; historical points simply don't appear under a specific course (rather than
> being mis-attributed). New activity is correct from day one.

Also fixed the **top-N cutoff**: the chart only loads the top colleges, but the checkbox list
used to offer *every* college — so ticking one with no data drew a blank line that looked
like "zero activity". The checklist now lists only colleges actually on the chart.

## What's genuinely finished vs. left

Per your calls: leaderboard cleanup job → **not needed** (admins/coordinators don't earn
points; guard added for the edge case). Weekly leaderboard → **removed**. Duplicate label →
**removed**. Feedback rewrite → **parked** until there's data. Daily chart → **course-scoped**.

The only thing still on the table is the optional `xp_last_week` column drop (noted above).

