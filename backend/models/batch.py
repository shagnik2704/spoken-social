# ============================================================
# Batch model — represents a time-bound offering of a course
# ============================================================

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone, date


class Batch(Base):
    __tablename__ = "batches"

    id = Column(String(50), primary_key=True)                # e.g. "linux-2026-jan"
    course_id = Column(String(50), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    programme_id = Column(String(50), ForeignKey("programmes.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(100), nullable=False)                # e.g. "Jan-Apr 2026"
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active | inactive
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("Course", back_populates="batches")
    enrollments = relationship("UserCourse", back_populates="batch")

    __table_args__ = (
        Index("idx_batches_course", "course_id"),
        Index("idx_batches_status", "status"),
    )

    @property
    def computed_status(self) -> str:
        """Auto-compute status based on end_date."""
        if self.end_date and self.end_date < date.today():
            return "inactive"
        return self.status

    def to_api_dict(self):
        return {
            "id": self.id,
            "courseId": self.course_id,
            "name": self.name,
            "startDate": self.start_date.isoformat() if self.start_date else None,
            "endDate": self.end_date.isoformat() if self.end_date else None,
            "status": self.computed_status,
            "is_active": self.computed_status == "active",
            "courseName": self.course.title if self.course else None,
        }
