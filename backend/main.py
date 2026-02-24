from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

user_data = {
    "user": {
        "id": "user-priya",
        "name": "Priya Singh",
        "username": "@priya_learns",
        "initials": "PS",
        "bio": "Computer Science student passionate about open-source and Python. Learning one tutorial at a time 🚀",
        "level": 12,
        "levelTitle": "Practitioner",
        "xpTotal": 2450,
        "xpForNextLevel": 3500,
        "xpToday": 25,
        "xpThisWeek": 180,
        "joinDate": "August 2025",
        "location": "Mumbai, India",
        "website": "github.com/priyasingh",
        "followers": 42,
        "following": 78,
        "postsCount": 15,
        "college": "VJTI Mumbai",
        "department": "B.Tech CSE, Year 2",
    },
    "streak": {
        "current": 15,
        "longest": 23,
        "isActiveToday": True,
    },
    "weeklyGoal": {
        "target": 5,
        "completed": 4,
        "days": [True, True, True, True, False, False, False],
        "dayLabels": ["M", "T", "W", "T", "F", "S", "S"],
    },
    "courses": [
        {"id": "1", "title": "Python", "progress": 70, "completed": 7, "total": 10, "status": "in_progress", "testPassed": False},
        {"id": "2", "title": "Linux", "progress": 45, "completed": 5, "total": 11, "status": "in_progress", "testPassed": False},
        {"id": "3", "title": "Scilab", "progress": 10, "completed": 1, "total": 10, "status": "in_progress", "testPassed": False},
        {"id": "4", "title": "C/C++", "progress": 100, "completed": 8, "total": 8, "status": "completed", "testPassed": True, "testScore": 85, "completedDate": "Feb 5, 2026"},
        {"id": "5", "title": "LibreOffice", "progress": 0, "completed": 0, "total": 12, "status": "not_started", "testPassed": False},
    ],
    "badges": [
        {"id": "1", "name": "7-Day Streak", "description": "Maintained a 7-day learning streak", "icon": "flame", "color": "text-warning", "bgColor": "bg-warning/10", "earned": True, "earnedDate": "Feb 22"},
        {"id": "2", "name": "5 Courses", "description": "Enrolled in 5 different courses", "icon": "book-open", "color": "text-primary", "bgColor": "bg-primary/10", "earned": True, "earnedDate": "Feb 17"},
        {"id": "3", "name": "First Post", "description": "Shared your first post with the community", "icon": "message-circle", "color": "text-secondary", "bgColor": "bg-secondary/10", "earned": True, "earnedDate": "Feb 10"},
        {"id": "4", "name": "Test Passer", "description": "Passed your first online test", "icon": "check-circle", "color": "text-success", "bgColor": "bg-success/10", "earned": True, "earnedDate": "Feb 5"},
        {"id": "5", "name": "Helpful", "description": "Received 10 likes on your answers", "icon": "heart", "color": "text-danger", "bgColor": "bg-danger/10", "earned": True, "earnedDate": "Jan 28"},
        {"id": "6", "name": "30-Day Streak", "description": "Maintain a 30-day learning streak", "icon": "flame", "color": "text-warning", "bgColor": "bg-warning/10", "earned": False, "progress": "15/30 days", "daysAway": 15},
        {"id": "7", "name": "Python Master", "description": "Complete all Python tutorials", "icon": "code", "color": "text-primary", "bgColor": "bg-primary/10", "earned": False, "progress": "7/10 tutorials", "daysAway": None},
        {"id": "8", "name": "Mentor", "description": "Help 20 learners with their questions", "icon": "users", "color": "text-secondary", "bgColor": "bg-secondary/10", "earned": False},
        {"id": "9", "name": "Top Contributor", "description": "Be in the top 10 weekly leaderboard", "icon": "trophy", "color": "text-xp-gold", "bgColor": "bg-xp-gold/10", "earned": False},
    ],
}

feed_data = [
    {
        "id": "1",
        "author": {"id": "user-rahul", "name": "Rahul Sharma", "initials": "RS", "level": 15, "title": "Python Pro"},
        "type": "achievement",
        "content": "Just completed the entire Python course with a perfect score on the online test! 🎉",
        "details": "Python — 10/10 tutorials completed • Online Test: 92%",
        "courseName": "Python",
        "timestamp": "2h ago",
        "createdAt": 1740400000000,
        "likes": 24, "comments": 8, "shares": 3,
        "isLiked": False, "isBookmarked": False,
        "tags": ["Python", "Achievement"],
    },
    {
        "id": "2",
        "author": {"id": "user-ananya", "name": "Ananya Patel", "initials": "AP", "level": 8, "title": "Learner"},
        "type": "question",
        "content": "Can someone explain the difference between lists and tuples in Python? I keep mixing them up in my tutorials.",
        "details": "I understand lists are mutable but when should I actually prefer tuples over lists in practice?",
        "courseName": "Python",
        "timestamp": "4h ago",
        "createdAt": 1740393000000,
        "likes": 12, "comments": 15, "shares": 1,
        "isLiked": True, "isBookmarked": True,
        "tags": ["Python", "Question", "Data Structures"],
    },
    {
        "id": "3",
        "author": {"id": "user-vikram", "name": "Vikram Desai", "initials": "VD", "level": 22, "title": "Mentor"},
        "type": "discussion",
        "content": "Pro tip for everyone learning Linux: Start by mastering these 10 commands and you'll be able to handle 80% of daily tasks.\n\n1. cd, ls, pwd\n2. grep, find\n3. chmod, chown\n4. cat, head, tail\n5. pipe (|) and redirect (>)",
        "timestamp": "6h ago",
        "createdAt": 1740386000000,
        "likes": 67, "comments": 23, "shares": 18,
        "isLiked": False, "isBookmarked": False,
        "tags": ["Linux", "Tips", "Beginner"],
    },
    {
        "id": "4",
        "author": {"id": "user-meera", "name": "Meera Joshi", "initials": "MJ", "level": 10, "title": "Practitioner"},
        "type": "milestone",
        "content": "Hit a 30-day learning streak! Consistency is the key. 🔥",
        "details": "30 days of continuous learning without missing a single day",
        "timestamp": "8h ago",
        "createdAt": 1740379000000,
        "likes": 89, "comments": 31, "shares": 7,
        "isLiked": True, "isBookmarked": False,
        "tags": ["Streak", "Milestone"],
    },
    {
        "id": "5",
        "author": {"id": "user-arjun", "name": "Arjun Nair", "initials": "AN", "level": 6, "title": "Explorer"},
        "type": "question",
        "content": "I'm stuck on Scilab Tutorial 5 — the matrix operations part. Has anyone found a good way to visualize what's happening with matrix multiplication?",
        "courseName": "Scilab",
        "timestamp": "12h ago",
        "createdAt": 1740372000000,
        "likes": 5, "comments": 9, "shares": 0,
        "isLiked": False, "isBookmarked": False,
        "tags": ["Scilab", "Help Needed"],
    },
    {
        "id": "6",
        "author": {"id": "user-priya", "name": "Priya Singh", "initials": "PS", "level": 12, "title": "Practitioner"},
        "type": "achievement",
        "content": "Passed my C/C++ online test! That pointer chapter was brutal but I made it through 💪",
        "details": "C/C++ — Online Test: 85% • All tutorials completed",
        "courseName": "C/C++",
        "timestamp": "1d ago",
        "createdAt": 1740330000000,
        "likes": 34, "comments": 12, "shares": 5,
        "isLiked": False, "isBookmarked": False,
        "tags": ["C/C++", "Online Test"],
    },
]

@app.get("/api/me")
def get_current_user():
    return user_data

@app.get("/api/feed")
def get_current_feed():
    return feed_data
