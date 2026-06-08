import sys
import os

# Add backend directory to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SyncSessionLocal
from models import (
    College, User, Course, Tutorial, Badge, Follow, UserCourse,
    Post, Hashtag, PostHashtag, PostLike, PostComment, PostShare,
    HashtagCount, TutorialFeedback, Activity, XPEvent, UserBadge,
    UserTutorial, Tag, PostTag, LeaderboardWeekly
)

def clear_all():
    db = SyncSessionLocal()
    print("🗑️  Clearing all tables...")
    try:
        # Delete in reverse-dependency order
        db.query(TutorialFeedback).delete()
        db.query(LeaderboardWeekly).delete()
        db.query(PostHashtag).delete()
        db.query(HashtagCount).delete()
        db.query(PostTag).delete()
        db.query(PostLike).delete()
        db.query(PostComment).delete()
        db.query(PostShare).delete()
        db.query(Activity).delete()
        db.query(XPEvent).delete()
        db.query(UserBadge).delete()
        db.query(UserTutorial).delete()
        db.query(UserCourse).delete()
        db.query(Follow).delete()
        db.query(Post).delete()
        db.query(Hashtag).delete()
        db.query(Tag).delete()
        db.query(Badge).delete()
        db.query(Tutorial).delete()
        db.query(Course).delete()
        db.query(User).delete()
        db.query(College).delete()
        
        db.commit()
        print("✅  Success! All tables are now empty.")
    except Exception as e:
        db.rollback()
        print(f"❌  Error clearing database: {e}")
    finally:
        db.close()

def clear_redis():
    import redis
    print("🗑️  Clearing Redis data...")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        r = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        # We can flush all databases, or just flush the specific keys.
        r.flushdb()
        print("✅  Success! Redis cleared.")
    except Exception as e:
        print(f"❌  Error clearing redis: {e}")

if __name__ == "__main__":
    clear_all()
    clear_redis()
