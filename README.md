# Spoken Social — Gamified Learning & Community Platform

Spoken Social is a robust, gamified learning management system (LMS) intertwined with social network mechanics. It provides structured courses (e.g., Linux, C++), real-time experience points (XP) tracking, leaderboards, a social feed, and incredibly detailed administrative dashboards.

The backend is built for performance and scale using **FastAPI** and **PostgreSQL**, leaning heavily on **SQLAlchemy ORM**, **Server-Sent Events (SSE)**, and advanced **SQL aggregations** to compute deep analytics in real-time.

---

## 🛠 Tech Stack

### Backend Core
- **Framework:** FastAPI (Python 3) for high-performance, async REST APIs.
- **Server:** Uvicorn (ASGI web server).
- **Database:** PostgreSQL (Relational Data).
- **ORM:** SQLAlchemy 2.0 (Declarative Base, complex query building).
- **Migrations:** Alembic.
- **Real-Time:** Server-Sent Events (SSE) via FastAPI StreamingResponse.
- **Background Jobs:** APScheduler (AsyncIOScheduler) with CronTriggers.
- **Authentication:** JWT (JSON Web Tokens) with Python-JOSE & Passlib.

### Frontend
- **Framework:** React / Vite with TypeScript.
- **State Management:** Zustand.
- **Styling:** Tailwind CSS + Radix UI (shadcn/ui).
- **Charts:** Recharts.

---

## 🏗 Backend Architecture & In-Depth Features

The Spoken Social backend is segmented into specialized modules (routers) with a focus on strict Role-Based Access Control (RBAC) and performance. Here's a deep dive into every backend feature and how it works under the hood.

### 1. Authentication & Security (`routes/auth.py`, `dependencies.py`)
The system uses stateless JWT authentication.
- **How it works:** When a user logs in, the backend verifies their credentials against highly secure hashed passwords in PostgreSQL. It generates an access token encoded with the user's UUID. 
- **RBAC (Role-Based Access Control):** 
  - Every API request passes through Dependency Injection (`Depends(get_current_user)`).
  - Specialized dependencies enforce role limits. `require_coordinator` blocks anyone except `"coordinator"` or `"admin"` from accessing college data. `require_admin` restricts analytics endpoints strictly to the `"admin"` role.

### 2. Gamified Learning System: XP & Leveling (`routes/user.py`)
The core loop of Spoken Social is watching tutorials, practicing, and asking questions, all of which reward XP to the user.
- **Tutorial Tracking (`UserTutorial`):** A many-to-many relationship tracking a user's progress through a course. It logs boolean states: `watched`, `practiced`, `assignment_done`, etc.
- **Dynamic XP Recalculation:** When a tutorial component is completed (e.g., a PUT request marking `practiced=True`), the backend re-calculates the XP earned solely for that tutorial based on an `XP_MAP`. 
- **Auto-Leveling:** It computes the `xp_gained` differential, updates the user's `xp_total`, and runs an IF/ELSE cascade to determine if the user has reached a new Level boundary (e.g., 500 XP = "Explorer", 12000 XP = "Spoken Legend").
- **Audit Logging (`XPEvent`):** Every single point of XP awarded is logged as an atomic `XPEvent` row. This allows for historic graphs of XP over time.

### 3. Real-Time Synchronization via SSE (`routes/sse.py`, `sse.py`)
To make the gamification feel alive, the backend uses Server-Sent Events to push data down to clients instantly, without holding WebSocket connections.
- **How it works:** When a user's XP changes (via tutorial completion or manual XP grant), the backend triggers `sse_manager.broadcast_sync(...)`.
- **The SSE Route:** The `/api/events` endpoint returns a `StreamingResponse` powered by an async generator. 
- **Queueing Engine:** `sse_manager` maintains a thread-safe registry of connected clients. If there are no messages, the generator yields a `: keepalive\n\n` heartbeat every 15 seconds to prevent the browser or proxy (like Nginx) from dropping the idle HTTP connection.

### 4. High-Performance Social Feed (`routes/feed.py`)
The feed merges traditional LMS with a social network.
- **The N+1 Problem:** Loading a timeline of posts, along with their authors, their likes, their comments, and hashtags could trigger hundreds of SQL queries (The N+1 Query Problem).
- **The Solution:** The backend utilizes SQLAlchemy's `joinedload()`. In a single, massive SQL query, the `feed` route fetches the latest 50 posts and eager-loads the `author`, `likes`, `comments`, `shares`, and `post_hashtags`. 
- **Deduplication:** Because `joinedload` on multiple one-to-many relationships causes SQL Cartesian plane row duplication, the backend gracefully iterates and deduplicates the result set in Python before returning it.

### 5. Advanced SQL Aggregations: Coordinator Dashboard (`routes/coordinator.py`)
Coordinators need to see the "health" of their college. Calculating this in Python by loading thousands of students into RAM would crash the server.
- **How it works:** The calculation is pushed entirely down to PostgreSQL.
- **Conditional Counts:** Using SQLAlchemy's `case()` and `func.count()`, the query dynamically counts how many tutorials a user has completed vs. how many exist in absolute total.
- **Status Computation:** The database returns individual student metrics (`watched`, `completed`). The backend then clusters them into cohorts:
  - `completed`: Finished all tutorials.
  - `active`: Watched > 30% of materials.
  - `at_risk`: Watched a few, but no recent completion.
  - `inactive`: Registered but 0 progress.
- **Pagination:** The route handles server-side pagination, searching, and sorting with O(1) memory overhead, regardless of the college's size.

### 6. Admin Analytics & Feedback Drilldowns (`routes/admin.py`)
Admins receive rich telemetry on *why* students are struggling.
- **How it works:** When students complete a course, they can leave feedback (via `TutorialFeedback`). The admin route groups this feedback.
- **Dictionary Aggregation:** It loops through all database feedbacks, utilizing Python dictionaries to compile a frequency map of `reason_counts` and `step_type_counts` (e.g., "Audio Issue", "Too Fast").
- **Drilldown Views:** It returns sorted arrays of top reasons, and deeply nested JSON structures clustering feedback per tutorial and per student, allowing the frontend admin panel to render pie charts and bar charts instantly.

### 7. Background Task Scheduler (`scheduler.py`)
Some computations (like calculating weekly leaderboard deltas) shouldn't happen during a web request.
- **How it works:** `APScheduler` is configured with a `CronTrigger` running natively inside the async event loop of FastAPI.
- **Execution:** Every Monday at 00:05 IST, it connects to the DB via `SessionLocal`, and executes a raw SQL Stored Procedure (`SELECT compute_leaderboard_weekly()`). This resets weekly XP variables for all players on the platform simultaneously without locking the main API threads.

---

## 🗄️ Database Models (`models/`)

The PostgreSQL schema is fully typed and connected via Foreign Keys.
- **`User`**: Tracks `xp_total`, `level`, roles (`student`, `coordinator`, `admin`).
- **`College`**: Binds users together. Links to a Coordinator.
- **`Tutorial` / `Course`**: Static catalog of the LMS content.
- **`UserTutorial`**: State machine mapping a User to a Tutorial.
- **`Post` / `Comment` / `Interaction`**: Social graph data. Polymorphic interactions handle likes and shares.
- **`Follow`**: Self-referential Many-to-Many mapping for the user follow system.
- **`XPEvent`**: Time-series log of all points gained.

---

## 🚀 Running the Project Locally

### Prerequisites
- Python 3.10+
- Node.js v18+
- PostgreSQL server

### 1. Database Setup
Ensure PostgreSQL is running. Create a database named `spoken_social`.
Provide your connection string in backend `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost/spoken_social
JWT_SECRET=your_super_secret_key
```

### 2. Start Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations (creates tables)
alembic upgrade head

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*API documentation automatically generates at: `http://localhost:8000/docs`*

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
*App is available at: `http://localhost:5173`*

---

## 🧠 Design Philosophy & Best Practices
1. **Fat Database, Thin Application:** Heavy analytics and leaderboard rankings are pushed to PostgreSQL using raw SQL procedures and SQLAlchemy `func` methods to drastically lower API memory usage.
2. **Context Managers for Safety:** `Yields` in FastAPI dependencies guarantee that database connections are always closed and returned to the pool, preventing connection leaks.
3. **Event-Driven UI:** Using SSE instead of Websockets handles one-way data flow (Server-to-Client) much more efficiently with lower overhead, perfect for Gamification pop-ups.
