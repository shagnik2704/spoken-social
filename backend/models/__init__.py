# Import all models so SQLAlchemy can resolve relationships between them.
# This file must be imported before any queries are made.

from models.user import User
from models.college import College
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.post import Post
from models.badge import Badge, UserBadge
from models.interaction import PostLike, PostComment, PostShare
from models.follow import Follow
from models.hashtag import Tag, PostTag, Hashtag, PostHashtag, HashtagCount
from models.xp_event import XPEvent
from models.leaderboard import LeaderboardWeekly
from models.activity import Activity
from models.feedback import TutorialFeedback
