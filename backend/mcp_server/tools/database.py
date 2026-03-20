from mcp_server.core import mcp
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")
    
engine = create_engine(DATABASE_URL, echo=False)

@mcp.tool()
def get_active_users_summary() -> dict:
    """Get a summary of user activity on the platform."""
    with engine.connect() as conn:
        role_counts = conn.execute(text(
            "SELECT role, COUNT(*) as count FROM users GROUP BY role"
        )).mappings().all()

        new_users = conn.execute(text(
            "SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '7 days'"
        )).scalar()

        xp_today = conn.execute(text(
            "SELECT COALESCE(SUM(xp_delta), 0) FROM xp_events "
            "WHERE created_at >= date_trunc('day', NOW())"
        )).scalar()

    return {
        "role_breakdown": [dict(r) for r in role_counts],
        "new_users_last_7_days": new_users,
        "total_xp_earned_today": xp_today,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

@mcp.tool()
def get_recent_activity(minutes: int = 30) -> dict:
    """Get recent platform activity within the last N minutes."""
    with engine.connect() as conn:
        recent_posts = conn.execute(text(
            "SELECT COUNT(*) FROM posts "
            "WHERE created_at >= NOW() - MAKE_INTERVAL(mins => :minutes)"
        ), {"minutes": minutes}).scalar()

        recent_tutorials = conn.execute(text(
            "SELECT COUNT(*) FROM user_tutorials "
            "WHERE completed_at IS NOT NULL "
            "AND completed_at >= NOW() - MAKE_INTERVAL(mins => :minutes)"
        ), {"minutes": minutes}).scalar()

        # FIXED: Using source_type instead of reason 
        recent_xp = conn.execute(text(
            "SELECT source_type as reason, COUNT(*) as count, SUM(xp_delta) as total_xp "
            "FROM xp_events "
            "WHERE created_at >= NOW() - MAKE_INTERVAL(mins => :minutes) "
            "GROUP BY source_type"
        ), {"minutes": minutes}).mappings().all()

    return {
        "window_minutes": minutes,
        "recent_posts": recent_posts,
        "recent_tutorial_completions": recent_tutorials,
        "xp_events_by_reason": [dict(r) for r in recent_xp],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }

@mcp.tool()
def get_college_health(college_id: str = None) -> list[dict]:
    """Get health metrics per college."""
    with engine.connect() as conn:
        if college_id:
            rows = conn.execute(text(
                "SELECT c.id as college_id, c.name as college_name, "
                "COUNT(u.id) as student_count, "
                "COALESCE(AVG(u.xp_total), 0) as avg_xp, "
                "COALESCE(MAX(u.xp_total), 0) as max_xp "
                "FROM colleges c "
                "LEFT JOIN users u ON u.college_id = c.id AND u.role = 'student' "
                "WHERE c.id = :college_id "
                "GROUP BY c.id, c.name"
            ), {"college_id": college_id}).mappings().all()
        else:
            rows = conn.execute(text(
                "SELECT c.id as college_id, c.name as college_name, "
                "COUNT(u.id) as student_count, "
                "COALESCE(AVG(u.xp_total), 0) as avg_xp, "
                "COALESCE(MAX(u.xp_total), 0) as max_xp "
                "FROM colleges c "
                "LEFT JOIN users u ON u.college_id = c.id AND u.role = 'student' "
                "GROUP BY c.id, c.name ORDER BY student_count DESC"
            )).mappings().all()

    return [dict(r) for r in rows]
