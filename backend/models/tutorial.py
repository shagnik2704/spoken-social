from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone
import uuid


class Tutorial(Base):
    __tablename__ = "tutorials"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(String(50), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    tutorial_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text)
    xp_reward = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("Course", back_populates="tutorials")
    user_progress = relationship("UserTutorial", back_populates="tutorial")

    __table_args__ = (
        UniqueConstraint("course_id", "tutorial_number", name="uq_tutorial_course_number"),
        Index("idx_tutorials_course", "course_id"),
    )


class UserTutorial(Base):
    __tablename__ = "user_tutorials"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    tutorial_id = Column(PG_UUID(as_uuid=True), ForeignKey("tutorials.id", ondelete="CASCADE"), primary_key=True)

    status = Column(String(20), nullable=False, default="not_started")
    watched = Column(Boolean, default=False)
    practiced = Column(Boolean, default=False)
    assignment_done = Column(Boolean, default=False)
    forum_asked = Column(Boolean, default=False)
    forum_answered = Column(Boolean, default=False)
    minitask_opted = Column(Boolean, default=False)
    xp_earned = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="tutorials")
    tutorial = relationship("Tutorial", back_populates="user_progress")

    __table_args__ = (
        Index("idx_user_tutorials_user", "user_id"),
        Index("idx_user_tutorials_tutorial", "tutorial_id"),
    )

    def to_api_dict(self):
        return {
            "id": str(self.tutorial_id),
            "number": self.tutorial.tutorial_number if self.tutorial else 0,
            "title": self.tutorial.title if self.tutorial else "",
            "status": self.status,
            "completed": self.status == "completed",
            "watched": self.watched,
            "practiced": self.practiced,
            "assignmentDone": self.assignment_done,
            "forumAsked": self.forum_asked,
            "forumAnswered": self.forum_answered,
            "minitaskOpted": self.minitask_opted,
            "xpEarned": self.xp_earned,
        }
