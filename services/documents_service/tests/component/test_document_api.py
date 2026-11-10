import requests
from uuid import uuid4

BASE_URL = "http://localhost:8004/api"

def test_create_and_get_document():
    booking_id = uuid4().hex
    resp = requests.post(f"{BASE_URL}/documents",
                         json={"booking_id": booking_id, "user_id": "u1", "tour_id": "t1"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["booking_id"] == booking_id
    assert body["status"] == "created"

    resp2 = requests.get(f"{BASE_URL}/documents/{body['id']}")
    assert resp2.status_code == 200

def test_sign_contract():
    resp = requests.post(f"{BASE_URL}/documents",
                         json={"booking_id": uuid4().hex, "user_id": "u1", "tour_id": "t1"})
    doc_id = resp.json()["id"]
    resp2 = requests.post(f"{BASE_URL}/documents/{doc_id}:sign")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "completed"