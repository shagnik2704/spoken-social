from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models.post import Post

router = APIRouter(prefix='/api', tags=['feed'])


@router.get('/feed')
def get_feed(db: Session = Depends(get_db)):
    """Returns the feed — posts with derived counts from interaction tables."""
    posts = (
        db.query(Post)
        .options(
            joinedload(Post.author),
            joinedload(Post.likes),
            joinedload(Post.comments),
            joinedload(Post.shares),
            joinedload(Post.post_hashtags),
        )
        .order_by(Post.created_at.desc())
        .limit(50)
        .all()
    )

    # Deduplicate due to joinedload producing multiple rows
    seen = set()
    unique_posts = []
    for p in posts:
        if p.id not in seen:
            seen.add(p.id)
            unique_posts.append(p)

    return [p.to_api_dict() for p in unique_posts]
