# ============================================================
# Feedback Routes — stores "why not?" responses from students
# ============================================================

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models import User
from models.feedback import TutorialFeedback

router = APIRouter(prefix="/api/me", tags=["feedback"])


# ----- Request Model -----

class FeedbackRequest(BaseModel):
    tutorialId: str
    stepType: str           # watched | practiced | assignmentDone | forumAsked | forumAnswered
    reasons: list[str]      # list of reason keys
    otherText: Optional[str] = None


# ----- Endpoint -----

@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save feedback for why a student selected 'No' on a tutorial step."""
    import uuid

    feedback = TutorialFeedback(
        user_id=user.id,
        tutorial_id=uuid.UUID(body.tutorialId),
        step_type=body.stepType,
        reasons=body.reasons,
        other_text=body.otherText,
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)

    return feedback.to_api_dict()
