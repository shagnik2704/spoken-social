from fastapi import APIRouter
from data import feed_data
from pydantic import BaseModel
import time

router = APIRouter(prefix='/api', tags=['feed'])

@router.get('/feed')
def get_feed():
    return feed_data


class LikeUpdate(BaseModel):
    isLiked: bool

@router.put('/feed/{post_id}/like')
def toggle_like(post_id: str):
    # This is a mock interaction for now
    for post in feed_data:
        if post["id"] == post_id:
            post["isLiked"] = not post.get("isLiked", False)
            if post["isLiked"]:
                post["likes"] = post.get("likes", 0) + 1
            else:
                post["likes"] = max(0, post.get("likes", 0) - 1)
            return post
    return {"error": "Post not found"}

class FeedPostCreate(BaseModel):
    content: str
    type: str # 'achievement' | 'question' | 'discussion' | 'milestone'
    tags: list[str] = []
    courseName: str | None = None
    authorId: str
    authorName: str
    authorInitials: str
    authorLevel: int
    authorTitle: str


@router.post('/feed')
def create_post(body: FeedPostCreate):
    new_post = {
        "id": f"post-{int(time.time() * 1000)}",
        "author": {
            "id": body.authorId,
            "name": body.authorName,
            "initials": body.authorInitials,
            "level": body.authorLevel,
            "title": body.authorTitle
        },
        "type": body.type,
        "content": body.content,
        "courseName": body.courseName,
        "timestamp": "Just now",
        "createdAt": int(time.time() * 1000),
        "likes": 0,
        "comments": 0,
        "shares": 0,
        "isLiked": False,
        "isBookmarked": False,
        "tags": body.tags,
    }
    
    # insert at the top
    feed_data.insert(0, new_post)
    return new_post
