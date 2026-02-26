from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from data import all_users, CURRENT_USER_ID, user_tutorials

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

@router.get('/users/{user_id}')
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


# ===== REQUEST MODELS =====

class TutorialUpdate(BaseModel):
    field: str
    value: Optional[str] = None

class XPUpdate(BaseModel):
    amount: int
    source: str


# ===== TUTORIAL ENDPOINTS =====

@router.get('/me/courses/{course_id}/tutorials')
def get_my_tutorials(course_id: str):
    key = f"{CURRENT_USER_ID}:{course_id}"
    tutorials = user_tutorials.get(key)
    if tutorials is None:
        raise HTTPException(status_code=404, detail="No tutorial data found")
    return tutorials


@router.put('/me/courses/{course_id}/tutorials/{tutorial_id}')
def update_tutorial(course_id: str, tutorial_id: str, body: TutorialUpdate):
    key = f"{CURRENT_USER_ID}:{course_id}"
    tutorials = user_tutorials.get(key)
    if tutorials is None:
        raise HTTPException(status_code=404, detail="No tutorial data found")

    tutorial = next((t for t in tutorials if t["id"] == tutorial_id), None)
    if not tutorial:
        raise HTTPException(status_code=404, detail="Tutorial not found")

    valid_fields = ["watched", "practiced", "assignmentDone", "forumAsked", "forumAnswered"]
    if body.field not in valid_fields:
        raise HTTPException(status_code=400, detail="Invalid field")

    tutorial[body.field] = body.value

    if body.field == "practiced" and body.value == "yes":
        tutorial["completed"] = True

    XP_MAP = {"watched": 10, "practiced": 10, "assignmentDone": 5, "forumAsked": 5, "forumAnswered": 5}
    tutorial["xpEarned"] = sum(XP_MAP[f] for f in valid_fields if tutorial.get(f) == "yes")

    return tutorial


# ===== XP ENDPOINT =====

@router.post('/me/xp')
def add_xp(body: XPUpdate):
    user = all_users[CURRENT_USER_ID]
    user["xpTotal"] += body.amount
    user["xpToday"] += body.amount
    user["xpThisWeek"] += body.amount

    xp = user["xpTotal"]
    if xp >= 12000:   user["level"], user["levelTitle"] = 26, "Spoken Legend"
    elif xp >= 7000:  user["level"], user["levelTitle"] = 21, "Master"
    elif xp >= 3500:  user["level"], user["levelTitle"] = 16, "Expert"
    elif xp >= 1500:  user["level"], user["levelTitle"] = 11, "Practitioner"
    elif xp >= 500:   user["level"], user["levelTitle"] = 6, "Explorer"
    else:             user["level"], user["levelTitle"] = 1, "Beginner"

    return {"xpTotal": user["xpTotal"], "level": user["level"], "levelTitle": user["levelTitle"]}
