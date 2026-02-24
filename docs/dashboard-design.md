# 📊 Learner's Dashboard — Detailed Design

> The dashboard is the **first thing a student sees** after logging in.
> It must answer three questions instantly:
> 1. **"How am I doing?"** — Streak, XP, level
> 2. **"What should I do next?"** — Continue learning CTA
> 3. **"What have I achieved?"** — Badges, certificates, progress

---

## 📌 Table of Contents

1. [Dashboard Philosophy](#1-dashboard-philosophy)
2. [Layout Overview](#2-layout-overview)
3. [Section-by-Section Breakdown](#3-section-by-section-breakdown)
4. [Mobile Layout](#4-mobile-layout)
5. [Desktop Layout](#5-desktop-layout)
6. [Interactions & Micro-Animations](#6-interactions--micro-animations)
7. [Data Requirements](#7-data-requirements)
8. [Component Hierarchy](#8-component-hierarchy)
9. [States & Edge Cases](#9-states--edge-cases)

---

## 1. Dashboard Philosophy

### Design Principles

| Principle | How We Apply It |
|-----------|----------------|
| **Motivate, don't overwhelm** | Show progress, not workload. "70% done" feels better than "3 tutorials remaining" |
| **Gamify without being childish** | Professional aesthetic (not cartoonish), but with satisfying animations and dopamine hits |
| **One primary CTA** | "Continue Learning" button should be the most prominent element after the greeting |
| **Progressive disclosure** | Show summary on dashboard, detail on click-through |
| **Celebrate wins** | Every completion, streak milestone, and badge earns a celebration moment |

### Emotional Journey

```
Login → "Welcome back! 🔥 15-day streak!" → Feel good
      → "You're 70% through Python" → Feel motivated
      → "Continue Lesson 7 →" → Clear next step
      → See XP bar filling up → Feel rewarded
      → See badge unlocked → Feel accomplished
```

---

## 2. Layout Overview

### Mobile (Primary) — Single Column

```
┌─────────────────────────────────────┐
│  ┌─────────────────────────────┐    │
│  │ 1. TOP BAR                  │    │  Fixed
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 2. GREETING + STREAK BANNER │    │  ← Hero section
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 3. XP + LEVEL CARD          │    │  ← Gamification summary
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 4. CONTINUE LEARNING        │    │  ← Primary CTA
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 5. WEEKLY GOAL TRACKER      │    │  ← Goal progress
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 6. MY COURSES               │    │  ← Horizontal scroll
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 7. ACHIEVEMENTS PREVIEW     │    │  ← Recent badges
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 8. ACTIVITY HEATMAP         │    │  ← GitHub-style
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 9. UPCOMING DEADLINES       │    │  ← Calendar items
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 10. RECOMMENDED FOR YOU     │    │  ← Smart suggestions
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 11. BOTTOM NAVIGATION       │    │  Fixed
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### Desktop (1024px+) — Three Column

```
┌──────────────────────────────────────────────────────────────────┐
│  TOP BAR (logo, search, notifications, profile)                  │
├─────────┬───────────────────────────────────────┬────────────────┤
│         │                                       │                │
│  LEFT   │         MAIN CONTENT                  │   RIGHT        │
│  NAV    │                                       │   SIDEBAR      │
│         │  ┌───────────────────────────────┐    │                │
│  Feed   │  │ Greeting + Streak Banner       │    │  ┌──────────┐ │
│  Dash ● │  └───────────────────────────────┘    │  │ Weekly   │ │
│  Groups │  ┌──────────┐ ┌──────────────────┐    │  │ Goal     │ │
│  Msgs   │  │ XP Card  │ │ Continue Learning│    │  │ Tracker  │ │
│  Profile│  └──────────┘ └──────────────────┘    │  └──────────┘ │
│         │  ┌───────────────────────────────┐    │  ┌──────────┐ │
│         │  │ My Courses (grid)              │    │  │ Upcoming │ │
│         │  └───────────────────────────────┘    │  │ Deadlines│ │
│         │  ┌───────────────────────────────┐    │  └──────────┘ │
│         │  │ Activity Heatmap               │    │  ┌──────────┐ │
│         │  └───────────────────────────────┘    │  │ Achieve- │ │
│         │  ┌───────────────────────────────┐    │  │ ments    │ │
│         │  │ Recommended For You            │    │  └──────────┘ │
│         │  └───────────────────────────────┘    │                │
│         │                                       │                │
└─────────┴───────────────────────────────────────┴────────────────┘
```

---

## 3. Section-by-Section Breakdown

### 3.1 🔝 Top Bar

**Purpose**: Navigation and quick actions

**Mobile:**
```
┌─────────────────────────────────────┐
│  🟣 Spoken Social    🔍    🔔(3)  👤│
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| Logo | "Spoken Social" wordmark or icon |
| Search icon | Opens search overlay |
| Notification bell | Badge count for unread notifications |
| Avatar | Quick access to profile |

**Behavior:**
- Sticky on scroll (stays at top)
- On scroll down → shrinks to compact version
- Notification badge pulses when new notifications arrive

---

### 3.2 👋 Greeting + Streak Banner

**Purpose**: Warm welcome + instant streak motivation

```
┌─────────────────────────────────────┐
│                                     │
│  👋 Good evening, Priya!            │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  🔥 15-day streak!          │    │
│  │  Your longest: 23 days      │    │
│  │  Keep it going!             │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Greeting** | Time-aware: "Good morning/afternoon/evening, {name}!" |
| **Streak flame** | Animated fire icon (CSS animation, subtle bounce) |
| **Streak count** | Large, bold number with "day streak" label |
| **Longest streak** | Subtle text showing personal record |
| **Background** | Gradient card — warm orange/amber when streak is active, gray when broken |

**Streak States:**

| State | Visual |
|-------|--------|
| Active (1-6 days) | Small flame, amber background |
| Strong (7-29 days) | Medium flame, orange background |
| On Fire (30+ days) | Large animated flame, red-orange gradient, particle effects |
| Broken (0 days) | Gray, no flame, "Start a new streak today!" message |
| Frozen (streak freeze used) | Blue snowflake overlay, "Streak frozen for today" |

---

### 3.3 ⚡ XP + Level Card

**Purpose**: Show overall gamification progress

```
┌─────────────────────────────────────┐
│                                     │
│  Level 12 — Practitioner            │
│  ⚡ 2,450 / 3,500 XP               │
│  ████████████████░░░░░░ 70%         │
│                                     │
│  +25 XP today  •  +180 XP this week│
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Level number** | Large, with level title (Beginner → Explorer → Practitioner → ...) |
| **XP progress bar** | Animated fill, gradient from primary to gold |
| **XP fraction** | "2,450 / 3,500 XP" — current vs. needed for next level |
| **Daily/Weekly XP** | Small text showing recent XP gains |

**Interaction:**
- Tap/click → expands to show XP breakdown (from tutorials, tests, social, etc.)
- When XP bar completes → **level-up celebration animation** (confetti + badge)

---

### 3.4 ▶️ Continue Learning (Primary CTA)

**Purpose**: **THE most important element.** One-tap to continue exactly where they left off.

```
┌─────────────────────────────────────┐
│                                     │
│  📚 Continue Learning               │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  🐍                         │    │
│  │  Python - Lesson 7           │    │
│  │  "Working with Dictionaries" │    │
│  │                              │    │
│  │  ████████████░░░░░ 70%       │    │
│  │                              │    │
│  │  [▶ Resume Lesson]           │    │  ← Primary button
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Course icon** | Small icon or emoji for the course (e.g., 🐍 for Python) |
| **Course + Lesson name** | Course title and current lesson title |
| **Progress bar** | Shows progress within the course |
| **Resume button** | Large, prominent — primary color, rounded |
| **Deep link** | Clicking "Resume" opens the tutorial on spoken-tutorial.org in a new tab |

**Edge Cases:**
- **No courses enrolled**: Shows "Explore Courses" CTA instead
- **All courses completed**: Shows "Start a New Course" with recommendations
- **Multiple in-progress**: Shows the most recently accessed one, with a "Switch course" dropdown

---

### 3.5 📅 Weekly Goal Tracker

**Purpose**: Show progress toward weekly learning goal

```
┌─────────────────────────────────────┐
│                                     │
│  📅 Weekly Goal                     │
│                                     │
│       ◯◯◯◯◯◯◯                       │  ← 7 circles for 7 days
│    (M)(T)(W)(T)(F)(S)(S)            │
│    ✅ ✅ ✅ ✅  ○  ○  ○              │
│                                     │
│  4 of 5 tutorials completed         │
│  1 more to hit your weekly goal! 💪 │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Day circles** | 7 circles (Mon-Sun), filled for days with activity |
| **Goal progress** | Text showing progress toward weekly target |
| **Motivational text** | Dynamic: "Almost there!", "Crushing it!", "Start strong!" |
| **Goal setting** | User can set their own weekly goal (3, 5, or 7 tutorials/week) |

**Visual:**
- Completed days = filled circle with checkmark (primary color)
- Today (if not yet done) = pulsing circle with dotted border
- Future days = empty circle, gray border
- When goal is met → 🎉 celebration animation + bonus XP

---

### 3.6 📚 My Courses

**Purpose**: Overview of all enrolled courses with progress

**Mobile — Horizontal Scroll:**
```
┌─────────────────────────────────────┐
│                                     │
│  📚 My Courses              See All │
│                                     │
│  ┌──────────┐ ┌──────────┐ ┌─────  │
│  │  🐍      │ │  🐧      │ │ 📊   │  ← Swipeable
│  │  Python   │ │  Linux    │ │ Sci  │
│  │           │ │           │ │      │
│  │ ██████░░  │ │ ████░░░░  │ │ ██░  │
│  │   70%     │ │   45%     │ │  10% │
│  │           │ │           │ │      │
│  │ 7/10 done │ │ 5/11 done │ │ 1/10│
│  └──────────┘ └──────────┘ └─────  │
│                                     │
└─────────────────────────────────────┘
```

**Desktop — Grid (2-3 columns):**
```
┌──────────────────────────────────────────┐
│  📚 My Courses                   See All  │
│                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  🐍      │ │  🐧      │ │  📊      │ │
│  │  Python   │ │  Linux    │ │  Scilab   │ │
│  │  70%      │ │  45%      │ │  10%      │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────┘
```

**Each Course Card Contains:**

| Element | Details |
|---------|---------|
| **Course icon/emoji** | Visual identifier |
| **Course name** | Short title |
| **Progress bar** | Colored bar (green when complete, primary when in-progress) |
| **Progress %** | Numeric percentage |
| **Tutorials count** | "7/10 done" |
| **Status badge** | "In Progress", "Completed ✅", "Not Started" |
| **Test status** | "Test Passed ✅" or "Test Available" or hidden |

**Interaction:**
- Tap card → goes to Course Detail page
- Cards are sorted: In Progress first, then Not Started, then Completed
- "See All" → full course list page

---

### 3.7 🏆 Achievements Preview

**Purpose**: Show recently earned badges + tease upcoming ones

```
┌─────────────────────────────────────┐
│                                     │
│  🏆 Achievements            See All │
│                                     │
│  Recently Earned:                   │
│  ┌────┐ ┌────┐ ┌────┐              │
│  │ 🔥 │ │ 📚 │ │ 💬 │              │
│  │7-day│ │5   │ │1st │              │
│  │strek│ │done│ │post│              │
│  └────┘ └────┘ └────┘              │
│                                     │
│  Next up:                           │
│  🔒 "30-day Streak" — 15 days away │
│  🔒 "Python Master" — 3 tutorials  │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Recent badges** | Last 3 earned, with icons and names |
| **Locked badges** | Next 2 closest to earning, with progress hint |
| **Badge icons** | Custom designed, colorful when earned, grayscale when locked |

**Interaction:**
- Tap a badge → show full-screen badge detail modal with description and date earned
- "See All" → full achievements page with all categories

---

### 3.8 📊 Activity Heatmap

**Purpose**: Visual representation of learning consistency (like GitHub contribution graph)

```
┌─────────────────────────────────────┐
│                                     │
│  📊 Learning Activity               │
│                                     │
│  Jan                          Feb   │
│  ░░▓▓█░░░▓▓█▓░░░▓▓██▓░░▓█████░░░   │
│  ░▓▓██░░▓▓███░░░▓█████░░▓████▓░░   │
│  ░░▓██░░░▓▓█▓░░░░▓███▓░░░▓██▓░░░   │
│  ░░▓▓█░░░▓▓██░░░▓▓████░░▓████▓░░   │
│  ░░░▓▓░░░░▓▓█░░░▓▓███░░░▓▓██░░░░   │
│  ░░░░░░░░░░▓▓░░░░░▓▓▓░░░░░▓░░░░░   │
│  ░░░░░░░░░░░▓░░░░░░▓░░░░░░░░░░░░   │
│                                     │
│  Less ░░▓▓██ More                   │
│                                     │
│  142 tutorials in the last 90 days  │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Grid** | 13 weeks × 7 days (3 months of data) |
| **Color intensity** | Ranges from empty (no activity) to dark (heavy activity) |
| **Legend** | "Less → More" color scale |
| **Summary text** | Total activity count for the period |

**Interaction:**
- Hover/tap a cell → tooltip showing date and activity (e.g., "Feb 15: 3 tutorials completed")
- Color scale uses primary color (indigo) at different opacities

**Mobile Optimization:**
- On mobile, show last 8 weeks instead of 13 weeks (fits the screen)
- Horizontally scrollable if needed

---

### 3.9 🗓 Upcoming Deadlines

**Purpose**: Never miss a test or workshop

```
┌─────────────────────────────────────┐
│                                     │
│  🗓 Upcoming                        │
│                                     │
│  ┌─────────────────────────────┐    │
│  │ 📝  Feb 28 (4 days)         │    │
│  │     Python Online Test       │    │
│  │     🏫 Lab 201, 10:00 AM    │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 🎓  Mar 5 (9 days)          │    │
│  │     Linux Training Workshop  │    │
│  │     🏫 Computer Lab, 2 PM   │    │
│  └─────────────────────────────┘    │
│  ┌─────────────────────────────┐    │
│  │ 📝  Mar 12 (16 days)        │    │
│  │     Scilab Online Test       │    │
│  │     📍 TBD                   │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Event type icon** | 📝 Test, 🎓 Workshop, 📅 Deadline |
| **Date + countdown** | "Feb 28 (4 days)" — relative time |
| **Event name** | Name of the test/workshop |
| **Location** | Venue or "Online" |

**Color coding:**
- Red border if < 3 days away (urgent)
- Yellow border if < 7 days (soon)
- Default border otherwise

**Empty State:**
- "No upcoming events. You're all clear! 🎉"

---

### 3.10 🎯 Recommended For You

**Purpose**: AI-powered course recommendations to keep learning

```
┌─────────────────────────────────────┐
│                                     │
│  🎯 Recommended For You             │
│                                     │
│  Based on your Python progress:     │
│                                     │
│  ┌──────────┐ ┌──────────┐         │
│  │  🌐      │ │  📊      │         │
│  │  Django   │ │  Pandas   │         │
│  │  Web Dev  │ │  Data Sci │         │
│  │           │ │           │         │
│  │ [Explore] │ │ [Explore] │         │
│  └──────────┘ └──────────┘         │
│                                     │
│  Students who learned Python also   │
│  learned: C/C++, R, LibreOffice    │
│                                     │
└─────────────────────────────────────┘
```

| Element | Details |
|---------|---------|
| **Recommendation reason** | "Based on your Python progress" |
| **Course cards** | 2-3 suggested courses with "Explore" button |
| **Social proof** | "Students who learned X also learned Y" |

**Recommendation Logic (v1 — simple):**
- If student is doing Python → recommend Django, Pandas, Flask
- Based on course category (e.g., same FOSS category)
- Based on what students at the same college are learning
- Later (v2): ML-based collaborative filtering

---

## 4. Mobile Layout

### Complete Mobile Scroll Flow

The dashboard is a **single scrollable page** with clear section dividers:

```
┌─────────────────────────────────────┐
│ 🟣 Spoken Social      🔍  🔔(3) 👤 │  ← STICKY TOP BAR
├─────────────────────────────────────┤
│                                     │
│  👋 Good evening, Priya!            │
│  🔥 15-day streak!                  │  Section 1: Greeting
│  Your longest: 23 days              │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  Level 12 — Practitioner            │
│  ⚡ 2,450 / 3,500 XP        70%    │  Section 2: XP
│  ████████████████░░░░░░             │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  📚 Continue Learning               │
│  🐍 Python - Lesson 7               │  Section 3: CTA
│  "Working with Dictionaries"        │
│  ████████████░░░░░ 70%              │
│  [ ▶ Resume Lesson ]               │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  📅 Weekly Goal: 4/5                │
│  (M)(T)(W)(T)(F)(S)(S)             │  Section 4: Weekly
│  ✅ ✅ ✅ ✅  ◯  ◯  ◯               │
│  1 more to go! 💪                   │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  📚 My Courses           See All >  │
│  ┌──────┐ ┌──────┐ ┌──────┐ →     │  Section 5: Courses
│  │Python│ │Linux │ │Scilab│        │  (horizontal scroll)
│  │ 70%  │ │ 45%  │ │ 10%  │        │
│  └──────┘ └──────┘ └──────┘        │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  🏆 Achievements         See All >  │
│  [🔥 7-day] [📚 5 done] [💬 1st]  │  Section 6: Badges
│  🔒 Next: 30-day streak (15 away)  │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  📊 Activity (Last 90 days)         │
│  ░░▓▓█░░░▓▓█▓░░░▓▓██▓░░           │  Section 7: Heatmap
│  142 tutorials completed            │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  🗓 Upcoming                        │
│  📝 Feb 28 — Python Test (4 days)  │  Section 8: Deadlines
│  🎓 Mar 5  — Linux Workshop        │
│                                     │
├ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┤
│                                     │
│  🎯 Recommended For You             │
│  ┌──────┐ ┌──────┐                 │  Section 9: Recs
│  │Django│ │Pandas│                 │
│  └──────┘ └──────┘                 │
│                                     │
├─────────────────────────────────────┤
│  🏠    📊    ➕     👥     👤      │  ← STICKY BOTTOM NAV
│ Feed  Dash  Post  Groups  Profile  │
└─────────────────────────────────────┘
```

### Spacing & Sizing (Mobile)

| Element | Height (approx) |
|---------|-----------------|
| Top bar | 56px (fixed) |
| Greeting + Streak | 120px |
| XP + Level | 90px |
| Continue Learning | 140px |
| Weekly Goal | 110px |
| My Courses | 200px (with scroll) |
| Achievements | 120px |
| Activity Heatmap | 180px |
| Upcoming | ~150px (varies) |
| Recommended | 180px |
| Bottom nav | 64px (fixed) |
| **Total scroll** | **~1,290px of content** |

---

## 5. Desktop Layout

### Three-Column Layout (> 1024px)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  🟣 Spoken Social        [🔍 Search courses, people...]    🔔(3)  👤   │
├────────────┬──────────────────────────────────────┬──────────────────────┤
│            │                                      │                      │
│   📊 Dash  │  👋 Good evening, Priya!              │  📅 Weekly Goal      │
│   🏠 Feed  │  🔥 15-day streak!                    │  ✅✅✅✅○○○           │
│   👥 Groups│                                      │  4/5 done            │
│   💬 Msgs  │  ┌──────────────┬───────────────────┐│  1 more! 💪          │
│   👤 Profile│ │ Level 12     │ ▶ Continue Python  ││                      │
│   🏆 Board │  │ ⚡ 2,450 XP  │ Lesson 7 - Dicts  ││──────────────────────│
│   🔔 Notif │  │ ████████░░░  │ ████████░░░ 70%   ││                      │
│            │  │              │ [Resume Lesson →]  ││  🗓 Upcoming         │
│            │  └──────────────┴───────────────────┘│  📝 Feb 28 Python    │
│            │                                      │  🎓 Mar 5 Linux      │
│            │  📚 My Courses                       │                      │
│            │  ┌────────┐ ┌────────┐ ┌────────┐   │──────────────────────│
│            │  │ Python │ │ Linux  │ │ Scilab │   │                      │
│            │  │  70%   │ │  45%   │ │  10%   │   │  🏆 Achievements     │
│            │  └────────┘ └────────┘ └────────┘   │  [🔥] [📚] [💬]      │
│            │                                      │  Next: 30-day streak │
│            │  📊 Learning Activity                │                      │
│            │  ░░▓▓█░░░▓▓█▓░░░▓▓██▓░░▓█████░░    │──────────────────────│
│            │  142 tutorials • Last 90 days        │                      │
│            │                                      │  🎯 Recommended      │
│            │                                      │  ┌──────┐ ┌──────┐  │
│            │                                      │  │Django│ │Pandas│  │
│            │                                      │  └──────┘ └──────┘  │
│            │                                      │                      │
└────────────┴──────────────────────────────────────┴──────────────────────┘

Column widths: Nav 240px | Main flex-1 | Sidebar 320px
```

---

## 6. Interactions & Micro-Animations

### Entry Animations (Page Load)

| Element | Animation | Duration |
|---------|-----------|----------|
| Greeting text | Fade in + slide up | 300ms |
| Streak flame | Scale in with bounce | 400ms, 100ms delay |
| XP bar | Fill from 0 to current value | 800ms, ease-out |
| Weekly goal circles | Pop in one by one (left to right) | 50ms each, staggered |
| Course cards | Slide in from right | 300ms, staggered by 100ms |
| Badges | Scale in with slight rotation | 200ms each |
| Heatmap cells | Fade in from left to right (wave) | 1000ms total |

### Interactive Animations

| Trigger | Animation |
|---------|-----------|
| XP gained | XP bar fills, "+25 XP" floats up and fades |
| Streak incremented | Flame grows, particles emit, count bumps up |
| Badge earned | Full-screen confetti burst, badge zooms in from center |
| Level up | Screen flash, level number animates, title slides in |
| Weekly goal met | Ring completes, checkmark appears, celebration particle burst |
| Course completed | Progress bar fills to 100%, card flips to show "COMPLETED ✅" |

### Pull-to-Refresh (Mobile)

- Pull down on dashboard → custom loading animation (Spoken Social logo spinning)
- Refreshes all dashboard data

---

## 7. Data Requirements

### API Call for Dashboard

The dashboard should load with a **single API call** that returns all needed data:

```
GET /api/dashboard

Response:
{
  "user": {
    "name": "Priya Sharma",
    "avatar_url": "...",
    "level": 12,
    "level_title": "Practitioner",
    "xp_total": 2450,
    "xp_for_next_level": 3500,
    "xp_today": 25,
    "xp_this_week": 180
  },
  "streak": {
    "current": 15,
    "longest": 23,
    "is_active_today": true,
    "freeze_available": true,
    "freeze_count": 1
  },
  "weekly_goal": {
    "target": 5,
    "completed": 4,
    "days": [true, true, true, true, false, false, false]
  },
  "continue_learning": {
    "course_id": "...",
    "course_title": "Python",
    "course_icon": "🐍",
    "lesson_title": "Working with Dictionaries",
    "lesson_number": 7,
    "progress_percent": 70,
    "spoken_tutorial_url": "https://spoken-tutorial.org/watch/Python/..."
  },
  "courses": [
    {
      "id": "...",
      "title": "Python",
      "icon": "🐍",
      "progress_percent": 70,
      "tutorials_completed": 7,
      "tutorials_total": 10,
      "status": "in_progress",
      "test_passed": false
    },
    ...
  ],
  "recent_badges": [
    {
      "id": "...",
      "name": "7-day Streak",
      "icon_url": "...",
      "earned_at": "2026-02-20T10:30:00Z"
    },
    ...
  ],
  "upcoming_badges": [
    {
      "id": "...",
      "name": "30-day Streak",
      "progress": "15/30 days",
      "days_away": 15
    },
    ...
  ],
  "activity_heatmap": {
    "data": [
      {"date": "2026-02-24", "count": 3},
      {"date": "2026-02-23", "count": 1},
      ...
    ],
    "total_90_days": 142
  },
  "upcoming_events": [
    {
      "id": "...",
      "type": "test",
      "title": "Python Online Test",
      "date": "2026-02-28T10:00:00Z",
      "location": "Lab 201",
      "days_away": 4
    },
    ...
  ],
  "recommendations": [
    {
      "course_id": "...",
      "title": "Django",
      "icon": "🌐",
      "reason": "Based on your Python progress"
    },
    ...
  ]
}
```

---

## 8. Component Hierarchy

```
<DashboardPage>
├── <TopBar />
├── <ScrollContainer>
│   ├── <GreetingBanner>
│   │   └── <StreakDisplay />
│   ├── <XPLevelCard>
│   │   └── <XPProgressBar />
│   ├── <ContinueLearning>
│   │   └── <ProgressBar />
│   ├── <WeeklyGoalTracker>
│   │   └── <DayCircle /> × 7
│   ├── <MyCourses>
│   │   └── <CourseCard /> × n (horizontal scroll)
│   ├── <AchievementsPreview>
│   │   ├── <BadgeChip /> × 3 (recent)
│   │   └── <LockedBadge /> × 2 (upcoming)
│   ├── <ActivityHeatmap>
│   │   └── <HeatmapCell /> × 91 (13 weeks)
│   ├── <UpcomingDeadlines>
│   │   └── <DeadlineItem /> × n
│   └── <RecommendedCourses>
│       └── <CourseCard /> × 2-3
└── <BottomNav />
```

---

## 9. States & Edge Cases

### 9.1 New User (First Login)

When a student logs in for the first time, the dashboard shows an **onboarding-friendly** state:

```
┌─────────────────────────────────────┐
│                                     │
│  👋 Welcome to Spoken Social,       │
│     Priya!                          │
│                                     │
│  Let's get you started 🚀           │
│                                     │
│  Step 1: Pick your interests        │
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │Python│ │Linux │ │C/C++ │       │
│  │  ☐   │ │  ☐   │ │  ☐   │       │
│  └──────┘ └──────┘ └──────┘       │
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │Scilab│ │R     │ │PHP   │       │
│  │  ☐   │ │  ☐   │ │  ☐   │       │
│  └──────┘ └──────┘ └──────┘       │
│                                     │
│  Step 2: Set a weekly goal          │
│  ○ 3 tutorials/week (Casual)       │
│  ● 5 tutorials/week (Regular)      │
│  ○ 7 tutorials/week (Intense)      │
│                                     │
│  [ 🚀 Start Learning ]             │
│                                     │
└─────────────────────────────────────┘
```

### 9.2 No Active Courses

```
┌─────────────────────────────────────┐
│                                     │
│  📚 You haven't enrolled in any     │
│     courses yet!                    │
│                                     │
│  Popular at your college:           │
│  ┌──────┐ ┌──────┐ ┌──────┐       │
│  │Python│ │Linux │ │Scilab│       │
│  └──────┘ └──────┘ └──────┘       │
│                                     │
│  [ Explore All Courses → ]          │
│                                     │
└─────────────────────────────────────┘
```

### 9.3 All Courses Completed

```
┌─────────────────────────────────────┐
│                                     │
│  🎉 Amazing! You've completed all   │
│     your enrolled courses!          │
│                                     │
│  What's next?                       │
│  • Start a new course               │
│  • Help others in the community     │
│  • Take an online test              │
│                                     │
└─────────────────────────────────────┘
```

### 9.4 Streak Just Broken

```
┌─────────────────────────────────────┐
│                                     │
│  😔 Your 15-day streak ended        │
│     yesterday.                      │
│                                     │
│  Don't worry — start fresh today!   │
│  Complete 1 tutorial to begin a     │
│  new streak.                        │
│                                     │
│  [ 🔥 Start New Streak ]            │
│                                     │
│  💡 Tip: Use a Streak Freeze next   │
│  time to protect your streak!       │
│                                     │
└─────────────────────────────────────┘
```

### 9.5 Loading State

All sections show **skeleton loaders** (pulsing gray shapes matching the layout) while data loads. This prevents layout shift and feels fast.

### 9.6 Error State

If the dashboard API fails:
```
┌─────────────────────────────────────┐
│                                     │
│  😕 Couldn't load your dashboard.   │
│                                     │
│  [ 🔄 Try Again ]                   │
│                                     │
│  If the problem persists, check     │
│  your internet connection.          │
│                                     │
└─────────────────────────────────────┘
```

---

## Next Steps for Dashboard

1. **Generate visual UI mockups** — Realistic designs showing the dashboard with actual styling
2. **Review and refine** — Discuss what to add, remove, or change
3. **Define the component API** — Props and interfaces for each React component
4. **Build design system** — CSS variables, colors, typography, spacing
5. **Implement** — Start coding Phase 1
