from database import SyncSessionLocal
from models import User
from routes.admin import get_platform_summary

db = SyncSessionLocal()
admin = db.query(User).filter_by(role="admin").first()
try:
    res = get_platform_summary(user=admin, db=db)
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
