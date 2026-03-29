# ============================================================
# ForumActivity — tracks individual forum posts synced from
# the Spoken Tutorial Forum via webhooks or background sync.
# ============================================================
# Each row = one question or answer by a student on the forum.
# The forum_post_id (unique) is the dedup key that makes
# sync idempotent — safe to process the same event twice.
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone


class ForumActivity(Base):
    __tablename__ = "forum_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    tutorial_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("tutorials.id", ondelete="CASCADE"),
        nullable=True,  # nullable in case we can't match to a tutorial
    )

    # From the forum webhook / API
    forum_post_id = Column(Integer, nullable=False)  # the question/answer ID on the forum
    activity_type = Column(String(10), nullable=False)  # "question" or "answer"
    title = Column(String(500))  # question title (answers may not have one)
    category = Column(String(200))  # e.g., "Linux New"
    tutorial_name = Column(String(255))  # e.g., "Basic Commands in Linux"
    forum_url = Column(String(500))  # link back to the forum post

    # Timestamps
    posted_at = Column(DateTime(timezone=True))  # when the student posted on the forum
    synced_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # XP tracking
    xp_awarded = Column(Boolean, default=False)
    xp_amount = Column(Integer, default=0)

    # Deletion tracking
    deleted_on_forum = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
    tutorial = relationship("Tutorial")

    __table_args__ = (
        UniqueConstraint("forum_post_id", "activity_type", name="uq_forum_post"),
        Index("idx_forum_activity_user", "user_id"),
        Index("idx_forum_activity_tutorial", "tutorial_id"),
        Index("idx_forum_activity_post_id", "forum_post_id"),
    )
