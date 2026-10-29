# ============================================================
# Learner Pack Models — For SWAYAM Plus & Content-Rich Courses
# ============================================================
# Supports structured readings, notebook activities ("Try it"),
# student written reflections, 5-question automated quizzes,
# and dated habit log check-ins.
# ============================================================

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date,
    Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship
from database import Base


class TutorialContent(Base):
    """Stores the structured educational content for a tutorial in a learner pack."""
    __tablename__ = "tutorial_contents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutorial_id = Column(PG_UUID(as_uuid=True), ForeignKey("tutorials.id", ondelete="CASCADE"), unique=True, nullable=False)
    week_number = Column(Integer, nullable=False, default=1)
    
    # Reading Section
    reading_title = Column(String(255), nullable=False)
    reading_markdown = Column(Text, nullable=False)       # Full structured reading text
    reading_time_minutes = Column(Integer, default=15)
    
    # Activity ("Try it") Section
    try_it_instructions = Column(Text, nullable=False)    # Private notebook instructions
    
    # Reflection Prompt Section
    reflection_prompt = Column(Text, nullable=False)      # Questions for 3-5 sentence reflection
    reflection_min_sentences = Column(Integer, default=3)
    
    # Supplementary
    key_terms = Column(JSONB, default=list)               # [{"term": "...", "meaning": "..."}]
    read_more = Column(JSONB, default=list)               # [{"title": "...", "author": "...", "desc": "..."}]
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship
    tutorial = relationship("Tutorial", backref="learner_pack_content")


class QuizQuestion(Base):
    """5 multiple-choice questions per tutorial in the learner pack."""
    __tablename__ = "quiz_questions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tutorial_id = Column(PG_UUID(as_uuid=True), ForeignKey("tutorials.id", ondelete="CASCADE"), nullable=False)
    question_number = Column(Integer, nullable=False)     # 1 to 5
    question_text = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False)               # [{"id": "A", "text": "..."}, {"id": "B", "text": "..."}]
    correct_option = Column(String(5), nullable=False)    # "A", "B", "C", "D"
    explanation = Column(Text, nullable=False)            # Explanatory rationale shown after submission
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("tutorial_id", "question_number", name="uq_tutorial_quiz_question"),
        Index("idx_quiz_questions_tutorial", "tutorial_id"),
    )


class UserReflection(Base):
    """Stores the student's 3-5 sentence reflection submission for a tutorial."""
    __tablename__ = "user_reflections"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutorial_id = Column(PG_UUID(as_uuid=True), ForeignKey("tutorials.id", ondelete="CASCADE"), nullable=False)
    
    reflection_text = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "tutorial_id", name="uq_user_tutorial_reflection"),
        Index("idx_user_reflections_user", "user_id"),
    )


class UserQuizAttempt(Base):
    """Stores student's quiz submission, score, and answers."""
    __tablename__ = "user_quiz_attempts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    tutorial_id = Column(PG_UUID(as_uuid=True), ForeignKey("tutorials.id", ondelete="CASCADE"), nullable=False)
    
    score = Column(Integer, nullable=False)               # Number of correct answers (0-5)
    total_questions = Column(Integer, default=5)
    submitted_answers = Column(JSONB, nullable=False)     # {"1": "A", "2": "C", ...}
    passed = Column(Boolean, default=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "tutorial_id", name="uq_user_tutorial_quiz"),
        Index("idx_user_quiz_attempts_user", "user_id"),
    )


class UserHabitLogCheckin(Base):
    """Dated check-ins for multi-day habit logs (Emotion, Belief, Empathy, Breathing, Portfolio)."""
    __tablename__ = "user_habit_log_checkins"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(String(50), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    log_type = Column(String(50), nullable=False)         # "emotion", "belief", "empathy", "breathing", "portfolio"
    day_number = Column(Integer, nullable=False)          # 1 to 7
    checkin_date = Column(Date, nullable=False)
    
    # End of log summary reflection (150-200 words or 400-500 words for portfolio)
    summary_reflection = Column(Text, nullable=True)
    summary_submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", "log_type", "day_number", name="uq_user_habit_day"),
        Index("idx_user_habit_checkins", "user_id", "course_id", "log_type"),
    )
