from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone


class XPEvent(Base):
    __tablename__ = "xp_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    source_type = Column(String(50))
    source_id = Column(String(100))
    xp_delta = Column(Integer, nullable=False)
    # Which course this XP was earned in, so the daily-XP chart can be course-scoped like
    # every other metric. Nullable: historical events pre-date this and can't be attributed.
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="xp_events")

    __table_args__ = (
        Index("idx_xp_events_user_created", "user_id", created_at.desc()),
        Index("idx_xp_events_course", "course_id"),
    )
