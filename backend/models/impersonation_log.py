# ============================================================
# ImpersonationLog — audit trail for role impersonation
# ============================================================

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone


class ImpersonationLog(Base):
    __tablename__ = "impersonation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    real_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    effective_user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    effective_role = Column(String(20), nullable=False)       # student | coordinator | admin
    target_college_id = Column(String(50), ForeignKey("colleges.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(50), nullable=False)               # start | end
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    real_user = relationship("User", foreign_keys=[real_user_id])
    effective_user = relationship("User", foreign_keys=[effective_user_id])

    __table_args__ = (
        Index("idx_impersonation_real_user", "real_user_id", created_at.desc()),
    )
