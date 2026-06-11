# ============================================================
# CollegeCourse junction — which courses each college offers
# ============================================================

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


class CollegeCourse(Base):
    __tablename__ = "college_courses"

    college_id = Column(String(50), ForeignKey("colleges.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(String(50), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    programme_id = Column(String(50), ForeignKey("programmes.id", ondelete="CASCADE"), primary_key=True, server_default="fdp")
    enabled_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    college = relationship("College", back_populates="college_courses")
    course = relationship("Course", back_populates="college_courses")

