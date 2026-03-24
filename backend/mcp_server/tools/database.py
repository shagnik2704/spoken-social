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
    """Get health metrics per college, including count of students who completed all tutorials."""
    with engine.connect() as conn:
        # Base college stats
        where_clause = "WHERE c.id = :college_id" if college_id else ""
        params = {"college_id": college_id} if college_id else {}

        rows = conn.execute(text(
            "SELECT c.id as college_id, c.name as college_name, "
            "COUNT(u.id) as student_count, "
            "COALESCE(AVG(u.xp_total), 0) as avg_xp, "
            "COALESCE(MAX(u.xp_total), 0) as max_xp "
            "FROM colleges c "
            "LEFT JOIN users u ON u.college_id = c.id AND u.role = 'student' "
            f"{where_clause} "
            "GROUP BY c.id, c.name ORDER BY student_count DESC"
        ), params).mappings().all()

        # Count students who completed ALL their tutorials per college
        completed = conn.execute(text(
            "SELECT u.college_id, COUNT(*) as completed_students "
            "FROM ( "
            "    SELECT ut.user_id "
            "    FROM user_tutorials ut "
            "    JOIN users u ON u.id = ut.user_id AND u.role = 'student' "
            "    GROUP BY ut.user_id "
            "    HAVING COUNT(*) = COUNT(*) FILTER (WHERE ut.status = 'completed') "
            ") completed_users "
            "JOIN users u ON u.id = completed_users.user_id "
            "GROUP BY u.college_id"
        )).mappings().all()
        completed_map = {str(r["college_id"]): r["completed_students"] for r in completed}

    results = []
    for r in rows:
        d = dict(r)
        d["completed_students"] = completed_map.get(str(d["college_id"]), 0)
        results.append(d)
    return results


@mcp.tool()
def get_leaderboard(limit: int = 20) -> list[dict]:
    """Get the top students ranked by total XP."""
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT u.id, u.username, u.display_name, u.xp_total, u.level, "
            "u.college_id, c.name as college_name "
            "FROM users u "
            "LEFT JOIN colleges c ON c.id = u.college_id "
            "WHERE u.role = 'student' "
            "ORDER BY u.xp_total DESC "
            "LIMIT :limit"
        ), {"limit": limit}).mappings().all()

    return [
        {
            "rank": i + 1,
            "id": str(r["id"]),
            "username": r["username"],
            "display_name": r["display_name"],
            "xp_total": r["xp_total"],
            "level": r["level"],
            "college_id": r["college_id"],
            "college_name": r["college_name"],
        }
        for i, r in enumerate(rows)
    ]


@mcp.tool()
def get_feedback_summary(days: int = 7) -> dict:
    """Get an aggregated summary of student feedback (why students clicked 'No') over the last N days."""
    with engine.connect() as conn:
        # Aggregate by step_type and individual reason (unnesting the reasons array)
        by_reason = conn.execute(text(
            "SELECT tf.step_type, reason, COUNT(*) as count "
            "FROM tutorial_feedback tf, unnest(tf.reasons) as reason "
            "WHERE tf.created_at >= NOW() - MAKE_INTERVAL(days => :days) "
            "GROUP BY tf.step_type, reason "
            "ORDER BY count DESC"
        ), {"days": days}).mappings().all()

        # Totals per step_type
        by_step = conn.execute(text(
            "SELECT step_type, COUNT(*) as count "
            "FROM tutorial_feedback "
            "WHERE created_at >= NOW() - MAKE_INTERVAL(days => :days) "
            "GROUP BY step_type ORDER BY count DESC"
        ), {"days": days}).mappings().all()

        # Free-text "other" responses
        other_texts = conn.execute(text(
            "SELECT tf.step_type, tf.other_text, u.display_name, t.title as tutorial_title "
            "FROM tutorial_feedback tf "
            "JOIN users u ON u.id = tf.user_id "
            "JOIN tutorials t ON t.id = tf.tutorial_id "
            "WHERE tf.other_text IS NOT NULL AND tf.other_text != '' "
            "AND tf.created_at >= NOW() - MAKE_INTERVAL(days => :days) "
            "ORDER BY tf.created_at DESC "
            "LIMIT 50"
        ), {"days": days}).mappings().all()

    return {
        "period_days": days,
        "feedback_by_step_type": [dict(r) for r in by_step],
        "feedback_by_reason": [dict(r) for r in by_reason],
        "recent_other_texts": [dict(r) for r in other_texts],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@mcp.tool()
def get_student_feedback(user_id: str) -> dict:
    """Get all feedback entries submitted by a specific student, including their reasons and free-text comments."""
    with engine.connect() as conn:
        # Get student info
        student = conn.execute(text(
            "SELECT id, username, display_name, college_id "
            "FROM users WHERE id = :user_id"
        ), {"user_id": user_id}).mappings().first()

        if not student:
            return {"error": "Student not found"}

        # Get all their feedback entries
        feedback = conn.execute(text(
            "SELECT tf.step_type, tf.reasons, tf.other_text, tf.created_at, "
            "t.title as tutorial_title, t.tutorial_number "
            "FROM tutorial_feedback tf "
            "JOIN tutorials t ON t.id = tf.tutorial_id "
            "WHERE tf.user_id = :user_id "
            "ORDER BY tf.created_at DESC"
        ), {"user_id": user_id}).mappings().all()

    return {
        "student": {
            "id": str(student["id"]),
            "username": student["username"],
            "display_name": student["display_name"],
            "college_id": student["college_id"],
        },
        "total_feedback_count": len(feedback),
        "feedback": [
            {
                "tutorial_number": r["tutorial_number"],
                "tutorial_title": r["tutorial_title"],
                "step_type": r["step_type"],
                "reasons": list(r["reasons"]) if r["reasons"] else [],
                "other_text": r["other_text"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in feedback
        ],
    }
