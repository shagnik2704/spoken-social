from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func
from database import get_db
from models.post import Post
from models.hashtag import PostHashtag
from models.interaction import PostLike, PostComment, PostShare

router = APIRouter(prefix='/api', tags=['feed'])


@router.get('/feed')
async def get_feed(db: AsyncSession = Depends(get_db)):
    """Returns the feed — posts with derived counts from interaction tables."""
    # Derive counts with correlated COUNT subqueries instead of loading every
    # like/comment/share row into memory just to len() them.
    likes_ct = (
        select(func.count()).where(PostLike.post_id == Post.id)
        .correlate(Post).scalar_subquery()
    )
    comments_ct = (
        select(func.count()).where(PostComment.post_id == Post.id)
        .correlate(Post).scalar_subquery()
    )
    shares_ct = (
        select(func.count()).where(PostShare.post_id == Post.id)
        .correlate(Post).scalar_subquery()
    )

    stmt = (
        select(
            Post,
            likes_ct.label("likes_count"),
            comments_ct.label("comments_count"),
            shares_ct.label("shares_count"),
        )
        .options(
            selectinload(Post.author),
            selectinload(Post.post_hashtags).selectinload(PostHashtag.hashtag),
        )
        .order_by(Post.created_at.desc())
        .limit(50)
    )
    result = await db.execute(stmt)

    return [
        post.to_api_dict(
            likes_count=likes_count,
            comments_count=comments_count,
            shares_count=shares_count,
        )
        for post, likes_count, comments_count, shares_count in result.all()
    ]
