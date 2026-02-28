from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone
import uuid


class PostLike(Base):
    __tablename__ = "post_likes"

    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="likes")
    user = relationship("User")

    __table_args__ = (
        Index("idx_post_likes_post", "post_id"),
    )


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"))
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="comments")
    user = relationship("User")

    __table_args__ = (
        Index("idx_post_comments_post", "post_id"),
    )


class PostShare(Base):
    __tablename__ = "post_shares"

    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="shares")
    user = relationship("User")

    __table_args__ = (
        Index("idx_post_shares_post", "post_id"),
    )
