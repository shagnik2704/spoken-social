from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone


class Badge(Base):
    __tablename__ = "badges"

    id = Column(String(50), primary_key=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    icon = Column(String(255))
    color = Column(String(32))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    badge_id = Column(String(50), ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    earned_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="user_badges")

    def to_api_dict(self):
        return {
            "id": self.badge_id,
            "name": self.badge.name if self.badge else "",
            "description": self.badge.description if self.badge else "",
            "icon": self.badge.icon if self.badge else "",
            "color": self.badge.color if self.badge else "",
            "earnedAt": self.earned_at.isoformat() if self.earned_at else None,
        }
