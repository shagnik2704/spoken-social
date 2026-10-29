# 🎓 Spoken Social — Product & Application Brief

> **Audience:** Students, Faculty Coordinators, College Leadership, and Educational Decision-Makers  
> **Ecosystem:** [Spoken Tutorial](https://spoken-tutorial.org), IIT Bombay  
> **Status:** Active in Production (5,400+ students across 170+ colleges nationwide)  
> **Formats Available:** [Word Document (.docx)](Spoken_Social_Product_Brief.docx) | [PDF Document (.pdf)](Spoken_Social_Product_Brief.pdf)

---

## 1. Executive Summary & Why Spoken Social Exists

**Spoken Tutorial** (an initiative of IIT Bombay funded by the Ministry of Education, Govt. of India) has brought high-quality software education to millions of students across India through self-paced audio-video screencasts in regional languages (covering Python, Linux, C/C++, Scilab, Blender, LibreOffice, and more).

However, self-paced distance learning faces a universal problem: **"Silent Drop-Off"**.
* When students hit an obstacle—such as software installation errors, compiler bugs, or lack of computer access—they lose momentum in isolation and stop practicing.
* Because traditional systems only record initial enrollment and final exam certificates, teachers and coordinators have zero visibility into who is struggling until months later when the semester is over.

**Spoken Social** bridges this gap as **"Duolingo meets LinkedIn meets a Collaborative Learning Community"**. It turns solitary video watching into an active, habit-forming journey with micro-progress checklists, experience points (XP), levels, friendly college leaderboards, real-time teacher dashboards, and peer support.

---

## 2. Who the Platform Serves

| User Persona | Core Needs & Pain Points | Spoken Social Solution |
|---|---|---|
| **The Student**<br>*(e.g., Priya, 2nd-Year B.Tech)* | Needs daily motivation, clear learning targets, friendly peer competition, instant doubt help, and a portfolio to prove software skills to recruiters. | Gamified dashboard, step-by-step progress checklists, XP and levels, campus leaderboards, and forum rewards. |
| **The Faculty Coordinator**<br>*(e.g., Prof. Sharma, College SPOC)* | Manages 200+ students across departments; needs to know who is actively practicing and who needs help before exams. | Live institution radar, individual student drill-downs, friction analysis (installation bugs), and 1-click Excel compliance reports. |
| **The Programme Admin**<br>*(IIT Bombay / EduPyramids)* | Needs high-level oversight across dozens of universities, multiple concurrent training batches, and national course completion trends. | Platform-wide analytics, cross-institutional benchmarks, and seamless single sign-on integration. |

---

## 3. Core Features Live Today

### A. For Students: The Gamified Learning Journey
* **Interactive Step-by-Step Tracker:** Breaks each course into bite-sized actions: *Watched the video*, *Practiced hands-on*, *Finished the assignment*, and *Attempted the mini-challenge*. Progressive unlocking ensures students do not skip crucial practice.
* **Transparent Points (XP) & Levels:** Earn points for genuine learning steps:
  * 🎬 Watching a tutorial: **+10 Points**
  * 💻 Hands-on software practice: **+10 Points**
  * 📝 Submitting an assignment: **+5 Points**
  * ❓ Asking a doubt on the forum: **+5 Points**
  * 💡 Answering a peer's doubt on the forum: **+10 Points**  
  Learners advance through 6 tiers (from *Level 1: Beginner* to *Level 26+: Spoken Legend*).
* **Dynamic Multi-Scope Leaderboards:** Friendly rankings across three levels: **Your College** (healthy campus camaraderie), **Your Course** (topic-level competition), and **National** (countrywide recognition) across Weekly, Monthly, and All-Time windows, with top-3 podium highlights.
* **Smart Roadblock Detection:** When a student indicates "No" on practicing or an assignment, a non-intrusive prompt captures the exact roadblock (*Software wouldn't install*, *Command error / bug*, *No computer / lab access*, *Concept too difficult*, *Shortage of time*). This turns a failure point into a teacher support alert.
* **Learner Profile:** Displays earned XP, level milestones, completed courses, and learning achievements.

### B. For Faculty Coordinators: Real-Time Command Center
* **Live Cohort Radar:** Instantly categorizes enrolled students into four clear cohorts:
  * 🟢 **Completed:** 100% finished all course lessons and assignments.
  * 🔵 **Active:** Steady progress within recent days.
  * 🟡 **At-Risk:** Slowing down or falling behind schedule.
  * 🔴 **Stalled:** Inactive with zero progress recorded.
* **Individual Student Drill-Down:** Coordinators can click on any student to view their exact timeline and identify precisely which lesson or command stopped them.
* **Friction Analysis Heatmaps:** Aggregates student feedback to highlight class-wide roadblocks (e.g., 40% of the class cannot install Linux dependencies), allowing faculty to schedule targeted lab sessions.
* **One-Click Institutional Compliance Reports:** Download fully formatted progress sheets for department meetings, accreditation bodies (NAAC/NBA), and Semester Training Planner (STP) audits in one click.

### C. Seamless Ecosystem Integration
* **Single Sign-On (SSO):** Students log in using their existing Spoken Tutorial credentials. No new passwords, accounts, or friction.
* **Discussion Forum Sync:** Tied directly into the Spoken Tutorial forums to encourage peer support with built-in anti-spam verification.

---

## 4. Learning Activities Hosted on the Platform

| Learning Activity | Educational Objective | Platform Mechanism |
|---|---|---|
| **1. Video Screencast Learning** | Conceptual Comprehension | Students watch self-paced video lessons with voice narration in regional languages or English across programming, Linux, Scilab, and CAD tools. Earns **+10 XP**. |
| **2. Guided Lab Practice** | Hands-on Application | The heart of Spoken Tutorial: side-by-side software execution where students replicate commands and code on their own PC or college lab. Earns **+10 XP**. |
| **3. Formative Assignments** | Knowledge Application | Problem-solving tasks at the end of each tutorial (e.g., writing a script, configuring file permissions, generating computational graphs). Earns **+5 XP**. |
| **4. Practical Mini-Tasks** | Advanced Challenges | Optional creative challenge tasks for students who want to explore beyond basic curriculum requirements. |
| **5. Peer Q&A & Mentorship** | Collaborative Learning | Asking technical doubts (**+5 XP**) and answering classmates (**+10 XP**) on Spoken Tutorial forums. Reinforces knowledge through teaching. |
| **6. Diagnostic Roadblock Logs** | Reflective Feedback | Students self-report hurdles when stuck, turning moments of friction into actionable support tickets for faculty. |
| **7. Structured Cohort Workshops** | Institutional Training | Time-bound batches (e.g., *"Semester 3 Python Workshop"* or *"Faculty FDP on Scilab"*) with organized schedules, deadlines, and mentor oversight. |
| **8. Certification Exam Prep** | Summative Assessment | Readiness milestones and practice checks leading into official proctored Spoken Tutorial online certification exams. |

---

## 5. What More Can Be Added (Future Roadmap & Expansion)

Spoken Social is designed to expand seamlessly. The following high-impact features represent key opportunities for future growth:

### A. Ready in the Codebase (Immediate Activation)
* **Campus Social Feed:** A clean community wall where students can share mini-projects, code snippets, study resources, and celebrate learning wins with likes and comments.

### B. Gamification & Habit-Building Enhancements
* **Learning Streaks & Daily Habits:** Duolingo-style daily study streaks (*"🔥 15-day streak!"*) with *"Streak Freezes"* to keep students returning daily and build enduring learning habits.
* **Achievement Badges:** Collectible visual achievement badges for key milestones (e.g., *"First Script Executed"*, *"Weekend Warrior"*, *"Helpful Mentor"*, *"Top 5 Campus Performer"*).

### C. Career & Portfolio Features (LinkedIn-Inspired)
* **Digital Learning Resume:** Public, shareable student profile showcasing completed courses, verified certificates, code repositories, and faculty endorsements—acting as a modern tech resume.
* **Direct Job & Internship Pathways:** Connecting high-scoring students directly with internship and junior developer openings via Spoken Tutorial's Job Recommendation System (JRS).

### D. AI-Assisted Learning & Smart Support
* **AI Learning Companion:** A 24/7 in-app tutor to help students troubleshoot local software installation errors, explain compiler bug outputs, and answer concept queries in their mother tongue.
* **Automated Dropout Early Warning:** Predictive analytics alerting coordinators automatically when a student shows drop-off patterns, suggesting timely interventions.

### E. Collaborative & Mobile Learning
* **Mobile Companion App:** Lightweight mobile app with push notifications for batch deadlines, streak reminders, and weekly leaderboard podium alerts.
* **Cross-College Study Circles:** Virtual study circles allowing students from different colleges enrolled in the same course to collaborate and peer-review code.
