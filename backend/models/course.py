# ============================================================
# Course Models
# ============================================================
# Course      = the course template (e.g. "Python", "Linux")
# UserCourse  = a student's enrollment + progress in a course
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Course(Base):
    """A course template — e.g. 'Python' with 10 tutorials."""
    __tablename__ = "courses"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    total_tutorials = Column(Integer, default=0)

    # Relationships
    enrollments = relationship("UserCourse", back_populates="course")
    tutorials = relationship("Tutorial", back_populates="course")


class UserCourse(Base):
    """A student's enrollment in a course — tracks their progress."""
    __tablename__ = "user_courses"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)

    progress = Column(Integer, default=0)          # percentage
    completed_count = Column(Integer, default=0)   # tutorials done
    total = Column(Integer, default=0)             # total tutorials
    status = Column(String, default="not_started") # in_progress, completed, not_started
    completed_date = Column(String, nullable=True)
    test_passed = Column(Boolean, default=False)
    test_score = Column(Integer, nullable=True)

    # Relationships
    user = relationship("User", back_populates="courses")
    course = relationship("Course", back_populates="enrollments")

    def to_api_dict(self):
        return {
            "id": self.course_id,
            "title": self.course.title if self.course else "",
            "progress": self.progress,
            "completed": self.completed_count,
            "total": self.total,
            "status": self.status,
            "completedDate": self.completed_date,
        }
