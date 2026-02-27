# ============================================================
# Auth Service — credential verification
# ============================================================
# TODAY:  Checks against mock users (plain text comparison — it's mock data)
# LATER:  Swap verify_credentials() to call Spoken Tutorial's API
#         (at that point you don't handle passwords at all)
# ============================================================

# Mock users — since we'll swap this for an API call later,
# there's no point setting up bcrypt for temporary mock data.
# The real Spoken Tutorial API will handle password verification.

_MOCK_USERS = {
    "priya@vjti.ac.in": {
        "spoken_id": 1,
        "name": "Priya Singh",
        "user_id": "user-priya",
        "college": "VJTI Mumbai",
        "password": "password123",
    },
    "rahul@iitb.ac.in": {
        "spoken_id": 2,
        "name": "Rahul Sharma",
        "user_id": "user-rahul",
        "college": "IIT Bombay",
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
        "spoken_id": user["spoken_id"],
        "user_id": user["user_id"],
        "name": user["name"],
        "email": email,
        "college": user["college"],
    }
