from sqlalchemy import Column, String, BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone
import uuid


class Tag(Base):
    __tablename__ = "tags"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)


class PostTag(Base):
    __tablename__ = "post_tags"

    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(PG_UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    post = relationship("Post", back_populates="post_tags")
    tag = relationship("Tag")


class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag = Column(String(100), unique=True, nullable=False)


class PostHashtag(Base):
    __tablename__ = "post_hashtags"

    post_id = Column(PG_UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    hashtag_id = Column(PG_UUID(as_uuid=True), ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True)

    post = relationship("Post", back_populates="post_hashtags")
    hashtag = relationship("Hashtag")


class HashtagCount(Base):
    __tablename__ = "hashtag_counts"

    hashtag_id = Column(PG_UUID(as_uuid=True), ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True)
    count = Column(BigInteger, nullable=False, default=0)
    last_updated = Column(DateTime(timezone=True))

    hashtag = relationship("Hashtag")

    __table_args__ = (
        Index("idx_hashtag_counts_count", count.desc()),
    )
