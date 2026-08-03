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
from models.activity import Activity
from models.feedback import TutorialFeedback
from models.forum_activity import ForumActivity
from models.batch import Batch
from models.college_course import CollegeCourse
from models.programme import Programme, ProgrammeCourse
from models.impersonation_log import ImpersonationLog
