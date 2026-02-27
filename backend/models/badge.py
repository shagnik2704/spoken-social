# ============================================================
# Badge Models
# ============================================================
# Badge     = badge definition (e.g. "7-Day Streak")
# UserBadge = whether a specific user has earned it
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Badge(Base):
    """A badge definition."""
    __tablename__ = "badges"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    icon = Column(String, default="")
    color = Column(String, default="")
    bg_color = Column(String, default="")

    # Relationships
    user_badges = relationship("UserBadge", back_populates="badge")


class UserBadge(Base):
    """Whether a specific user has earned a badge."""
    __tablename__ = "user_badges"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    badge_id = Column(String, ForeignKey("badges.id"), nullable=False)

    earned = Column(Boolean, default=False)
    earned_date = Column(String, nullable=True)
    progress = Column(String, nullable=True)       # "15/30 days"
    days_away = Column(Integer, nullable=True)

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
            "bgColor": self.badge.bg_color if self.badge else "",
            "earned": self.earned,
            "earnedDate": self.earned_date,
            "progress": self.progress,
            "daysAway": self.days_away,
        }
