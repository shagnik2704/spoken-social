from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from database import get_db
from models.post import Post
from models.hashtag import PostHashtag

router = APIRouter(prefix='/api', tags=['feed'])


@router.get('/feed')
async def get_feed(db: AsyncSession = Depends(get_db)):
    """Returns the feed — posts with derived counts from interaction tables."""
    stmt = (
        select(Post)
        .options(
            selectinload(Post.author),
            selectinload(Post.likes),
            selectinload(Post.comments),
            selectinload(Post.shares),
            selectinload(Post.post_hashtags).selectinload(PostHashtag.hashtag),
        )
        .order_by(Post.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)
    posts = result.scalars().all()

    # Deduplicate due to joinedload producing multiple rows
    seen = set()
    unique_posts = []
    for p in posts:
        if p.id not in seen:
            seen.add(p.id)
            unique_posts.append(p)

    return [p.to_api_dict() for p in unique_posts]
