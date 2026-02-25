from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from data import all_users, feed_data, leaderboard_data, coordinator_colleges, CURRENT_USER_ID

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/api/me')
def get_current_user():
    data = all_users[CURRENT_USER_ID]
    return {
        "user": {
            "id": data["id"],
            "name": data["name"],
            "username": data["username"],
            "initials": data["initials"],
            "bio": data["bio"],
            "level": data["level"],
            "levelTitle": data["levelTitle"],
            "xpTotal": data["xpTotal"],
            "xpForNextLevel": data["xpForNextLevel"],
            "xpToday": data["xpToday"],
            "xpThisWeek": data["xpThisWeek"],
            "joinDate": data["joinDate"],
            "location": data["location"],
            "website": data["website"],
            "followers": data["followers"],
            "following": data["following"],
            "postsCount": data["postsCount"],
            "college": data["college"],
            "department": data["department"],
        },
        "streak": data["streak"],
        "weeklyGoal": data["weeklyGoal"],
        "courses": data["courses"],
        "badges": data["badges"],
    }

@app.get('/api/feed')
def get_feed():
    return feed_data

@app.get('/api/leaderboard')
def get_leaderboard():
    return leaderboard_data

@app.get('/api/users/{user_id}')
def get_user_by_id(user_id:str):
    data = all_users[user_id]
    return {
        "user": {
            "id": data["id"],
            "name": data["name"],
            "username": data["username"],
            "initials": data["initials"],
            "bio": data["bio"],
            "level": data["level"],
            "levelTitle": data["levelTitle"],
            "xpTotal": data["xpTotal"],
            "xpForNextLevel": data["xpForNextLevel"],
            "xpToday": data["xpToday"],
            "xpThisWeek": data["xpThisWeek"],
            "joinDate": data["joinDate"],
            "location": data["location"],
            "website": data["website"],
            "followers": data["followers"],
            "following": data["following"],
            "postsCount": data["postsCount"],
            "college": data["college"],
            "department": data["department"],
        },
        "streak": data["streak"],
        "weeklyGoal": data["weeklyGoal"],
        "courses": data["courses"],
        "badges": data["badges"],
    }


# ===== COORDINATOR ENDPOINTS =====

@app.get('/api/coordinator/colleges')
def get_coordinator_dashboard():
    """Returns all colleges with computed metrics for the coordinator overview"""
    summary = []
    for college in coordinator_colleges:
        students = college["students"]
        total = len(students)
        completed = len([s for s in students if s["status"] == "completed"])
        active = len([s for s in students if s["status"] in ["active", "completed"]])
        inactive = len([s for s in students if s["status"] in ["inactive", "not_started"]])
        at_risk = len([s for s in students if s["status"] == "at_risk"])
        avg_progress = round(sum(s["progress"] for s in students) / total) if total > 0 else 0
        avg_xp = round(sum(s["xp"] for s in students) / total) if total > 0 else 0
        completion_rate = round((completed / total) * 100) if total > 0 else 0

        summary.append({
            "id": college["id"],
            "name": college["name"],
            "location": college["location"],
            "coordinatorName": college["coordinatorName"],
            "course": college["course"],
            "totalStudents": total,
            "activeStudents": active,
            "inactiveStudents": inactive,
            "atRiskStudents": at_risk,
            "completedStudents": completed,
            "avgProgress": avg_progress,
            "avgXP": avg_xp,
            "completionRate": completion_rate,
        })
    return summary


@app.get('/api/coordinator/colleges/{college_id}')
def get_college_details(college_id: str):
    """Returns a specific college's students and detailed metrics"""
    college = next((c for c in coordinator_colleges if c["id"] == college_id), None)
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    students = college["students"]
    total = len(students)
    completed = len([s for s in students if s["status"] == "completed"])
    active = len([s for s in students if s["status"] in ["active", "completed"]])

    return {
        "college": {
            "id": college["id"],
            "name": college["name"],
            "location": college["location"],
            "coordinatorName": college["coordinatorName"],
            "course": college["course"],
        },
        "metrics": {
            "totalStudents": total,
            "activeStudents": active,
            "completedStudents": completed,
            "avgProgress": round(sum(s["progress"] for s in students) / total) if total > 0 else 0,
            "avgXP": round(sum(s["xp"] for s in students) / total) if total > 0 else 0,
            "completionRate": round((completed / total) * 100) if total > 0 else 0,
        },
        "students": students,
    }
