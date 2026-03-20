from mcp_server.server import mcp
from datetime import datetime, timezone
import logging

logger = logging.getLogger("spoken_social.alerts")

_recent_alerts: list[dict] = []

@mcp.tool()
def send_alert(
    severity: str,
    subject: str,
    summary: str,
    recommended_actions: list[str],
) -> dict:
    """Send an alert about a platform issue."""
    alert = {
        "severity": severity,
        "subject": subject,
        "summary": summary,
        "recommended_actions": recommended_actions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _recent_alerts.append(alert)

    logger.warning(f"ALERT [{severity.upper()}]: {subject}")
    logger.warning(f"  Summary: {summary}")
    for action in recommended_actions:
        logger.warning(f"  -> {action}")

    return {"sent": True, "alert_id": len(_recent_alerts)}

@mcp.tool()
def check_recent_alerts(hours: int = 1) -> list[dict]:
    """Check what alerts were sent recently."""
    cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
    return [
        a for a in _recent_alerts
        if datetime.fromisoformat(a["timestamp"]).timestamp() > cutoff
    ]

@mcp.tool()
def store_insight(category: str, summary: str, details: str) -> dict:
    """Store a non-urgent insight for the daily digest email."""
    insight = {
        "category": category,
        "summary": summary,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"Insight [{category}]: {summary}")
    return {"stored": True, "insight": insight}
