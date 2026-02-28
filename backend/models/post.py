from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from database import Base
from datetime import datetime, timezone
import uuid


class Post(Base):
    __tablename__ = "posts"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    course_id = Column(String(50), ForeignKey("courses.id"), nullable=True)
    type = Column(String(30), default="discussion")
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    author = relationship("User", back_populates="posts")
    likes = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")
    comments = relationship("PostComment", back_populates="post", cascade="all, delete-orphan")
    shares = relationship("PostShare", back_populates="post", cascade="all, delete-orphan")
    post_hashtags = relationship("PostHashtag", back_populates="post", cascade="all, delete-orphan")
    post_tags = relationship("PostTag", back_populates="post", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_posts_created", created_at.desc()),
        Index("idx_posts_user", "user_id"),
    )

    def to_api_dict(self, current_user_id=None):
        from datetime import datetime, timezone
        import math

        # Derive counts from relationships
        likes_count = len(self.likes) if self.likes else 0
        comments_count = len(self.comments) if self.comments else 0
        shares_count = len(self.shares) if self.shares else 0

        # Check if current user liked/bookmarked
        is_liked = False
        if current_user_id and self.likes:
            is_liked = any(l.user_id == current_user_id for l in self.likes)

        # Collect hashtags
        hashtags = []
        if self.post_hashtags:
            hashtags = [ph.hashtag.tag for ph in self.post_hashtags if ph.hashtag]

        # Compute relative timestamp
        now = datetime.now(timezone.utc)
        if self.created_at:
            ca = self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc)
            delta = now - ca
            secs = delta.total_seconds()
            if secs < 60: timestamp = "Just now"
            elif secs < 3600: timestamp = f"{int(secs//60)}m ago"
            elif secs < 86400: timestamp = f"{int(secs//3600)}h ago"
            else: timestamp = f"{int(secs//86400)}d ago"
        else:
            timestamp = ""

        return {
            "id": str(self.id),
            "author": {
                "id": str(self.author.id) if self.author else "",
                "name": self.author.display_name if self.author else "",
                "username": self.author.username if self.author else "",
                "level": self.author.level if self.author else 0,
                "title": self.author._level_title() if self.author else "",
            } if self.author else {},
            "type": self.type,
            "content": self.content,
            "courseId": self.course_id,
            "timestamp": timestamp,
            "createdAt": int(self.created_at.timestamp() * 1000) if self.created_at else 0,
            "likes": likes_count,
            "comments": comments_count,
            "shares": shares_count,
            "isLiked": is_liked,
            "isBookmarked": False,
            "tags": hashtags,
        }
