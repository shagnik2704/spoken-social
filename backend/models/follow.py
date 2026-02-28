from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone


class Follow(Base):
    __tablename__ = "follows"

    follower_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    follower_user = relationship("User", foreign_keys=[follower_id], back_populates="following_rel")
    following_user = relationship("User", foreign_keys=[following_id], back_populates="followers_rel")

    __table_args__ = (
        Index("idx_follows_following", "following_id"),
        Index("idx_follows_follower", "follower_id"),
    )
