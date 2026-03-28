"""Infrastructure tests — validates all Person C setup is working."""

import os
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GCS_BUCKET"] = "hailmary-491613-media"

import pytest
from io import BytesIO
from PIL import Image
from google.cloud import storage, firestore
from google import genai
from google.genai.types import GenerateContentConfig, Modality


def test_firestore_connection():
    """Verify Firestore is accessible and writable."""
    db = firestore.Client(project="hailmary-491613")
    doc_ref = db.collection("tests").document("infra_test")
    doc_ref.set({"status": "ok"})
    doc = doc_ref.get()
    assert doc.exists
    assert doc.to_dict()["status"] == "ok"
    doc_ref.delete()


def test_gcs_upload():
    """Verify Cloud Storage upload and public URL works."""
    client = storage.Client(project="hailmary-491613")
    bucket = client.bucket("hailmary-491613-media")
    blob = bucket.blob("tests/infra_test.txt")
    blob.upload_from_string("test content", content_type="text/plain")
    assert blob.exists()
    blob.delete()


def test_gemini_text():
    """Verify Gemini text generation works."""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say hello in one word.",
    )
    assert response.text is not None
    assert len(response.text) > 0


def test_gemini_interleaved():
    """Verify Gemini interleaved text+image generation works."""
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents="Draw a small red circle. Include a one-word description.",
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
        ),
    )
    text_found = False
    image_found = False
    for part in response.candidates[0].content.parts:
        if part.text:
            text_found = True
        elif part.inline_data:
            image_found = True
    assert text_found, "No text in interleaved response"
    assert image_found, "No image in interleaved response"


def test_health_endpoint():
    """Verify FastAPI health endpoint responds correctly."""
    from fastapi.testclient import TestClient
    from creative_storyteller.main import app
    client = TestClient(app)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_story_endpoint():
    """Verify story creation endpoint works."""
    from fastapi.testclient import TestClient
    from creative_storyteller.main import app
    client = TestClient(app)
    response = client.post("/api/v1/stories", json={
        "prompt": "A test story",
        "style": "watercolor",
        "audience": "children",
        "numScenes": 2,
    })
    assert response.status_code == 200
    data = response.json()
    assert "storyId" in data
    assert "streamUrl" in data

    # Clean up
    db = firestore.Client(project="hailmary-491613")
    db.collection("stories").document(data["storyId"]).delete()
