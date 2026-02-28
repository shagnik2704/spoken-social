from sqlalchemy import Column, String, Integer, Date, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base


class LeaderboardWeekly(Base):
    __tablename__ = "leaderboard_weekly"

    week_start = Column(Date, primary_key=True)
    course_id = Column(String(50), primary_key=True, default="__all__")
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    xp_week = Column(Integer, nullable=False)
    rank = Column(Integer)

    __table_args__ = (
        Index("idx_leaderboard_week_start_course", "week_start", "course_id", "rank"),
    )
