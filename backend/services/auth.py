# ============================================================
# Auth Service — credential verification
# ============================================================
# TODAY:  Checks against mock users (plain text comparison — it's mock data)
# LATER:  Swap verify_credentials() to call Spoken Tutorial's API
# ============================================================

import uuid

# Fixed UUIDs for mock users so they're consistent across restarts
PRIYA_UUID = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")
RAHUL_UUID = uuid.UUID("b2c3d4e5-f6a7-8901-bcde-f12345678901")

_MOCK_USERS = {
    "priya@vjti.ac.in": {
        "user_id": PRIYA_UUID,
        "display_name": "Priya Singh",
        "username": "@priya_learns",
        "email": "priya@vjti.ac.in",
        "password": "password123",
    },
    "rahul@iitb.ac.in": {
        "user_id": RAHUL_UUID,
        "display_name": "Rahul Sharma",
        "username": "@rahul_codes",
        "email": "rahul@iitb.ac.in",
        "password": "password123",
    },
}


def verify_credentials(email: str, password: str) -> dict | None:
    """
    THE function to swap later.
    Today: checks mock users with plain comparison
    Later: calls Spoken Tutorial's API (they handle password verification)
    """
    user = _MOCK_USERS.get(email)
    if not user:
        return None

    if user["password"] != password:
        return None

    return {
        "user_id": str(user["user_id"]),
        "display_name": user["display_name"],
        "username": user["username"],
        "email": email,
    }
