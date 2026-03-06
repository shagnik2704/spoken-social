import sys
import os

from database import SyncSessionLocal
from models import (
    College, User, Course, Tutorial, Badge, Follow, UserCourse,
    Post, Hashtag, PostHashtag, PostLike, PostComment, PostShare,
    HashtagCount, TutorialFeedback, Activity, XPEvent, UserBadge,
    UserTutorial
)

def clear_all():
    db = SyncSessionLocal()
    print("🗑️  Clearing all tables...")
    try:
        # Delete in reverse-dependency order
        db.query(TutorialFeedback).delete()
        db.query(PostHashtag).delete()
        db.query(HashtagCount).delete()
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

if __name__ == "__main__":
    clear_all()
