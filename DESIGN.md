# 🎓 Spoken Social — Design Document

> **"Facebook meets Duolingo meets LinkedIn, purpose-built for Spoken Tutorial"**

> **Status (August 2026):** this is the original product-design document from project
> inception (February 2026), kept as the vision reference. What shipped: the gamified
> learner dashboard, XP/levels/leaderboards, coordinator and admin analytics, forum-XP
> integration, and multi-programme support. Built but currently disabled in the UI: the
> social feed (posts, likes, comments, follows). Not built: streaks, badges UI,
> professional-profile features. For the system as it actually runs today, see
> [README.md](README.md) and [docs/SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md).

A social learning platform for college students that integrates with [Spoken Tutorial](https://spoken-tutorial.org). It combines a **gamified learner dashboard** with a **professional social network** — making open-source software learning engaging, trackable, and community-driven.

---

## 📌 Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [User Roles & Personas](#2-user-roles--personas)
3. [Information Architecture](#3-information-architecture)
4. [Feature Breakdown — Student View](#4-feature-breakdown--student-view)
5. [Feature Breakdown — Coordinator View](#5-feature-breakdown--coordinator-view)
6. [Gamification System (Duolingo-Inspired)](#6-gamification-system-duolingo-inspired)
7. [Professional Features (LinkedIn-Inspired)](#7-professional-features-linkedin-inspired)
8. [Social Features (Facebook-Inspired)](#8-social-features-facebook-inspired)
9. [Integration with Spoken Tutorial](#9-integration-with-spoken-tutorial)
10. [Page-by-Page Breakdown](#10-page-by-page-breakdown)
11. [Mobile-First Design Principles](#11-mobile-first-design-principles)
12. [Design System & Branding](#12-design-system--branding)
13. [Open Questions](#13-open-questions)

---

## 1. Platform Overview

### What is Spoken Social?

Spoken Social is a **companion web app** for the Spoken Tutorial platform. It sits alongside the existing Spoken Tutorial website and provides:

- **For Students**: A gamified dashboard to track learning progress, a social feed to connect with peers, and a professional profile to showcase skills.
- **For College Coordinators**: An admin dashboard to monitor student progress, manage training batches, and track course completions across their institution.

### How It Connects to Spoken Tutorial

```
┌─────────────────────────────────────────────────────┐
│              spoken-tutorial.org                      │
│  (Existing platform: tutorials, tests, certificates) │
│                                                       │
│   [🔗 "Join Spoken Social" button on landing page]    │
└──────────────────────┬────────────────────────────────┘
                       │ hyperlink / SSO
                       ▼
┌─────────────────────────────────────────────────────┐
│              Spoken Social (New App)                  │
│                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │  Dashboard   │  │  Social Feed │  │   Profile    │ │
│  │  (Duolingo)  │  │  (Facebook)  │  │  (LinkedIn)  │ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │        Coordinator Panel (Admin View)            │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 2. User Roles & Personas

### 👩‍🎓 Role 1: Student

| Attribute        | Details |
|------------------|---------|
| **Who**          | College students (18-24 years old) |
| **Goal**         | Learn open-source software, earn certificates, build skills portfolio |
| **Pain Points**  | Learning feels isolated, no motivation to continue, can't showcase progress |
| **Needs**        | Gamified motivation, peer community, professional skill showcase |
| **Tech Comfort** | High — uses Instagram, WhatsApp, YouTube daily |

**Student Persona — "Priya"**
> Priya is a 2nd-year B.Tech student. Her college coordinator organized a Python training workshop. She completed the tutorials but felt disconnected — she didn't know anyone else learning the same topics. She wants to ask doubts, share her progress, and show potential employers that she's skilled in Python.

---

### 🧑‍💼 Role 2: College Coordinator

| Attribute        | Details |
|------------------|---------|
| **Who**          | Faculty/staff responsible for Spoken Tutorial training at their college |
| **Goal**         | Organize training, track student progress, ensure course completions |
| **Pain Points**  | Hard to track individual student progress, no engagement visibility |
| **Needs**        | Batch management, progress analytics, reporting tools |
| **Tech Comfort** | Moderate — comfortable with dashboards and spreadsheets |

**Coordinator Persona — "Prof. Sharma"**
> Prof. Sharma coordinates Spoken Tutorial training for 200 students across 3 departments. He needs to see which students completed tutorials, who passed online tests, and generate reports for the college administration. He also wants to motivate students by showcasing top performers.

---

## 3. Information Architecture

### Student Navigation Structure

```
🏠 Home (Social Feed)
├── 📊 Dashboard
│   ├── My Progress (courses, streaks, XP)
│   ├── Learning Path (recommended next steps)
│   ├── Achievements (badges, certificates)
│   └── Calendar (upcoming tests, deadlines)
│
├── 🌐 Feed (Social)
│   ├── All Posts
│   ├── Following
│   ├── Trending
│   └── My College
│
├── 👥 Community
│   ├── Groups (topic-based: Python Learners, Linux Users, etc.)
│   ├── Discussions (Q&A threads)
│   └── Study Buddies (find peers learning same topics)
│
├── 👤 Profile (LinkedIn-style)
│   ├── About Me
│   ├── Skills & Endorsements
│   ├── Certificates
│   ├── Learning Activity
│   └── Posts & Contributions
│
├── 🔔 Notifications
│
├── 💬 Messages
│
└── ⚙️ Settings
```

### Coordinator Navigation Structure

```
🏠 Coordinator Home
├── 📊 Analytics Dashboard
│   ├── Institution Overview (total students, completion rates)
│   ├── Course-wise Progress
│   ├── Batch-wise Performance
│   └── Test Results Summary
│
├── 👥 Student Management
│   ├── All Students (list, search, filter)
│   ├── Student Detail View (individual progress)
│   └── Batch Management (create/manage training batches)
│
├── 📋 Reports
│   ├── Generate Reports (PDF/Excel)
│   ├── Semester Training Planner Status
│   └── Completion Certificates Status
│
├── 📢 Announcements
│   ├── Post Announcements (to batches/all students)
│   └── Schedule Reminders
│
├── 🏆 Leaderboard
│   ├── College Leaderboard
│   └── Batch-wise Leaderboard
│
└── ⚙️ Settings
```

---

## 4. Feature Breakdown — Student View

### 4.1 📊 Dashboard ("My Learning Hub")

The heart of the student experience. Inspired by Duolingo's motivational design.

**Key Components:**

| Component | Description | Inspiration |
|-----------|-------------|-------------|
| **Daily Streak Counter** | "🔥 15-day streak!" — consecutive days of learning activity | Duolingo |
| **XP Progress Bar** | Visual XP bar showing progress to next level | Duolingo |
| **Course Cards** | Cards for each enrolled course showing % completion | Coursera |
| **Learning Path Tree** | Visual skill tree showing course dependencies | Duolingo |
| **Weekly Goal Ring** | Circular progress showing weekly learning goal completion | Apple Watch |
| **Quick Actions** | "Continue Learning", "Take a Test", "Practice" | Duolingo |
| **Upcoming Deadlines** | Calendar widget showing test dates and deadlines | Google Classroom |

**Dashboard Layout (Mobile-First):**

```
┌─────────────────────────────────┐
│  👋 Hi Priya!         🔔  👤    │  ← Header with greeting
├─────────────────────────────────┤
│  🔥 15-day streak   ⚡ 2,450 XP │  ← Streak + XP bar
│  ████████████░░░ Level 12       │
├─────────────────────────────────┤
│  📅 Weekly Goal: 4/5 tutorials  │  ← Weekly goal ring
│       ◯◯◯◯                      │
│    ◯       ◯   80%              │
│       ◯◯◯◯                      │
├─────────────────────────────────┤
│  ▶ Continue: Python Lesson 7    │  ← Continue Learning CTA
│    ████████░░ 70% complete      │
├─────────────────────────────────┤
│  📚 My Courses                  │
│  ┌──────┐ ┌──────┐ ┌──────┐   │  ← Horizontal scroll cards
│  │Python│ │Linux │ │Scilab│   │
│  │ 70%  │ │ 45%  │ │ 10%  │   │
│  └──────┘ └──────┘ └──────┘   │
├─────────────────────────────────┤
│  🏆 Achievements                │
│  [🥇 Python Basics] [🔒 ???]   │  ← Badge collection
│  [🥈 First Post]    [🔒 ???]   │
├─────────────────────────────────┤
│  🗓 Upcoming                    │
│  • Feb 28 — Python Online Test  │  ← Calendar/deadlines
│  • Mar 5  — Linux Workshop      │
├─────────────────────────────────┤
│   🏠    📊    ➕    👥    👤    │  ← Bottom navigation bar
│  Feed  Dash  Post  Groups  Me  │
└─────────────────────────────────┘
```

### 4.2 🌐 Social Feed ("What's Happening")

The Facebook-style feed where students share, learn, and engage.

**Post Types:**

| Post Type | Description | Example |
|-----------|-------------|---------|
| **Learning Win** | Auto-generated when completing a course/test | "🎉 Priya completed Python Basics!" |
| **Question** | Ask doubts with code snippets and tags | "How do I use list comprehension in Python?" |
| **Resource Share** | Share helpful links, notes, tips | "Found this great cheatsheet for Linux commands" |
| **Project Showcase** | Share projects built using learned skills | "Built a calculator app using Python!" |
| **Discussion** | Open-ended topic discussions | "Which is better for data science: R or Python?" |
| **Poll** | Quick community polls | "What should I learn next? 🐍 Python / 🐧 Linux" |

**Feed Interactions:**

- 👍 Like / ❤️ React (multiple reaction types like Facebook)
- 💬 Comment (threaded replies)
- 🔄 Share / Repost
- 🔖 Bookmark
- 🏷️ Tag topics (#Python, #Linux, #SpokenTutorial)

**Feed Filters:**
- **All** — everything from everyone
- **Following** — only from people you follow
- **My College** — only from your institution
- **Trending** — most engaged posts this week

### 4.3 👤 Profile ("My Professional Identity")

LinkedIn-inspired profile that doubles as a **learning portfolio**.

**Profile Sections:**

```
┌─────────────────────────────────┐
│  ┌─────┐                       │
│  │ 📸  │  Priya Sharma          │  ← Profile photo + name
│  │     │  B.Tech CSE, Year 2    │
│  └─────┘  ABC Engineering College│
│           Level 12 • 2,450 XP   │
│           🔥 15-day streak      │
│                                 │
│  [Follow]  [Message]            │
├─────────────────────────────────┤
│  📝 About                       │
│  "Passionate about open-source  │
│   software and Python dev..."   │
├─────────────────────────────────┤
│  🛠 Skills & Endorsements       │
│  Python ████████░░ 12 endorsements│
│  Linux  ██████░░░░ 8 endorsements │
│  Scilab ████░░░░░░ 4 endorsements │
├─────────────────────────────────┤
│  🏅 Certificates                │
│  [Python Basics — Spoken Tutorial]│
│  [Linux Essentials — Spoken Tutorial]│
├─────────────────────────────────┤
│  🏆 Badges                      │
│  [🔥 30-day Streak] [📚 5 Courses]│
│  [💬 Helpful Answer] [⭐ Top 10] │
├─────────────────────────────────┤
│  📊 Learning Activity           │
│  ▁▃▅▇█▅▃▁▃▅▇ (GitHub-style heatmap)│
├─────────────────────────────────┤
│  📝 Recent Posts                 │
│  • "How I learned Python in..."  │
│  • "Tips for Linux beginners..." │
└─────────────────────────────────┘
```

---

## 5. Feature Breakdown — Coordinator View

### 5.1 📊 Analytics Dashboard

**Key Metrics (Top Cards):**

| Metric | Description |
|--------|-------------|
| **Total Students** | Number of registered students from the institution |
| **Active Learners** | Students with activity in last 7 days |
| **Avg. Completion Rate** | Average course completion % across all students |
| **Tests Passed** | Total online tests passed this semester |
| **Top Course** | Most popular/enrolled course |

**Charts & Visualizations:**

- **Completion Funnel**: Enrolled → Started → 50% → Completed → Tested → Certified
- **Course-wise Bar Chart**: Completion rates by course
- **Weekly Activity Trend**: Line chart of daily active learners
- **Department-wise Heatmap**: Which departments are most active

**Dashboard Layout:**

```
┌──────────────────────────────────────────────────┐
│  🏫 ABC Engineering College    [Prof. Sharma] 🔔  │
├──────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐            │
│  │ 247  │ │ 182  │ │ 68%  │ │ 156  │            │
│  │Total │ │Active│ │Compl.│ │Tests │            │
│  │Stdnts│ │Learn.│ │Rate  │ │Passed│            │
│  └──────┘ └──────┘ └──────┘ └──────┘            │
├──────────────────────────────────────────────────┤
│  📈 Weekly Activity     │  📊 Course Completion   │
│  ╱╲    ╱╲               │  Python  ████████ 82%   │
│ ╱  ╲╱╱  ╲              │  Linux   ██████░░ 65%   │
│╱        ╲              │  Scilab  ████░░░░ 45%   │
│  M T W T F S S          │  C/C++   ███░░░░░ 38%   │
├──────────────────────────────────────────────────┤
│  🏆 Top Performers       │  ⚠️ At-Risk Students    │
│  1. Priya S. — 2450 XP  │  • Rahul M. — 0 activity│
│  2. Amit K.  — 2100 XP  │  • Sneha P. — stuck 2wk │
│  3. Divya R. — 1890 XP  │  • Arjun T. — failed test│
├──────────────────────────────────────────────────┤
│  📋 Recent Activity                               │
│  • 12 students completed Python Lesson 5 today    │
│  • 3 students passed Linux online test            │
│  • New batch "CSE Sem 4" needs 15 more enrollments│
└──────────────────────────────────────────────────┘
```

### 5.2 👥 Student Management

- **Student List**: Searchable, filterable table (by batch, course, department, status)
- **Student Detail**: Click into a student to see their full progress timeline
- **Batch Management**: Create batches, assign students, set deadlines
- **Bulk Actions**: Send reminders, export data, assign courses

### 5.3 📋 Reports

- **Semester Reports**: Auto-generated semester-wise training summary
- **STPS Tracking**: Semester Training Planner Status (matches Spoken Tutorial's existing concept)
- **Export Formats**: PDF, Excel, CSV
- **Scheduled Reports**: Auto-email weekly/monthly reports

### 5.4 📢 Announcements

- Post announcements visible to all students or specific batches
- Schedule future announcements
- Push notifications to students

---

## 6. Gamification System (Duolingo-Inspired)

### 6.1 XP (Experience Points) System

| Activity | XP Earned |
|----------|-----------|
| Watch a tutorial | +10 XP |
| Complete a tutorial (with practice) | +25 XP |
| Pass a quiz | +50 XP |
| Pass an online test | +100 XP |
| Help someone (accepted answer) | +30 XP |
| Daily login | +5 XP |
| Share a resource | +15 XP |
| Get endorsement | +10 XP |

### 6.2 Levels

| Level | XP Required | Title |
|-------|-------------|-------|
| 1-5 | 0 - 500 | Beginner |
| 6-10 | 500 - 1,500 | Explorer |
| 11-15 | 1,500 - 3,500 | Practitioner |
| 16-20 | 3,500 - 7,000 | Expert |
| 21-25 | 7,000 - 12,000 | Master |
| 26-30 | 12,000 - 20,000 | Spoken Legend |

### 6.3 Streak System

- **Daily Streak**: Consecutive days with at least 1 learning activity
- **Streak Freeze**: Can "freeze" streak for 1 day (earned with XP or purchased with coins)
- **Streak Milestones**: Special badges at 7, 30, 100, 365 days
- **Streak Recovery**: "Weekend warrior" mode — streaks only count weekdays

### 6.4 Badges

| Category | Badges |
|----------|--------|
| **Learning** | First Tutorial, 5 Courses, 10 Courses, Speed Learner, Night Owl |
| **Testing** | First Test, Perfect Score, Test Streak (3 in a row) |
| **Social** | First Post, Helpful Answer (10 upvotes), Mentor (helped 10 people) |
| **Streaks** | 7-day, 30-day, 100-day, 365-day |
| **Special** | Early Adopter, College Champion, Bug Reporter |

### 6.5 Leaderboards

- **College Leaderboard**: Top learners in your institution
- **National Leaderboard**: Top learners across all Spoken Tutorial users
- **Course Leaderboard**: Top performers in a specific course
- **Weekly Challenge**: Reset weekly, fresh competition

---

## 7. Professional Features (LinkedIn-Inspired)

### 7.1 Skills & Endorsements

- Skills are auto-added when a course is completed
- Peers and coordinators can **endorse** skills
- Skill proficiency levels: Beginner → Intermediate → Advanced
- Skills are verified through Spoken Tutorial certificates

### 7.2 Learning Portfolio

- Public profile page that acts as a **learning resume**
- Shareable link (like LinkedIn profile URL)
- Certificates displayed with verification links (integrates with Spoken Tutorial's existing certificate verification)
- GitHub-style activity heatmap

### 7.3 Recommendations

- Coordinators can write recommendations for students
- Peer recommendations for collaborative projects
- These appear on the student's public profile

### 7.4 Job Readiness Signal

- Integration with Spoken Tutorial's existing [Job Recommendation System](https://jrs.spoken-tutorial.org/)
- "Open to opportunities" badge
- Skills-based matching with job posts

---

## 8. Social Features (Facebook-Inspired)

### 8.1 Groups

| Group Type | Description | Example |
|------------|-------------|---------|
| **Course Groups** | Auto-created for each course | "Python Learners", "Linux Users" |
| **College Groups** | Private group for each institution | "ABC Engineering — Spoken Tutorial" |
| **Batch Groups** | For specific training batches | "CSE Sem 4 — Python Batch 2026" |
| **Interest Groups** | User-created topic groups | "Web Development Enthusiasts" |

### 8.2 Messaging

- **Direct Messages**: 1-on-1 chat between students
- **Group Chat**: Within groups/batches
- **Coordinator Broadcasts**: One-way announcements from coordinators

### 8.3 Events

- **Training Workshops**: Coordinator-created events
- **Online Tests**: Synced from Spoken Tutorial schedule
- **Study Sessions**: Student-organized group study events
- **Hackathons/Challenges**: Platform-wide learning challenges

### 8.4 Notifications

| Notification Type | Example |
|-------------------|---------|
| **Social** | "Priya liked your post" |
| **Learning** | "🔥 Don't lose your streak! Complete 1 tutorial today" |
| **Achievement** | "🏆 You earned the 'Python Pro' badge!" |
| **Coordinator** | "Prof. Sharma posted an announcement" |
| **Deadline** | "⏰ Python Online Test in 3 days" |
| **Community** | "Your question received 5 answers" |

---

## 9. Integration with Spoken Tutorial

### 9.1 Data Flow

```
┌──────────────────────┐         ┌──────────────────────┐
│  spoken-tutorial.org  │ ──API──▶│    Spoken Social      │
│                      │         │                      │
│  • Course catalog    │────────▶│  • Course cards       │
│  • Tutorial progress │────────▶│  • Progress tracking  │
│  • Test results      │────────▶│  • XP calculation     │
│  • Certificates      │────────▶│  • Profile badges     │
│  • User accounts     │────────▶│  • SSO login          │
│  • STPS data         │────────▶│  • Coordinator reports│
└──────────────────────┘         └──────────────────────┘
```

### 9.2 Authentication ✅ DECIDED

- **Decision**: Use Spoken Tutorial's existing login (SSO)
- Students log in with their Spoken Tutorial credentials
- JWT tokens issued by Spoken Social after validating against Spoken Tutorial's auth
- Coordinator accounts are also sourced from Spoken Tutorial's existing coordinator system

### 9.3 Cross-College Interaction ✅ DECIDED

- **Decision**: Full cross-college interaction enabled
- Students from any college can see and interact with students from other colleges
- Feed has a "My College" filter for institution-scoped content, but "All" is the default
- College leaderboards are scoped, but national leaderboard spans all institutions

### 9.4 Coordinator Visibility ✅ DECIDED

- **Decision**: Coordinators can see everything
- Coordinators have full visibility into student social posts, learning data, and activity
- This enables coordinators to identify at-risk students and celebrate top performers
- Coordinators can moderate posts from their institution's students

### 9.5 Deep Links

Every tutorial, course, and test on Spoken Social links back to the corresponding page on spoken-tutorial.org. Users watch/practice on the original platform; progress is reflected on Spoken Social.

---

## 10. Page-by-Page Breakdown

### Student Pages

| # | Page | URL | Description |
|---|------|-----|-------------|
| 1 | **Landing/Login** | `/` | Hero page with "Join Spoken Social" CTA |
| 2 | **Onboarding** | `/onboarding` | Select interests, set goals, follow peers |
| 3 | **Social Feed** | `/feed` | Main feed with posts, filters |
| 4 | **Dashboard** | `/dashboard` | Personal learning progress hub |
| 5 | **Course Detail** | `/course/:id` | Course progress, lessons, discussions |
| 6 | **Learning Path** | `/path` | Visual skill tree of recommended courses |
| 7 | **Profile** | `/profile/:username` | Public learning portfolio |
| 8 | **Edit Profile** | `/profile/edit` | Update bio, skills, photo |
| 9 | **Groups List** | `/groups` | Browse and join groups |
| 10 | **Group Detail** | `/group/:id` | Group feed, members, resources |
| 11 | **Messages** | `/messages` | DM inbox and group chats |
| 12 | **Notifications** | `/notifications` | All notification types |
| 13 | **Leaderboard** | `/leaderboard` | College, national, course-wise rankings |
| 14 | **Achievements** | `/achievements` | Full badge collection and progress |
| 15 | **Settings** | `/settings` | Account, notifications, privacy |
| 16 | **Search** | `/search` | Search people, courses, posts, groups |
| 17 | **Create Post** | `/post/create` | Rich post editor with media, code, polls |

### Coordinator Pages

| # | Page | URL | Description |
|---|------|-----|-------------|
| 1 | **Coordinator Dashboard** | `/coordinator` | Analytics overview |
| 2 | **Student List** | `/coordinator/students` | Searchable student table |
| 3 | **Student Detail** | `/coordinator/student/:id` | Individual student progress |
| 4 | **Batch Management** | `/coordinator/batches` | Create/manage training batches |
| 5 | **Course Analytics** | `/coordinator/courses` | Course-wise performance metrics |
| 6 | **Reports** | `/coordinator/reports` | Generate and download reports |
| 7 | **Announcements** | `/coordinator/announcements` | Post and manage announcements |
| 8 | **Leaderboard Admin** | `/coordinator/leaderboard` | Leaderboard with admin actions |
| 9 | **Settings** | `/coordinator/settings` | Institution settings |

---

## 11. Mobile-First Design Principles

Since college students primarily use **mobile phones**, the design prioritizes mobile:

### Navigation Pattern

- **Bottom Tab Bar** (5 tabs max): Feed, Dashboard, Create (+), Community, Profile
- **Top App Bar**: Context-aware title + notifications bell + search
- **Swipe Gestures**: Swipe between feed tabs, swipe to dismiss
- **Pull-to-Refresh**: On feed and dashboard

### Mobile Considerations

| Principle | Implementation |
|-----------|---------------|
| **Thumb Zone** | Critical actions within easy thumb reach |
| **Touch Targets** | Minimum 44px × 44px for all interactive elements |
| **One-Handed Use** | Bottom navigation, FAB for create action |
| **Offline Support** | Cache dashboard data, queue posts for upload |
| **Low Bandwidth** | Lazy load images, compress assets, skeleton screens |
| **PWA** | Installable as app, push notifications, offline capable |

### Responsive Breakpoints

| Breakpoint | Layout |
|------------|--------|
| **< 640px** | Mobile — single column, bottom nav |
| **640-1024px** | Tablet — two columns, side navigation |
| **> 1024px** | Desktop — three columns (nav + content + sidebar) |

---

## 12. Design System & Branding

### Color Palette (Proposed)

Since this integrates with Spoken Tutorial, we should complement their existing branding:

| Color | Hex | Usage |
|-------|-----|-------|
| **Primary** | `#4F46E5` (Indigo) | CTAs, active states, links |
| **Secondary** | `#06B6D4` (Cyan) | Accents, highlights |
| **Success** | `#10B981` (Emerald) | Completed, passed, positive |
| **Warning** | `#F59E0B` (Amber) | Streaks, alerts, pending |
| **Danger** | `#EF4444` (Red) | Errors, overdue, streak lost |
| **XP Gold** | `#FBBF24` (Gold) | XP indicators, achievements |
| **Background** | `#0F172A` (Dark Slate) | Dark mode background |
| **Surface** | `#1E293B` (Slate) | Cards, panels in dark mode |
| **Text Primary** | `#F8FAFC` | Main text (dark mode) |
| **Text Secondary** | `#94A3B8` | Secondary text (dark mode) |

> **Note**: Dark mode as default (students prefer it), with light mode toggle available.

### Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| **Heading 1** | Inter | 28px | Bold (700) |
| **Heading 2** | Inter | 22px | Semibold (600) |
| **Heading 3** | Inter | 18px | Semibold (600) |
| **Body** | Inter | 16px | Regular (400) |
| **Caption** | Inter | 14px | Regular (400) |
| **Small** | Inter | 12px | Medium (500) |
| **XP/Numbers** | Space Grotesk | Varies | Bold (700) |

### Component Library

Key reusable components to build:

- `Avatar` — user profile pictures with level badges
- `CourseCard` — course preview with progress bar
- `PostCard` — social feed post with interactions
- `BadgeChip` — achievement badge display
- `StreakCounter` — animated streak flame
- `XPBar` — animated experience point bar
- `LeaderboardRow` — ranked user entry
- `StatCard` — metric display card for coordinator
- `NotificationItem` — notification with icon and timestamp
- `BottomNav` — mobile navigation bar
- `SkeletonLoader` — loading placeholder for all components

---

## 13. Technical Architecture ✅ DECIDED

### 13.1 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | React 18 + TypeScript + Vite | Fast DX, type-safe, tree-shaking, great for SPA dashboards |
| **Styling** | Vanilla CSS (CSS Modules + CSS Variables) | Full control, no framework lock-in, custom design system |
| **State Mgmt** | Zustand (UI) + TanStack Query (server) | Lightweight, caching, pagination, optimistic updates |
| **Routing** | React Router v6 | Lazy loading, nested routes, protected routes |
| **Backend** | FastAPI (Python 3.11+) | Async-first, auto OpenAPI docs, type-safe with Pydantic |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | Async queries, mature ecosystem, migration support |
| **Database** | PostgreSQL 15+ | Relational data, full-text search, JSON support |
| **Cache** | Redis | Session cache, leaderboard, real-time pub/sub, streak tracking |
| **Real-time** | WebSockets (FastAPI native) | Live notifications, messaging, streak alerts |
| **File Storage** | MinIO (self-hosted S3) or AWS S3 | Profile photos, post attachments, shared resources |
| **Auth** | JWT (access + refresh tokens) via Spoken Tutorial SSO | Stateless, secure, integrates with existing accounts |
| **API Client** | Auto-generated from OpenAPI spec (openapi-typescript) | Type-safe frontend ↔ backend contract |
| **PWA** | Workbox service worker | Installable, push notifications, offline dashboard |
| **Containerization** | Docker + Docker Compose | Consistent dev/prod, easy deployment |
| **Reverse Proxy** | Nginx | SSL termination, static file serving, load balancing |

### 13.2 System Architecture Diagram

```
                    ┌──────────────────────────┐
                    │       Nginx (Proxy)       │
                    │   SSL + Static Files      │
                    └─────┬──────────┬──────────┘
                          │          │
              ┌───────────▼──┐  ┌────▼───────────┐
              │  React SPA   │  │   FastAPI       │
              │  (Vite Build)│  │   (Backend)     │
              │              │  │                 │
              │  • Dashboard │  │  • REST API     │
              │  • Feed      │  │  • WebSocket    │
              │  • Profile   │  │  • Auth         │
              │  • Coordinator│ │  • Background   │
              └──────────────┘  │    Jobs         │
                                └───┬───┬───┬─────┘
                                    │   │   │
                    ┌───────────────▼┐ ┌▼┐ ┌▼──────────────┐
                    │  PostgreSQL    │ │R│ │ MinIO / S3     │
                    │                │ │e│ │                │
                    │  • Users       │ │d│ │  • Avatars     │
                    │  • Posts       │ │i│ │  • Attachments │
                    │  • Courses     │ │s│ │  • Certificates│
                    │  • Badges      │ │ │ │                │
                    │  • Messages    │ │ │ └────────────────┘
                    └────────────────┘ └─┘
                                        │
                    ┌───────────────────▼──────────────────┐
                    │       spoken-tutorial.org API         │
                    │  (Course data, test results, certs)  │
                    └──────────────────────────────────────┘
```

### 13.3 Database Schema (Core Tables)

```sql
-- ============== USERS & AUTH ==============

users
├── id (UUID, PK)
├── spoken_tutorial_id (INT, unique)     -- linked ST account
├── username (VARCHAR, unique)
├── email (VARCHAR, unique)
├── full_name (VARCHAR)
├── avatar_url (VARCHAR)
├── bio (TEXT)
├── college_id (FK → colleges.id)
├── department (VARCHAR)
├── year_of_study (INT)
├── role (ENUM: student, coordinator, admin)
├── xp_total (INT, default 0)
├── level (INT, default 1)
├── current_streak (INT, default 0)
├── longest_streak (INT, default 0)
├── last_activity_date (DATE)
├── is_active (BOOL)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

colleges
├── id (UUID, PK)
├── spoken_tutorial_college_id (INT)     -- linked ST college
├── name (VARCHAR)
├── city (VARCHAR)
├── state (VARCHAR)
└── created_at (TIMESTAMP)

-- ============== LEARNING ==============

courses
├── id (UUID, PK)
├── spoken_tutorial_course_id (INT)      -- linked ST course
├── title (VARCHAR)
├── description (TEXT)
├── category (VARCHAR)
├── total_tutorials (INT)
├── icon_url (VARCHAR)
└── created_at (TIMESTAMP)

user_courses
├── id (UUID, PK)
├── user_id (FK → users.id)
├── course_id (FK → courses.id)
├── tutorials_completed (INT)
├── progress_percent (DECIMAL)
├── started_at (TIMESTAMP)
├── completed_at (TIMESTAMP, nullable)
├── test_passed (BOOL)
├── test_score (INT, nullable)
└── certificate_url (VARCHAR, nullable)

-- ============== GAMIFICATION ==============

badges
├── id (UUID, PK)
├── name (VARCHAR)
├── description (TEXT)
├── icon_url (VARCHAR)
├── category (ENUM: learning, testing, social, streak, special)
├── criteria (JSONB)                     -- conditions to earn
└── xp_reward (INT)

user_badges
├── id (UUID, PK)
├── user_id (FK → users.id)
├── badge_id (FK → badges.id)
└── earned_at (TIMESTAMP)

xp_transactions
├── id (UUID, PK)
├── user_id (FK → users.id)
├── amount (INT)
├── source (ENUM: tutorial, test, post, endorsement, login, ...)
├── source_id (UUID, nullable)           -- reference to the activity
└── created_at (TIMESTAMP)

-- ============== SOCIAL ==============

posts
├── id (UUID, PK)
├── author_id (FK → users.id)
├── content (TEXT)
├── post_type (ENUM: learning_win, question, resource, project, discussion, poll)
├── media_urls (JSONB, array of URLs)
├── tags (JSONB, array of strings)
├── group_id (FK → groups.id, nullable)  -- if posted in a group
├── likes_count (INT, default 0)
├── comments_count (INT, default 0)
├── shares_count (INT, default 0)
├── is_pinned (BOOL)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

post_reactions
├── id (UUID, PK)
├── post_id (FK → posts.id)
├── user_id (FK → users.id)
├── reaction_type (ENUM: like, love, celebrate, insightful, support)
└── created_at (TIMESTAMP)

comments
├── id (UUID, PK)
├── post_id (FK → posts.id)
├── author_id (FK → users.id)
├── parent_comment_id (FK → comments.id, nullable)  -- threaded
├── content (TEXT)
├── likes_count (INT)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

groups
├── id (UUID, PK)
├── name (VARCHAR)
├── description (TEXT)
├── group_type (ENUM: course, college, batch, interest)
├── cover_image_url (VARCHAR)
├── created_by (FK → users.id)
├── member_count (INT)
├── is_private (BOOL)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

group_members
├── id (UUID, PK)
├── group_id (FK → groups.id)
├── user_id (FK → users.id)
├── role (ENUM: member, moderator, admin)
└── joined_at (TIMESTAMP)

-- ============== PROFESSIONAL ==============

skills
├── id (UUID, PK)
├── user_id (FK → users.id)
├── name (VARCHAR)                       -- e.g. "Python", "Linux"
├── proficiency (ENUM: beginner, intermediate, advanced)
├── endorsement_count (INT)
├── verified_by_certificate (BOOL)
└── created_at (TIMESTAMP)

endorsements
├── id (UUID, PK)
├── skill_id (FK → skills.id)
├── endorser_id (FK → users.id)          -- who endorses
├── endorsed_user_id (FK → users.id)     -- who gets endorsed
└── created_at (TIMESTAMP)

-- ============== MESSAGING ==============

conversations
├── id (UUID, PK)
├── type (ENUM: direct, group)
├── name (VARCHAR, nullable)             -- for group chats
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

conversation_members
├── id (UUID, PK)
├── conversation_id (FK → conversations.id)
├── user_id (FK → users.id)
├── last_read_at (TIMESTAMP)
└── joined_at (TIMESTAMP)

messages
├── id (UUID, PK)
├── conversation_id (FK → conversations.id)
├── sender_id (FK → users.id)
├── content (TEXT)
├── media_url (VARCHAR, nullable)
├── created_at (TIMESTAMP)
└── is_deleted (BOOL)

-- ============== NOTIFICATIONS ==============

notifications
├── id (UUID, PK)
├── user_id (FK → users.id)
├── type (ENUM: social, learning, achievement, coordinator, deadline, community)
├── title (VARCHAR)
├── body (TEXT)
├── action_url (VARCHAR)                 -- deep link on click
├── is_read (BOOL)
├── created_at (TIMESTAMP)
└── source_user_id (FK → users.id, nullable)

-- ============== COORDINATOR ==============

batches
├── id (UUID, PK)
├── name (VARCHAR)                       -- e.g. "CSE Sem 4 Python"
├── college_id (FK → colleges.id)
├── coordinator_id (FK → users.id)
├── course_id (FK → courses.id)
├── start_date (DATE)
├── end_date (DATE)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

batch_students
├── id (UUID, PK)
├── batch_id (FK → batches.id)
├── user_id (FK → users.id)
└── enrolled_at (TIMESTAMP)

announcements
├── id (UUID, PK)
├── author_id (FK → users.id)            -- coordinator
├── title (VARCHAR)
├── content (TEXT)
├── target_type (ENUM: all, college, batch)
├── target_id (UUID, nullable)           -- college_id or batch_id
├── scheduled_at (TIMESTAMP, nullable)
├── published_at (TIMESTAMP)
└── created_at (TIMESTAMP)

-- ============== FOLLOWS ==============

follows
├── id (UUID, PK)
├── follower_id (FK → users.id)
├── following_id (FK → users.id)
└── created_at (TIMESTAMP)
```

### 13.4 Project Folder Structure

```
spoken-social/
├── frontend/                         # React + TypeScript + Vite
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── manifest.json             # PWA manifest
│   │   └── sw.js                     # Service worker
│   ├── src/
│   │   ├── api/                      # Auto-generated API client
│   │   │   ├── client.ts             # Axios/fetch wrapper
│   │   │   ├── types.ts              # Generated from OpenAPI
│   │   │   └── endpoints/
│   │   │       ├── auth.ts
│   │   │       ├── posts.ts
│   │   │       ├── users.ts
│   │   │       ├── courses.ts
│   │   │       ├── groups.ts
│   │   │       └── coordinator.ts
│   │   ├── components/               # Reusable UI components
│   │   │   ├── common/               # Buttons, inputs, modals
│   │   │   ├── dashboard/            # Streak, XPBar, CourseCard
│   │   │   ├── feed/                 # PostCard, PostComposer
│   │   │   ├── profile/              # SkillBar, BadgeGrid
│   │   │   ├── coordinator/          # StatCard, StudentTable
│   │   │   └── layout/               # Navbar, BottomNav, Sidebar
│   │   ├── pages/                    # Route-level page components
│   │   │   ├── student/
│   │   │   │   ├── Feed.tsx
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Profile.tsx
│   │   │   │   ├── CourseDetail.tsx
│   │   │   │   ├── Groups.tsx
│   │   │   │   ├── Messages.tsx
│   │   │   │   ├── Leaderboard.tsx
│   │   │   │   └── Settings.tsx
│   │   │   ├── coordinator/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── Students.tsx
│   │   │   │   ├── Batches.tsx
│   │   │   │   ├── Reports.tsx
│   │   │   │   └── Announcements.tsx
│   │   │   ├── auth/
│   │   │   │   ├── Login.tsx
│   │   │   │   └── Onboarding.tsx
│   │   │   └── Landing.tsx
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useStreak.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useInfiniteScroll.ts
│   │   ├── stores/                   # Zustand stores
│   │   │   ├── authStore.ts
│   │   │   ├── uiStore.ts
│   │   │   └── notificationStore.ts
│   │   ├── styles/                   # CSS files
│   │   │   ├── variables.css         # Design system tokens
│   │   │   ├── global.css            # Reset + base styles
│   │   │   └── components/           # Component-specific CSS
│   │   ├── utils/                    # Helper functions
│   │   ├── App.tsx
│   │   ├── Router.tsx
│   │   └── main.tsx
│   ├── index.html
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                          # FastAPI + Python
│   ├── src/
│   │   ├── api/                      # Route handlers
│   │   │   ├── routes/
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── posts.py
│   │   │   │   ├── courses.py
│   │   │   │   ├── groups.py
│   │   │   │   ├── messages.py
│   │   │   │   ├── notifications.py
│   │   │   │   ├── gamification.py
│   │   │   │   └── coordinator.py
│   │   │   └── deps.py               # Dependency injection
│   │   ├── core/
│   │   │   ├── config.py             # Settings (env vars)
│   │   │   ├── security.py           # JWT, hashing
│   │   │   └── websocket.py          # WS connection manager
│   │   ├── db/
│   │   │   ├── database.py           # Async engine + sessions
│   │   │   ├── models/               # SQLAlchemy models
│   │   │   │   ├── user.py
│   │   │   │   ├── post.py
│   │   │   │   ├── course.py
│   │   │   │   ├── gamification.py
│   │   │   │   ├── group.py
│   │   │   │   ├── message.py
│   │   │   │   └── coordinator.py
│   │   │   └── migrations/           # Alembic migrations
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   │   ├── user.py
│   │   │   ├── post.py
│   │   │   ├── course.py
│   │   │   └── ...
│   │   ├── services/                 # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── xp_service.py
│   │   │   ├── streak_service.py
│   │   │   ├── badge_service.py
│   │   │   ├── feed_service.py
│   │   │   ├── notification_service.py
│   │   │   └── sync_service.py       # Spoken Tutorial data sync
│   │   └── main.py                   # FastAPI app entry point
│   ├── tests/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docker-compose.yml                # PostgreSQL, Redis, MinIO, Backend, Frontend
├── docker-compose.dev.yml            # Dev overrides (hot reload, etc.)
├── nginx/
│   └── nginx.conf                    # Reverse proxy config
├── DESIGN.md                         # ← This document
└── README.md
```

### 13.5 API Design (Key Endpoints)

```
# ============== AUTH ==============
POST   /api/auth/login                  # Login via Spoken Tutorial credentials
POST   /api/auth/refresh                 # Refresh JWT token
GET    /api/auth/me                      # Get current user
POST   /api/auth/onboarding             # Complete onboarding (interests, goals)

# ============== USERS ==============
GET    /api/users/:username              # Get user profile
PATCH  /api/users/me                     # Update own profile
GET    /api/users/:id/activity           # Get user activity heatmap
POST   /api/users/:id/follow             # Follow a user
DELETE /api/users/:id/follow             # Unfollow a user
GET    /api/users/:id/followers          # List followers
GET    /api/users/:id/following          # List following

# ============== FEED ==============
GET    /api/posts                        # Get feed (paginated, filterable)
POST   /api/posts                        # Create a post
GET    /api/posts/:id                    # Get single post with comments
DELETE /api/posts/:id                    # Delete own post
POST   /api/posts/:id/react              # React to a post
POST   /api/posts/:id/comments           # Comment on a post
GET    /api/posts/trending               # Get trending posts

# ============== COURSES ==============
GET    /api/courses                      # List all courses
GET    /api/courses/:id                  # Course detail with user progress
GET    /api/courses/:id/leaderboard      # Course leaderboard
POST   /api/courses/:id/sync             # Trigger sync from Spoken Tutorial

# ============== GAMIFICATION ==============
GET    /api/gamification/dashboard       # XP, level, streak, recent badges
GET    /api/gamification/badges          # All badges (earned + locked)
GET    /api/gamification/leaderboard     # Leaderboards (college, national)
GET    /api/gamification/streak          # Streak details + freeze status

# ============== GROUPS ==============
GET    /api/groups                       # List groups (filterable)
POST   /api/groups                       # Create a group
GET    /api/groups/:id                   # Group detail
POST   /api/groups/:id/join              # Join a group
GET    /api/groups/:id/posts             # Group feed

# ============== MESSAGES ==============
GET    /api/conversations                # List conversations
POST   /api/conversations                # Start a conversation
GET    /api/conversations/:id/messages   # Get messages (paginated)
POST   /api/conversations/:id/messages   # Send a message
WS     /api/ws/chat                      # Real-time messaging WebSocket

# ============== NOTIFICATIONS ==============
GET    /api/notifications                # List notifications
PATCH  /api/notifications/:id/read       # Mark as read
PATCH  /api/notifications/read-all       # Mark all as read
WS     /api/ws/notifications             # Real-time notification WebSocket

# ============== SKILLS ==============
GET    /api/users/:id/skills             # Get user skills
POST   /api/skills/:id/endorse           # Endorse a skill

# ============== COORDINATOR ==============
GET    /api/coordinator/dashboard        # Analytics overview
GET    /api/coordinator/students         # Student list (paginated, filterable)
GET    /api/coordinator/students/:id     # Student detail (full progress)
GET    /api/coordinator/batches          # List batches
POST   /api/coordinator/batches          # Create a batch
PATCH  /api/coordinator/batches/:id      # Update a batch
GET    /api/coordinator/courses          # Course analytics
GET    /api/coordinator/reports          # Generate reports
POST   /api/coordinator/announcements    # Post announcement
GET    /api/coordinator/announcements    # List announcements

# ============== SEARCH ==============
GET    /api/search                       # Unified search (users, posts, courses, groups)
```

---

## 14. Resolved Decisions

Summary of all decisions made so far:

| # | Question | Decision |
|---|----------|----------|
| 1 | Authentication | Use Spoken Tutorial's existing login (SSO with JWT) |
| 2 | Cross-College | Full interaction enabled across all colleges |
| 3 | Coordinator Visibility | Coordinators can see everything (posts + learning data) |
| 4 | Tech Stack (Frontend) | React 18 + TypeScript + Vite |
| 5 | Tech Stack (Backend) | FastAPI (Python 3.11+) |
| 6 | Database | PostgreSQL + Redis |
| 7 | Target Audience | College students (18-24) |
| 8 | Mobile Priority | Mobile-first responsive design (PWA) |
| 9 | Platform Integration | Hyperlinked to Spoken Tutorial landing page |
| 10 | Gamification Style | Duolingo-inspired (streaks, XP, badges, leaderboards) |
| 11 | Social Style | Facebook-inspired feed + LinkedIn-inspired profiles |

---

## 15. Open Questions (Remaining)

### Product Questions

1. **Data Sync**: How often should we sync data from Spoken Tutorial? Real-time API, or periodic batch sync?
2. **Content Moderation**: How do we handle inappropriate posts? Manual moderation, AI-based, or community reporting?
3. **Privacy**: Can students see each other's profiles by default, or is it opt-in? (Recommendation: public by default, like LinkedIn)
4. **Onboarding Flow**: How many steps? What information do we collect?

### Technical Questions

5. **Hosting**: Where will this be deployed? Spoken Tutorial's existing infrastructure, or separate cloud?
6. **Spoken Tutorial API**: Does Spoken Tutorial have an existing API we can consume, or do we need to build a data bridge?

### Design Questions

7. **Color Scheme**: Should we use the proposed dark indigo theme, or match Spoken Tutorial's blue/white?
8. **Feature Phasing**: Should we build everything at once, or phase the rollout?

---

## 16. Implementation Roadmap (Proposed)

### Phase 1: Foundation (Weeks 1-4)
> **Goal**: Users can log in and see their dashboard

- [ ] Project scaffolding (Vite + FastAPI + Docker)
- [ ] Database setup + migrations
- [ ] Auth flow (Spoken Tutorial SSO integration)
- [ ] Student Dashboard (streaks, XP, course progress)
- [ ] Profile page (basic — photo, bio, skills)
- [ ] Design system + component library foundation
- [ ] Mobile-responsive layout + bottom navigation

### Phase 2: Social Core (Weeks 5-8)
> **Goal**: Users can post, react, and interact

- [ ] Social Feed (post creation, reactions, comments)
- [ ] Post types (learning wins, questions, resources)
- [ ] Follow system
- [ ] Feed filters (All, Following, My College, Trending)
- [ ] Notification system (in-app)
- [ ] Search (users, posts)

### Phase 3: Gamification (Weeks 9-11)
> **Goal**: Full gamification system live

- [ ] XP system (earning, tracking, level-ups)
- [ ] Streak system (tracking, freezes, milestones)
- [ ] Badge system (criteria engine, badge awarding)
- [ ] Leaderboards (college, national, course-wise)
- [ ] Achievement animations and celebrations

### Phase 4: Community (Weeks 12-14)
> **Goal**: Groups and messaging are functional

- [ ] Groups (create, join, group feed)
- [ ] Group types (course, college, batch, interest)
- [ ] Direct messaging (WebSocket-based)
- [ ] Group chat
- [ ] Events (training workshops, tests)

### Phase 5: Coordinator Panel (Weeks 15-17)
> **Goal**: Coordinators can manage and track students

- [ ] Coordinator analytics dashboard
- [ ] Student management (list, detail, filters)
- [ ] Batch management (create, assign, track)
- [ ] Reports (PDF/Excel generation)
- [ ] Announcements system

### Phase 6: Professional Features (Weeks 18-20)
> **Goal**: LinkedIn-style professional identity

- [ ] Skills & endorsements system
- [ ] Certificate showcase (linked to Spoken Tutorial verification)
- [ ] Learning activity heatmap
- [ ] Recommendations from coordinators/peers
- [ ] Public shareable profile links
- [ ] Job readiness integration

### Phase 7: Polish & Launch (Weeks 21-24)
> **Goal**: Production-ready with PWA

- [ ] PWA setup (service worker, offline, push notifications)
- [ ] Performance optimization (lazy loading, caching)
- [ ] Accessibility audit (WCAG 2.1 AA compliance)
- [ ] Security audit (OWASP top 10)
- [ ] Load testing
- [ ] Beta launch with select colleges
- [ ] Feedback collection and iteration

---

## Next Steps

Now that architecture and tech stack are decided, the immediate next steps are:

1. **📐 UI Mockups** — Generate visual designs for key pages (Dashboard, Feed, Profile, Coordinator)
2. **🔄 User Flow Diagrams** — Map the critical journeys (login → onboarding → first post)
3. **🗃️ Database Schema Refinement** — Review and finalize the schema
4. **🚀 Project Scaffolding** — Set up the Vite + FastAPI + Docker boilerplate
