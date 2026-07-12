from sqlalchemy import Column, String, Integer, DateTime, Text, Index, ForeignKey, Boolean
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
    college_id = Column(String(50), ForeignKey("colleges.id", ondelete="SET NULL"), nullable=True)  # which college they belong to
    is_test_account = Column(Boolean, default=False)  # Marks auto-generated test students
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
        Index("idx_users_college", "college_id"),
    )

    async def to_api_dict(self, db=None, active_course_id=None):
        """Convert to the JSON shape the frontend expects."""
        from models.post import Post
        from models.follow import Follow
        from sqlalchemy import select

        followers_count = 0
        following_count = 0
        posts_count = 0
        xp_today = 0
        xp_this_week = 0

        if db:
            from sqlalchemy import func
            from models.xp_event import XPEvent

            # Single round-trip: 5 scalar subqueries in one SELECT (was 5 separate queries).
            followers_sq = select(func.count()).where(Follow.following_id == self.id).scalar_subquery()
            following_sq = select(func.count()).where(Follow.follower_id == self.id).scalar_subquery()
            posts_sq = select(func.count()).where(Post.user_id == self.id).scalar_subquery()
            xp_today_sq = select(func.coalesce(func.sum(XPEvent.xp_delta), 0)).where(
                XPEvent.user_id == self.id,
                XPEvent.created_at >= func.date_trunc('day', func.now()),
            ).scalar_subquery()
            xp_week_sq = select(func.coalesce(func.sum(XPEvent.xp_delta), 0)).where(
                XPEvent.user_id == self.id,
                XPEvent.created_at >= func.date_trunc('week', func.now()),
            ).scalar_subquery()

            row = (await db.execute(
                select(followers_sq, following_sq, posts_sq, xp_today_sq, xp_week_sq)
            )).one()
            followers_count, following_count, posts_count, xp_today, xp_this_week = row

        # XP milestone for the next level up (see services/xp). The old 100*(level+1)^2
        # formula didn't match the discrete level thresholds, so the profile progress bar
        # could read >100% without the user actually leveling up.
        from services.xp import xp_for_next_level as _next_level_xp
        xp_for_next_level = _next_level_xp(self.xp_total)

        res = {
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
            "role": self.__dict__.get("effective_role", self.role),
            "effectiveRole": self.__dict__.get("effective_role", self.role),
            "isImpersonating": self.__dict__.get("is_impersonating", False),
            "collegeId": self.college_id,
            "active_batch_id": None,
            "active_batch_is_active": True,
        }

        # Try to find batch info from UserCourse
        if self.courses:
            # If active_course_id provided, use that, otherwise use first
            target_course = active_course_id or (self.courses[0].course_id if self.courses else None)
            uc = next((c for c in self.courses if c.course_id == target_course), self.courses[0] if self.courses else None)
            if uc:
                res["active_batch_id"] = uc.batch_id
                if uc.batch:
                    res["active_batch_is_active"] = uc.batch.status == "active"

        return res

    def _level_title(self):
        if self.xp_total >= 12000: return "Spoken Legend"
        elif self.xp_total >= 7000: return "Master"
        elif self.xp_total >= 3500: return "Expert"
        elif self.xp_total >= 1500: return "Practitioner"
        elif self.xp_total >= 500: return "Explorer"
        else: return "Beginner"
