from fastapi import APIRouter,HTTPException
from data import COORDINATOR_COLLEGE_ID,coordinator_colleges

router = APIRouter(prefix='/api/coordinator',tags=['coordinator'])

@router.get('/colleges')
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


@router.get('/colleges/{college_id}')
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
