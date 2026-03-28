"""API edge case tests — shows graceful error handling."""

import os
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GCS_BUCKET"] = "hailmary-491613-media"

import pytest
from fastapi.testclient import TestClient
from creative_storyteller.main import app
from google.cloud import firestore

client = TestClient(app)


def test_health_returns_version():
    """Health endpoint includes version for monitoring."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_root_endpoint():
    """Root endpoint confirms service is alive."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Creative Storyteller" in response.json()["message"]


def test_create_story_minimal():
    """Story creation works with only a prompt (defaults for rest)."""
    response = client.post("/api/v1/stories", json={
        "prompt": "A tiny dragon learning to fly",
    })
    assert response.status_code == 200
    data = response.json()
    assert "storyId" in data
    assert "streamUrl" in data
    assert data["streamUrl"].startswith("/api/v1/stories/")
    # Clean up
    db = firestore.Client(project="hailmary-491613")
    db.collection("stories").document(data["storyId"]).delete()


def test_create_story_all_options():
    """Story creation works with all options specified."""
    response = client.post("/api/v1/stories", json={
        "prompt": "A brave fox in a moonlit forest",
        "style": "anime",
        "audience": "teens",
        "numScenes": 3,
        "voiceEnabled": True,
    })
    assert response.status_code == 200
    data = response.json()
    assert "storyId" in data
    # Clean up
    db = firestore.Client(project="hailmary-491613")
    db.collection("stories").document(data["storyId"]).delete()


def test_create_story_empty_prompt():
    """Empty prompt should still be accepted (agent handles it)."""
    response = client.post("/api/v1/stories", json={
        "prompt": "",
    })
    assert response.status_code == 200


def test_create_story_missing_prompt():
    """Missing prompt field returns 422 validation error."""
    response = client.post("/api/v1/stories", json={
        "style": "watercolor",
    })
    assert response.status_code == 422


def test_create_story_invalid_json():
    """Invalid JSON body returns error."""
    response = client.post(
        "/api/v1/stories",
        content="not json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_get_nonexistent_story():
    """Requesting a story that doesn't exist returns 404."""
    response = client.get("/api/v1/stories/nonexistent_story_id_12345")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_stories_empty_user():
    """Listing stories for a user with no stories returns empty list."""
    response = client.get("/api/v1/stories?userId=user_that_does_not_exist")
    assert response.status_code == 200
    assert response.json() == []


def test_list_stories_default_user():
    """Listing stories without userId defaults to anonymous."""
    response = client.get("/api/v1/stories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_stream_endpoint_returns_sse():
    """Stream endpoint returns SSE content type."""
    # First create a story
    create_response = client.post("/api/v1/stories", json={
        "prompt": "test stream",
    })
    story_id = create_response.json()["storyId"]

    response = client.get(f"/api/v1/stories/{story_id}/stream")
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    # Clean up
    db = firestore.Client(project="hailmary-491613")
    db.collection("stories").document(story_id).delete()


def test_cors_headers():
    """CORS headers are present for cross-origin frontend access."""
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
