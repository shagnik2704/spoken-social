# ============================================================
# College model — represents a participating institution
# ============================================================

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone


class College(Base):
    __tablename__ = "colleges"

    id = Column(String(50), primary_key=True)          # e.g. "vjti", "iitb"
    name = Column(String(255), nullable=False)          # e.g. "VJTI Mumbai"
    location = Column(String(255))                      # e.g. "Mumbai, Maharashtra"
    coordinator_name = Column(String(255))              # e.g. "Prof. Sanjay Deshmukh"
    course_id = Column(String(50), default="linux")     # Focus course for now
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    students = relationship("User", back_populates="college")
