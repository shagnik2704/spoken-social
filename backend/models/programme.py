# ============================================================
# Programme model — top-level abstraction above courses
# ============================================================
# Programmes group courses into offerings like FDP, Swayam Plus, ILW.
# A Course can belong to multiple Programmes (M2M via programme_courses).
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


class Programme(Base):
    __tablename__ = "programmes"

    id = Column(String(50), primary_key=True)               # e.g. "fdp", "swayam_plus", "ilw"
    name = Column(String(255), nullable=False)               # e.g. "FDP", "Swayam Plus", "ILW"
    description = Column(Text)
    icon = Column(String(50))                                # lucide icon name for frontend
    color = Column(String(100))                              # CSS gradient / color string
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    programme_courses = relationship("ProgrammeCourse", back_populates="programme", cascade="all, delete-orphan")


class ProgrammeCourse(Base):
    """Many-to-many junction: which courses belong to which programme."""
    __tablename__ = "programme_courses"

    programme_id = Column(String(50), ForeignKey("programmes.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(String(50), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)

    # Relationships
    programme = relationship("Programme", back_populates="programme_courses")
    course = relationship("Course", back_populates="programme_courses")
