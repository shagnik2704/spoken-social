# ============================================================
# TutorialFeedback — stores reasons why a student said "No"
# ============================================================

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import relationship
from database import Base


class TutorialFeedback(Base):
    __tablename__ = "tutorial_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tutorial_id = Column(PG_UUID(as_uuid=True), ForeignKey("tutorials.id"), nullable=False)
    step_type = Column(String(30), nullable=False)  # watched | practiced | assignmentDone | forumAsked | forumAnswered
    reasons = Column(ARRAY(String), nullable=False, default=[])  # list of reason keys
    other_text = Column(Text, nullable=True)  # free-text if "other" is selected
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User")
    tutorial = relationship("Tutorial")

    __table_args__ = (
        Index("idx_tutorial_feedback_user", "user_id"),
        Index("idx_tutorial_feedback_tutorial", "tutorial_id"),
    )

    def to_api_dict(self):
        return {
            "id": self.id,
            "userId": str(self.user_id),
            "tutorialId": str(self.tutorial_id),
            "stepType": self.step_type,
            "reasons": self.reasons or [],
            "otherText": self.other_text,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
