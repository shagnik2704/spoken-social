# ============================================================
# Tutorial Models
# ============================================================
# Tutorial     = a single tutorial in a course (e.g. "Linux Lesson 3")
# UserTutorial = a student's progress on that tutorial
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Tutorial(Base):
    """A tutorial within a course — the template."""
    __tablename__ = "tutorials"

    id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="tutorials")
    user_progress = relationship("UserTutorial", back_populates="tutorial")


class UserTutorial(Base):
    """A student's progress on a single tutorial."""
    __tablename__ = "user_tutorials"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tutorial_id = Column(String, ForeignKey("tutorials.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)

    completed = Column(Boolean, default=False)
    watched = Column(String, nullable=True)         # "yes", "no", or null
    practiced = Column(String, nullable=True)
    assignment_done = Column(String, nullable=True)
    forum_asked = Column(String, nullable=True)
    forum_answered = Column(String, nullable=True)
    xp_earned = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="tutorials")
    tutorial = relationship("Tutorial", back_populates="user_progress")

    def to_api_dict(self):
        return {
            "id": self.tutorial_id,
            "number": self.tutorial.number if self.tutorial else 0,
            "title": self.tutorial.title if self.tutorial else "",
            "completed": self.completed,
            "watched": self.watched,
            "practiced": self.practiced,
            "assignmentDone": self.assignment_done,
            "forumAsked": self.forum_asked,
            "forumAnswered": self.forum_answered,
            "xpEarned": self.xp_earned,
        }
