# 🎓 Spoken Social — Project Brief & Platform Capabilities

> **Executive Brief & Capabilities Document**  
> **Platform:** Spoken Social  
> **Ecosystem:** [Spoken Tutorial](https://spoken-tutorial.org), IIT Bombay  
> **Target Audience:** Students, College Coordinators, Faculty Mentors, and Programme Administrators  
> **Status:** Production (Active deployment serving 5,400+ students across 170+ colleges)

---

## 1. Executive Summary

**Spoken Social** is a companion gamified learning management and community platform built specifically for [Spoken Tutorial](https://spoken-tutorial.org) (an initiative of IIT Bombay funded by the Ministry of Education, Govt. of India). 

While the core Spoken Tutorial platform excels at course cataloging, video distribution, and certification exams, self-paced distance learning often suffers from **"silent drop-off"**—students get stuck, lose momentum in isolation, and stop progressing without generating any actionable signal.

Spoken Social bridges this gap by acting as **"Duolingo meets LinkedIn meets a Collaborative Learning Community"** for open-source software training:
- **For Students:** It transforms solitary tutorial watching into an engaging, gamified journey with micro-progress tracking, experience points (XP), level progressions, and friendly college/course leaderboards.
- **For College Coordinators:** It gives faculty mentors a real-time, drill-down command center to monitor batch progress, spot at-risk or stalled learners early, and export institutional compliance reports.
- **For Programme Administrators:** It delivers multi-institution analytics across all training cohorts with continuous data-integrity checks.

---

## 2. What We Intend to Achieve (Core Objectives)

| Objective | Problem Addressed | Spoken Social Solution |
|---|---|---|
| **Eliminate "Silent Drop-Off"** | Students stall in isolation when facing technical hurdles (e.g., installation errors, syntax confusion) with zero feedback to teachers. | Granular micro-milestones and immediate feedback capture when a student cannot complete an activity, routing diagnostic reasons directly to coordinators. |
| **Track the "Messy Middle"** | Traditional systems only log initial enrollment and the final exam certificate, leaving the actual learning process invisible. | Per-tutorial state machine recording every learning step: video watched, hands-on practice, assignment completed, and forum questions. |
| **Gamified Extrinsic & Intrinsic Motivation** | Self-paced courses lack urgency and positive reinforcement. | Dual-incentive gamification: XP earned per action, 6 level tiers (Beginner to Spoken Legend), and multi-scoped, IST-aligned leaderboards. |
| **Institutional Accountability** | College coordinators manage hundreds of students across multiple departments without visibility into who is actually practicing. | Real-time coordinator dashboard grouping students into actionable cohorts (*Completed*, *Active*, *At-Risk*, *Stalled*), with one-click Excel reports. |
| **Collaborative Community Learning** | Students learn in silos with no peer interaction. | Integrated forum rewards (+5 XP for asking, +10 XP for answering) with anti-abuse mechanisms and a social engagement architecture. |

---

## 3. What the Platform Can Do (Current Capabilities)

### 3.1 👩‍🎓 Student Experience
1. **Granular Tutorial Tracker:**
   - Step-by-step progress tracking for every tutorial in an enrolled course.
   - Clear distinction between passive consumption and active work: **Watched**, **Practiced**, **Assignment Done**, and **Mini-Task Opted**.
   - Progressive unlocking mechanics that guide learners sequentially through the syllabus.
2. **Deterministic XP & Leveling Engine:**
   - Single-writer, accounting-grade XP engine preventing double-counting and race conditions.
   - Transparent rule map:
     - 🎬 **Watch Tutorial:** +10 XP
     - 💻 **Hands-on Practice:** +10 XP
     - 📝 **Tutorial Assignment:** +5 XP
     - ❓ **Ask Doubt in Forum:** +5 XP
     - 💡 **Answer Doubt in Forum:** +10 XP
   - 6 progressive level tiers (from *Level 1: Beginner* to *Level 26+: Spoken Legend*).
3. **Multi-Scope, Real-Time Leaderboards:**
   - **Scopes:** Global (Platform-wide), College (Intra-institutional competition), and Course (Topic-specific).
   - **Time Windows:** All-Time, Monthly, and Weekly (strictly bound to Indian Standard Time).
   - Instant rank retrieval (`RANK()` in PostgreSQL) with tie-ranking and dedicated top-3 podium display.
4. **Diagnostic Friction Feedback:**
   - When a student marks "No" on practice or assignments, an intuitive modal captures the exact obstacle (e.g., software installation failure, OS compatibility issue, lack of computer lab access, concept difficulty).
5. **Learner Profile:**
   - Overview of total XP, current level, tutorial breakdown, and course completion status.

### 3.2 🧑‍🏫 Coordinator & Administrator Experience
1. **Live Institution Command Center:**
   - Overview cards: Total Enrolled Students, Active Learners (last 7 days), Course Completion Rate, and At-Risk Count.
   - Status Cohort classification:
     - **Completed:** 100% of tutorials and assignments cleared.
     - **Active:** Progress made within recent days.
     - **At-Risk:** Slowing down or falling behind cohort schedule.
     - **Stalled / Inactive:** Zero activity recorded.
2. **Student Drill-Down View:**
   - Searchable, filterable student roster by batch, department, course, and status.
   - Inspect individual student timelines down to the exact tutorial and step where they stopped.
3. **Friction Analysis & Roadblock Heatmaps:**
   - Aggregated views of why students are not practicing or submitting assignments, allowing faculty to arrange targeted lab assistance.
4. **Institutional Compliance & Reporting:**
   - One-click styled Excel (`.xlsx`) export of student progress and batch completion for college records and Semester Training Planner (STP) audits.
5. **Administrator Multi-College Supervision:**
   - Platform-level analytics across 170+ colleges, course distributions, and cross-institutional benchmarks.
   - Audited **User Impersonation Flow** allowing admins to troubleshoot student and coordinator issues without credential sharing.

### 3.3 🛡️ Ecosystem & System Integrity
1. **Seamless Ecosystem Integration:**
   - Direct credential verification against Spoken Tutorial's auth API (no separate user database or passwords required).
   - Signed webhooks for forum activity syncing.
2. **Anti-Abuse Forum XP Verification:**
   - A 24-hour verification window ensures forum XP is only credited if a question or answer survives undeleted, neutralizing spam or post-then-delete farming.
3. **Nightly Invariant Engine:**
   - Automated nightly integrity checks verifying that user XP, journaled events, and tutorial flags remain mathematically consistent.

---

## 4. Learning Activities That Can Be Hosted on the Platform

Spoken Social is designed to support both **self-paced open learning** and **structured cohort-based training** (such as Faculty Development Programmes - FDPs, semester college courses, and student workshops).

The platform accommodates a diverse range of learning activities:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          HOSTED LEARNING ACTIVITIES                             │
├──────────────────────┬──────────────────────┬───────────────────────────────────┤
│  1. Video Screencasts│  2. Hands-on Practice│  3. Formative Assignments         │
│     (Passive Intake) │     (Side-by-Side)   │     (Application of Knowledge)    │
├──────────────────────┼──────────────────────┼───────────────────────────────────┤
│  4. Practical Tasks  │  5. Peer Q&A Forums  │  6. Diagnostic Roadblock Reports  │
│     (Mini-Challenges)│     (Community Doubts│     (Reflective Friction Capture) │
├──────────────────────┼──────────────────────┼───────────────────────────────────┤
│  7. Cohort Workshops │  8. Milestone Tests  │  9. Social & Project Showcases    │
│     (FDPs & Batches) │     (Certifications) │     (Peer Learning - Extensible)  │
└──────────────────────┴──────────────────────┴───────────────────────────────────┘
```

### Detailed Breakdown of Learning Activities:

1. **Self-Paced Screencast Video Learning ("Watched")**
   - Students watch Spoken Tutorial's audio-video tutorials in various languages (English, Hindi, Tamil, Telugu, Marathi, etc.).
   - Covers diverse software domains: Programming (Python, C, C++, Java), Open Source Systems (Linux, Bash), Computational Tools (Scilab, R, Octave), Creative Suites (Blender, GIMP, Inkscape), Web Technologies (HTML, PHP, MySQL), and Academic Tools (LaTeX, LibreOffice).

2. **Side-by-Side Guided Software Practice ("Practiced")**
   - The foundational philosophy of Spoken Tutorial is *learning by doing*.
   - Students replicate the tutorial commands, scripts, or interface workflows on their local machine or college lab systems simultaneously.
   - Earns +10 XP upon completing the hands-on exercise.

3. **Tutorial-Specific Homework & Assignments ("Assignment Done")**
   - Practical assignments attached to individual tutorials (e.g., writing a Python script to sort data, configuring a Linux directory permission structure, plotting equations in Scilab).
   - Verifies concept comprehension and earns +5 XP.

4. **Optional Practical Mini-Tasks ("Mini-Task Opted")**
   - Targeted challenge tasks designed for students seeking extra practice or deeper exploration of a tool.

5. **Peer-to-Peer Collaborative Doubt Resolution ("Forum Activity")**
   - **Asking Doubts (+5 XP):** Encourages inquisitive learning. When students get stuck on syntax errors or installation hiccups, they post detailed questions on the Spoken Tutorial forums.
   - **Answering Peers (+10 XP):** Encourages active mastery and mentorship. Students reinforce their own understanding by troubleshooting and explaining solutions to fellow cohort members.

6. **Self-Diagnostic Roadblock & Feedback Reporting**
   - An active metacognitive learning activity. If a student is unable to practice or complete an assignment, they log their reason (e.g., "Software wouldn't install", "Permission denied", "Need instructor clarification").
   - This turns a moment of failure into a high-visibility support ticket for coordinators.

7. **Structured Cohort Programmes & Faculty Development Programmes (FDPs)**
   - Batch-based learning with start and end dates, departmental rosters, and scheduled milestones.
   - Coordinators assign courses to specific academic batches (e.g., "CSE 3rd Semester Linux Workshop" or "Faculty FDP on Scilab").

8. **Assessment Prep & Certification Milestones**
   - Pre-test readiness tracking leading up to Spoken Tutorial's official proctored online certification exams.

9. **Social Learning & Project Showcases (Extensible / Built-in Architecture)**
   - Peer social feeds (implemented in the backend) for sharing code snippets, mini-projects built using learned tools, asking open-ended discussions, and celebrating milestone badges.

---

## 5. Technology & Architecture Highlights

- **Frontend:** Modern, responsive React 19 + TypeScript (strict mode), Vite 7, Tailwind CSS, TanStack Query, and Recharts.
- **Backend:** High-performance async FastAPI (Python 3.10+), SQLAlchemy 2.0 with `asyncpg`, Alembic database migrations.
- **Database:** PostgreSQL 16 with 27 tables, 30 performance indexes (covering indexes, composite indexes for sub-millisecond leaderboard queries).
- **Asynchronous Processing:** Redis 7 and `arq` background workers handling forum XP reconciliation and nightly data consistency checks.
- **Observability:** Prometheus, Grafana Loki, Grafana Alloy, node-exporter, and a 12-tool Model Context Protocol (MCP) server for AI-driven operations and diagnostics.
- **Deployment:** Docker Compose on cloud VM, verified in production.

---

## 6. Summary: Value Proposition

| Stakeholder | Before Spoken Social | With Spoken Social |
|---|---|---|
| **Student** | Learns alone; drops out silently when confused; only feedback is a pass/fail certificate at the very end. | Active gamified journey; earns XP and levels; tracks rank against college peers; doubts resolved via forum; clear next steps. |
| **Faculty Coordinator** | Blind to whether students are actually practicing; spends hours collating manual attendance and spreadsheet reports. | Real-time visibility into student progress; instant identification of at-risk students; one-click Excel reports for accreditation. |
| **Spoken Tutorial / IIT Bombay** | High initial enrollment with uncertain daily engagement levels across 100+ partner institutions. | Comprehensive macro and micro analytics; high student retention; verified learning integrity across all national cohorts. |
