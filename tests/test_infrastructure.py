"""Infrastructure + ADK API tests for Creative Storyteller."""
import os
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GCS_BUCKET"] = "hailmary-491613-media"
import pytest
import httpx
from google.cloud import storage, firestore
from google import genai
from google.genai.types import GenerateContentConfig, Modality
LIVE_URL = "https://creative-storyteller-zaad2c7uvq-uc.a.run.app"
APP_NAME = "creative_storyteller"
# === GCP Infrastructure Tests ===
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
    """Verify Cloud Storage upload works."""
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
        contents="Create a children's storybook illustration of a cute orange fox in a forest. Write a title for the image.",
        config=GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE],
        ),
    )
    has_content = len(response.candidates[0].content.parts) > 0
    assert has_content, "No content in interleaved response"
# === Live Deployment Tests ===
def test_health_endpoint():
    """Verify deployed service health check."""
    r = httpx.get(f"{LIVE_URL}/health", timeout=10)
    assert r.status_code == 200
def test_version_endpoint():
    """Verify version endpoint responds."""
    r = httpx.get(f"{LIVE_URL}/version", timeout=10)
    assert r.status_code == 200
def test_list_apps():
    """Verify the agent app is registered."""
    r = httpx.get(f"{LIVE_URL}/list-apps", timeout=10)
    assert r.status_code == 200
    apps = r.json()
    assert APP_NAME in str(apps), f"App '{APP_NAME}' not found in {apps}"
def test_create_session():
    """Verify session creation works."""
    r = httpx.post(
        f"{LIVE_URL}/apps/{APP_NAME}/users/test_user/sessions",
        timeout=10,
    )
    assert r.status_code == 200
    data = r.json()
    assert "id" in data or "session_id" in data or len(data) > 0
def test_get_sessions():
    """Verify session listing works."""
    r = httpx.get(
        f"{LIVE_URL}/apps/{APP_NAME}/users/test_user/sessions",
        timeout=10,
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)
def test_cors_headers():
    """Verify CORS is enabled for frontend access."""
    r = httpx.get(
        f"{LIVE_URL}/health",
        headers={"Origin": "http://localhost:3000"},
        timeout=10,
    )
    assert r.status_code == 200
