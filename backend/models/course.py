from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone


class Course(Base):
    __tablename__ = "courses"

    id = Column(String(50), primary_key=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    forum_category = Column(String(200))  # e.g., "Linux New" — maps to forum's FOSS category
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    batches = relationship("Batch", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("UserCourse", back_populates="course")
    tutorials = relationship("Tutorial", back_populates="course")
    college_courses = relationship("CollegeCourse", back_populates="course", cascade="all, delete-orphan")
    programme_courses = relationship("ProgrammeCourse", back_populates="course")


class UserCourse(Base):
    __tablename__ = "user_courses"

    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    course_id = Column(String(50), ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    batch_id = Column(String(50), ForeignKey("batches.id", ondelete="SET NULL"), nullable=True)

    status = Column(String(20), nullable=False, default="in_progress")
    progress_percent = Column(Numeric(5, 2), default=0)
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="enrollments")
    batch = relationship("Batch", back_populates="enrollments")

    __table_args__ = (
        Index("idx_user_courses_user", "user_id"),
        Index("idx_user_courses_course", "course_id"),
    )

    def to_api_dict(self):
        # Derive completed count from user_tutorials
        return {
            "id": self.course_id,
            "title": self.course.title if self.course else "",
            "status": self.status,
            "progressPercent": float(self.progress_percent or 0),
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "forumCategory": self.course.forum_category if self.course else None,
            "batchId": self.batch_id,
            "batchName": self.batch.name if self.batch else None,
            "batchStatus": self.batch.computed_status if self.batch else "active",
            "batches": [self.batch.to_api_dict()] if self.batch else [],
        }
