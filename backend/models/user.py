# ============================================================
# User Model — the core of everything
# ============================================================
# This maps to a "users" table in PostgreSQL.
# Every column here = a column in the database.
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    # Primary key — matches the "user-priya" format from mock data
    id = Column(String, primary_key=True)

    # Link to Spoken Tutorial (for when SSO is ready)
    spoken_tutorial_id = Column(Integer, unique=True, nullable=True)

    # Profile
    name = Column(String, nullable=False)
    username = Column(String, unique=True)
    email = Column(String, unique=True, nullable=False)
    initials = Column(String(5))
    bio = Column(Text, default="")
    avatar = Column(String, nullable=True)

    # College
    college = Column(String, nullable=True)
    department = Column(String, nullable=True)

    # Gamification
    level = Column(Integer, default=1)
    level_title = Column(String, default="Beginner")
    xp_total = Column(Integer, default=0)
    xp_for_next_level = Column(Integer, default=500)
    xp_today = Column(Integer, default=0)
    xp_this_week = Column(Integer, default=0)


    # Weekly goal (stored as JSON for flexibility)
    weekly_goal = Column(JSON, default={"target": 5, "completed": 0, "days": [False]*7, "dayLabels": ["M","T","W","T","F","S","S"]})

    # Social
    followers = Column(Integer, default=0)
    following = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)

    # Meta
    join_date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships — SQLAlchemy will auto-join these
    courses = relationship("UserCourse", back_populates="user")
    badges = relationship("UserBadge", back_populates="user")
    posts = relationship("Post", back_populates="author")
    tutorials = relationship("UserTutorial", back_populates="user")

    def to_api_dict(self):
        """Convert to the JSON shape the frontend expects."""
        return {
            "id": self.id,
            "name": self.name,
            "username": self.username,
            "initials": self.initials,
            "bio": self.bio,
            "level": self.level,
            "levelTitle": self.level_title,
            "xpTotal": self.xp_total,
            "xpForNextLevel": self.xp_for_next_level,
            "xpToday": self.xp_today,
            "xpThisWeek": self.xp_this_week,
            "joinDate": self.join_date,
            "location": self.location,
            "website": self.website,
            "followers": self.followers,
            "following": self.following,
            "postsCount": self.posts_count,
            "college": self.college,
            "department": self.department,
            "avatar": self.avatar,
        }
