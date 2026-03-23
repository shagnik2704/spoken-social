import requests

def test():
    import uuid
    uid = uuid.uuid4().hex[:8]
    res = requests.post("http://localhost:8000/api/auth/register", json={
        "username": f"test_{uid}",
        "password": "password",
        "email": f"test_{uid}@example.com",
        "displayName": "Tester",
        "role": "student"
    })
    token = res.json().get("access_token")
    if not token:
        print("Error during register:", res.json())
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # Get tutorials
    res = requests.get("http://localhost:8000/api/me/courses/linux/tutorials", headers=headers)
    t1_id = res.json()[0]["id"]
    
    # Watched = YES
    res = requests.put(f"http://localhost:8000/api/me/courses/linux/tutorials/{t1_id}", json={"field": "watched", "value": True}, headers=headers)
    xp1 = requests.get("http://localhost:8000/api/me", headers=headers).json()["user"]["xpTotal"]
    print(f"XP after YES: {xp1}")
    
    # Watched = NO
    res = requests.put(f"http://localhost:8000/api/me/courses/linux/tutorials/{t1_id}", json={"field": "watched", "value": False}, headers=headers)
    xp2 = requests.get("http://localhost:8000/api/me", headers=headers).json()["user"]["xpTotal"]
    print(f"XP after NO: {xp2}")

if __name__ == "__main__":
    test()
