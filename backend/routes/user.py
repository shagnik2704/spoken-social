from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from data import all_users, user_tutorials
from dependencies import get_current_user

router = APIRouter(prefix='/api', tags=['users'])


# ===== PROTECTED: requires JWT token =====

@router.get('/me')
def get_current_user_profile(user: dict = Depends(get_current_user)):
    """
    Returns the logged-in user's full profile.
    'user' is automatically resolved from the JWT token by get_current_user.
    """
    return {
        "user": {
            "id": user["id"],
            "name": user["name"],
            "username": user["username"],
            "initials": user["initials"],
            "bio": user["bio"],
            "level": user["level"],
            "levelTitle": user["levelTitle"],
            "xpTotal": user["xpTotal"],
            "xpForNextLevel": user["xpForNextLevel"],
            "xpToday": user["xpToday"],
            "xpThisWeek": user["xpThisWeek"],
            "joinDate": user["joinDate"],
            "location": user["location"],
            "website": user["website"],
            "followers": user["followers"],
            "following": user["following"],
            "postsCount": user["postsCount"],
            "college": user["college"],
            "department": user["department"],
        },
        "weeklyGoal": user["weeklyGoal"],
        "courses": user["courses"],
        "badges": user["badges"],
    }


# ===== PUBLIC: no auth needed =====

@router.get('/users/{user_id}')
def get_user_by_id(user_id: str):
    data = all_users.get(user_id)
    if not data:
        raise HTTPException(status_code=404, detail="User not found")
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


# ===== TUTORIAL ENDPOINTS (protected) =====

@router.get('/me/courses/{course_id}/tutorials')
def get_my_tutorials(course_id: str, user: dict = Depends(get_current_user)):
    key = f"{user['id']}:{course_id}"
    tutorials = user_tutorials.get(key)
    if tutorials is None:
        raise HTTPException(status_code=404, detail="No tutorial data found")
    return tutorials


@router.put('/me/courses/{course_id}/tutorials/{tutorial_id}')
def update_tutorial(course_id: str, tutorial_id: str, body: TutorialUpdate, user: dict = Depends(get_current_user)):
    key = f"{user['id']}:{course_id}"
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


# ===== XP ENDPOINT (protected) =====

@router.post('/me/xp')
def add_xp(body: XPUpdate, user: dict = Depends(get_current_user)):
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
