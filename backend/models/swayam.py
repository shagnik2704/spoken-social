from sqlalchemy import Column, String, DateTime, Index
from database import Base
from datetime import datetime, timezone


class SwayamOIDCState(Base):
    __tablename__ = "swayam_oidc_states"

    state = Column(String(128), primary_key=True)
    nonce = Column(String(128), nullable=False)
    code_verifier = Column(String(128), nullable=False)
    login_hint = Column(String(255), nullable=True)
    enrollment_id = Column(String(255), nullable=True)
    target_link_uri = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_swayam_oidc_states_created_at", "created_at"),
    )
