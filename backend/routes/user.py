from fastapi import APIRouter
from data import all_users,CURRENT_USER_ID

router = APIRouter(prefix='/api',tags=['users'])

@router.get('/me')
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


        "weeklyGoal": data["weeklyGoal"],
        "courses": data["courses"],
        "badges": data["badges"],
    }

@router.get('/api/users/{user_id}')
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


        "weeklyGoal": data["weeklyGoal"],
        "courses": data["courses"],
        "badges": data["badges"],
    }
