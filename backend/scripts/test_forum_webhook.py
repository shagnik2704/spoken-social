#!/usr/bin/env python3
"""
Quick test: simulate a forum webhook to verify the end-to-end flow.
Run with: python scripts/test_forum_webhook.py

Pre-requisites:
  - Backend server running on localhost:8000
  - At least one student user in the DB
"""

import httpx
import json
import sys
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8000"
WEBHOOK_URL = f"{BACKEND_URL}/api/webhooks/forum"

# Simulate a question_created event
def test_question_created():
    payload = {
        "event": "question_created",
        "user_id": 12345,  # Forum's user ID (for reference)
        "email": "demo@spoken-social.org",  # Must match a user in our DB
        "resource_id": 99901,  # Fake forum post ID
        "category": "Linux New",
        "tutorial": "Basic Commands in Linux",
        "title": "Test: How does the 'who' command work?",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"\n📤 Sending question_created webhook...")
    print(f"   Payload: {json.dumps(payload, indent=2)}")

    resp = httpx.post(WEBHOOK_URL, json=payload, timeout=10)
    print(f"\n📥 Response ({resp.status_code}): {resp.json()}")
    return resp


def test_answer_created():
    payload = {
        "event": "answer_created",
        "user_id": 12345,
        "email": "demo@spoken-social.org",
        "resource_id": 99902,
        "category": "Linux New",
        "tutorial": "Basic Commands in Linux",
        "question_id": 99901,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"\n📤 Sending answer_created webhook...")
    resp = httpx.post(WEBHOOK_URL, json=payload, timeout=10)
    print(f"📥 Response ({resp.status_code}): {resp.json()}")
    return resp


def test_duplicate():
    """Send the same question again — should be skipped (idempotent)."""
    payload = {
        "event": "question_created",
        "user_id": 12345,
        "email": "demo@spoken-social.org",
        "resource_id": 99901,  # Same ID as before
        "category": "Linux New",
        "tutorial": "Basic Commands in Linux",
        "title": "Test: How does the 'who' command work?",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"\n📤 Sending duplicate question_created (should be skipped)...")
    resp = httpx.post(WEBHOOK_URL, json=payload, timeout=10)
    print(f"📥 Response ({resp.status_code}): {resp.json()}")
    return resp


def test_question_deleted():
    payload = {
        "event": "question_deleted",
        "user_id": 12345,
        "resource_id": 99901,
        "category": "Linux New",
        "tutorial": "Basic Commands in Linux",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    print(f"\n📤 Sending question_deleted webhook (should revoke XP)...")
    resp = httpx.post(WEBHOOK_URL, json=payload, timeout=10)
    print(f"📥 Response ({resp.status_code}): {resp.json()}")
    return resp


if __name__ == "__main__":
    print("=" * 60)
    print("Forum Webhook Integration Test")
    print("=" * 60)

    test_question_created()
    test_answer_created()
    test_duplicate()

    if "--with-delete" in sys.argv:
        test_question_deleted()

    print("\n✅ All tests completed!")
