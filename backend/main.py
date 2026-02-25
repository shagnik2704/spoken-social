from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from data import all_users, feed_data, leaderboard_data, CURRENT_USER_ID

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



