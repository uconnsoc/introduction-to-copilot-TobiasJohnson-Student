import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

original_activities = copy.deepcopy(activities)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities():
    response = client.get("/activities")
    data = response.json()

    assert response.status_code == 200
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] == 12
    assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_for_activity_adds_participant():
    email = "jordan@mergington.edu"
    activity = quote("Chess Club", safe="")
    response = client.post(f"/activities/{activity}/signup?email={quote(email, safe='')}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"
    assert email in activities["Chess Club"]["participants"]


def test_signup_for_activity_rejects_duplicate_registration():
    email = "michael@mergington.edu"
    activity = quote("Chess Club", safe="")

    response = client.post(f"/activities/{activity}/signup?email={quote(email, safe='')}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_for_nonexistent_activity_returns_404():
    email = "student@mergington.edu"
    response = client.post("/activities/Nonexistent%20Club/signup?email=" + quote(email, safe=""))

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_from_activity():
    email = "michael@mergington.edu"
    activity = quote("Chess Club", safe="")
    response = client.delete(f"/activities/{activity}/participants/{quote(email, safe='')}")

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Chess Club"
    assert email not in activities["Chess Club"]["participants"]


def test_remove_nonexistent_participant_returns_400():
    email = "notregistered@mergington.edu"
    activity = quote("Chess Club", safe="")
    response = client.delete(f"/activities/{activity}/participants/{quote(email, safe='')}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Participant not found"


def test_remove_participant_from_nonexistent_activity_returns_404():
    email = "michael@mergington.edu"
    response = client.delete("/activities/No%20Club/participants/" + quote(email, safe=""))

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
