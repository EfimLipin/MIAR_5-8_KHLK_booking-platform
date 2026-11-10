import requests
from uuid import uuid4

BASE_URL = "http://localhost:8003/api"

def test_create_search():
    resp = requests.post(f"{BASE_URL}/search",
                         json={"user_id": "u1", "destination": "Париж"})
    assert resp.status_code == 200
    assert resp.json()["destination"] == "Париж"

def test_favorites_flow():
    user_id = uuid4().hex
    resp = requests.post(f"{BASE_URL}/favorites",
                         json={"user_id": user_id, "tour_id": "t1"})
    assert resp.status_code == 200
    fav_id = resp.json()["id"]

    resp2 = requests.get(f"{BASE_URL}/favorites", params={"user_id": user_id})
    assert any(f["id"] == fav_id for f in resp2.json())

    resp3 = requests.delete(f"{BASE_URL}/favorites/{fav_id}")
    assert resp3.status_code == 200