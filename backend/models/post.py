# ============================================================
# Post Model — the social feed
# ============================================================

from sqlalchemy import Column, String, Integer, Boolean, Text, BigInteger, JSON, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)

    type = Column(String, nullable=False)           # achievement, question, discussion, milestone
    content = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    course_name = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)        # "2h ago" — display string
    created_at = Column(BigInteger, nullable=False)  # epoch ms for sorting

    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    tags = Column(JSON, default=[])

    # Relationships
    author = relationship("User", back_populates="posts")

    def to_api_dict(self):
        return {
            "id": self.id,
            "author": {
                "id": self.author.id,
                "name": self.author.name,
                "initials": self.author.initials,
                "level": self.author.level,
                "title": self.author.level_title,
            } if self.author else {},
            "type": self.type,
            "content": self.content,
            "details": self.details,
            "courseName": self.course_name,
            "timestamp": self.timestamp,
            "createdAt": self.created_at,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "isLiked": False,       # TODO: per-user likes table
            "isBookmarked": False,  # TODO: per-user bookmarks table
            "tags": self.tags or [],
        }
