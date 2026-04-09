"""
Backend tests for the Mergington High School API.

Tests use pytest and FastAPI TestClient. Each test is written with
Arrange-Act-Assert structure and the in-memory activity state is restored
after each test.
"""

import copy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def restore_activity_state():
    original_activities = copy.deepcopy(activities)
    try:
        yield
    finally:
        activities.clear()
        activities.update(original_activities)


@pytest.fixture
def client():
    return TestClient(app)


class TestRootEndpoint:
    def test_root_redirects_to_static_index(self, client):
        # Arrange

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code in (307, 308)
        assert response.headers["location"].endswith("/static/index.html")


class TestActivitiesEndpoint:
    def test_get_activities_returns_activity_map(self, client):
        # Arrange

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_structure_contains_required_fields(self, client):
        # Arrange
        expected_fields = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()["Chess Club"]

        # Assert
        assert expected_fields.issubset(set(data.keys()))
        assert isinstance(data["participants"], list)


class TestSignupEndpoint:
    def test_signup_adds_participant(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "testsignup@mergington.edu"
        before = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        after = len(client.get("/activities").json()[activity_name]["participants"])
        assert after == before + 1

    def test_signup_duplicate_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "activity not found" in response.json()["detail"].lower()


class TestRemoveParticipantEndpoint:
    def test_remove_participant_successfully(self, client):
        # Arrange
        activity_name = "Drama Club"
        email = "isabella@mergington.edu"
        before = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        after = len(client.get("/activities").json()[activity_name]["participants"])
        assert after == before - 1

    def test_remove_nonexistent_participant_returns_404(self, client):
        # Arrange
        activity_name = "Drama Club"
        email = "notfound@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "participant not found" in response.json()["detail"].lower()

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Unknown Club"
        email = "test@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "activity not found" in response.json()["detail"].lower()
