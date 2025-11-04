import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_read_root():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect status code
    assert response.headers["location"] == "/static/index.html"
    
    # Test following the redirect
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200  # Final response after redirect

def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    activities = response.json()
    assert isinstance(activities, dict)
    assert "Chess Club" in activities
    assert "Programming Class" in activities

def test_signup_for_activity():
    # Test successful signup
    response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
    assert response.status_code == 200
    assert response.json()["message"] == "Signed up test@mergington.edu for Chess Club"

    # Verify the participant was added
    activities = client.get("/activities").json()
    assert "test@mergington.edu" in activities["Chess Club"]["participants"]

def test_signup_for_nonexistent_activity():
    response = client.post("/activities/Nonexistent Club/signup?email=test@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

def test_duplicate_signup():
    # First signup
    client.post("/activities/Programming Class/signup?email=duplicate@mergington.edu")
    
    # Attempt duplicate signup
    response = client.post("/activities/Programming Class/signup?email=duplicate@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"

def test_maximum_participants():
    activity_name = "Chess Club"
    # Get current number of spots left
    activities = client.get("/activities").json()
    max_participants = activities[activity_name]["max_participants"]
    current_participants = len(activities[activity_name]["participants"])
    spots_left = max_participants - current_participants

    # Fill up all remaining spots
    for i in range(spots_left):
        email = f"student{i}@mergington.edu"
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200

    # Try to sign up one more student
    response = client.post(f"/activities/{activity_name}/signup?email=onemore@mergington.edu")
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"

def test_unregister_from_activity():
    # First, sign up a test participant
    test_email = "unregister_test@mergington.edu"
    activity_name = "Programming Class"
    client.post(f"/activities/{activity_name}/signup?email={test_email}")

    # Test unregistration
    response = client.post(f"/activities/{activity_name}/unregister?email={test_email}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Unregistered {test_email} from {activity_name}"

    # Verify the participant was removed
    activities = client.get("/activities").json()
    assert test_email not in activities[activity_name]["participants"]

def test_unregister_from_nonexistent_activity():
    response = client.post("/activities/Nonexistent Club/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

def test_unregister_nonexistent_participant():
    response = client.post("/activities/Chess Club/unregister?email=nonexistent@mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Student not found in this activity"