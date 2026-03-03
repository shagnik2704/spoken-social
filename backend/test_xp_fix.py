import asyncio
import uuid
import httpx
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    async with httpx.AsyncClient() as client:
        # We need a user token. 
        # Alternatively, let's just use the testing file structure or create via script!
        res = await client.post("http://localhost:8000/api/register", json={
            "username": f"testuser_{uuid.uuid4().hex[:6]}",
            "password": "password123",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "displayName": "Test User",
            "role": "student"
        })
        user_data = res.json()
        print("Registered:", user_data)
        token = user_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # get user's courses
        res = await client.get("http://localhost:8000/api/me", headers=headers)
        course_id = "linux" # default
        
        # get tutorials
        res = await client.get(f"http://localhost:8000/api/me/courses/{course_id}/tutorials", headers=headers)
        tutorials = res.json()
        t1_id = tutorials[0]["id"]
        print("Target Tutorial:", tutorials[0]["title"])

        # toggle yes
        res = await client.put(f"http://localhost:8000/api/me/courses/{course_id}/tutorials/{t1_id}", json={"field": "watched", "value": True}, headers=headers)
        print("Toggle YES response:", res.json())

        res = await client.get("http://localhost:8000/api/me", headers=headers)
        print("XP after YES:", res.json()["user"]["xpTotal"])

        # toggle no
        res = await client.put(f"http://localhost:8000/api/me/courses/{course_id}/tutorials/{t1_id}", json={"field": "watched", "value": False}, headers=headers)
        print("Toggle NO response:", res.json())

        res = await client.get("http://localhost:8000/api/me", headers=headers)
        print("XP after NO:", res.json()["user"]["xpTotal"])

asyncio.run(main())
