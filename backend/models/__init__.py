# Import all models so SQLAlchemy can resolve relationships between them.
# This file must be imported before any queries are made.

from models.user import User
from models.course import Course, UserCourse
from models.tutorial import Tutorial, UserTutorial
from models.post import Post
from models.badge import Badge, UserBadge
