from sqlalchemy import Column, String, Integer, DateTime, Text, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    bio = Column(Text)
    department_year = Column(String(128))
    location = Column(String(100))
    website = Column(String(255))
    level = Column(Integer, nullable=False, default=1)
    xp_total = Column(Integer, nullable=False, default=0)
    xp_last_week = Column(Integer, nullable=False, default=0)
    role = Column(String(20), nullable=False, default="student")  # student | coordinator | admin
    college_id = Column(String(50), ForeignKey("colleges.id"), nullable=True)  # which college they belong to
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    college = relationship("College", back_populates="students")
    courses = relationship("UserCourse", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    posts = relationship("Post", back_populates="author")
    tutorials = relationship("UserTutorial", back_populates="user")
    xp_events = relationship("XPEvent", back_populates="user")
    activities = relationship("Activity", back_populates="user")

    # Follow relationships
    followers_rel = relationship("Follow", foreign_keys="Follow.following_id", back_populates="following_user")
    following_rel = relationship("Follow", foreign_keys="Follow.follower_id", back_populates="follower_user")

    __table_args__ = (
        Index("idx_users_xp_total", xp_total.desc()),
    )

    def to_api_dict(self, db=None):
        """Convert to the JSON shape the frontend expects."""
        from models.post import Post
        from models.follow import Follow

        followers_count = 0
        following_count = 0
        posts_count = 0
        xp_today = 0
        xp_this_week = 0

        if db:
            from sqlalchemy import func, text
            from models.xp_event import XPEvent

            followers_count = db.query(func.count()).filter(Follow.following_id == self.id).scalar() or 0
            following_count = db.query(func.count()).filter(Follow.follower_id == self.id).scalar() or 0
            posts_count = db.query(func.count()).filter(Post.user_id == self.id).scalar() or 0

            xp_today = db.query(func.coalesce(func.sum(XPEvent.xp_delta), 0)).filter(
                XPEvent.user_id == self.id,
                XPEvent.created_at >= func.date_trunc('day', func.now())
            ).scalar() or 0

            xp_this_week = db.query(func.coalesce(func.sum(XPEvent.xp_delta), 0)).filter(
                XPEvent.user_id == self.id,
                XPEvent.created_at >= func.date_trunc('week', func.now())
            ).scalar() or 0

        # Compute xp_for_next_level using formula: 100 * (level+1)^2
        xp_for_next_level = 100 * (self.level + 1) * (self.level + 1)

        return {
            "id": str(self.id),
            "username": self.username,
            "displayName": self.display_name,
            "email": self.email,
            "bio": self.bio,
            "departmentYear": self.department_year,
            "location": self.location,
            "website": self.website,
            "level": self.level,
            "levelTitle": self._level_title(),
            "xpTotal": self.xp_total,
            "xpForNextLevel": xp_for_next_level,
            "xpToday": xp_today,
            "xpThisWeek": xp_this_week,
            "xpLastWeek": self.xp_last_week,
            "followers": followers_count,
            "following": following_count,
            "postsCount": posts_count,
            "role": self.role,
            "collegeId": self.college_id,
        }

    def _level_title(self):
        if self.xp_total >= 12000: return "Spoken Legend"
        elif self.xp_total >= 7000: return "Master"
        elif self.xp_total >= 3500: return "Expert"
        elif self.xp_total >= 1500: return "Practitioner"
        elif self.xp_total >= 500: return "Explorer"
        else: return "Beginner"
