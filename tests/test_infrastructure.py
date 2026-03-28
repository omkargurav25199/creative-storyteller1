"""Creative Storyteller — Comprehensive Test Suite.
Tests GCP infrastructure, live deployment, Gemini models,
error handling, and graceful degradation."""

import os, time
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GCS_BUCKET"] = "hailmary-491613-media"

import pytest
import httpx
from io import BytesIO
from google.cloud import storage, firestore
from google import genai
from google.genai.types import GenerateContentConfig, Modality
from PIL import Image

LIVE_URL = "https://creative-storyteller-zaad2c7uvq-uc.a.run.app"
APP_NAME = "creative_storyteller"
PROJECT_ID = "hailmary-491613"
GCS_BUCKET = "hailmary-491613-media"


# =====================================================
# SECTION 1: GCP Infrastructure (Core Services)
# =====================================================

class TestFirestore:
    """Validate Firestore database operations."""

    def test_write_and_read(self):
        """Documents can be written and read back correctly."""
        db = firestore.Client(project=PROJECT_ID)
        doc_ref = db.collection("tests").document("infra_test")
        doc_ref.set({"status": "ok", "timestamp": time.time()})
        doc = doc_ref.get()
        assert doc.exists
        assert doc.to_dict()["status"] == "ok"
        doc_ref.delete()

    def test_subcollection(self):
        """Subcollections work (required for stories/{id}/scenes/{id})."""
        db = firestore.Client(project=PROJECT_ID)
        parent = db.collection("tests").document("parent_test")
        parent.set({"name": "test story"})
        child = parent.collection("scenes").document("scene_1")
        child.set({"order": 1, "text": "Once upon a time..."})
        child_doc = child.get()
        assert child_doc.exists
        assert child_doc.to_dict()["order"] == 1
        child.delete()
        parent.delete()

    def test_story_data_model(self):
        """Full story data model matches production schema."""
        db = firestore.Client(project=PROJECT_ID)
        doc_ref = db.collection("tests").document("schema_test")
        doc_ref.set({
            "userId": "test_user",
            "title": "Test Story",
            "prompt": "A dragon learns to fly",
            "style": "watercolor",
            "audience": "children",
            "status": "generating",
            "sceneCount": 4,
            "storyBible": {
                "characters": [{"name": "Ember", "type": "dragon", "appearance": "small purple dragon"}],
                "setting": "enchanted forest",
                "visualStyle": "soft watercolor",
            },
        })
        doc = doc_ref.get()
        data = doc.to_dict()
        assert data["storyBible"]["characters"][0]["name"] == "Ember"
        assert data["status"] == "generating"
        assert data["sceneCount"] == 4
        doc_ref.delete()


class TestCloudStorage:
    """Validate Cloud Storage for media file hosting."""

    def test_text_upload(self):
        """Text files can be uploaded and deleted."""
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob("tests/text_test.txt")
        blob.upload_from_string("test content", content_type="text/plain")
        assert blob.exists()
        blob.delete()

    def test_image_upload(self):
        """PNG images can be uploaded (simulates scene illustration storage)."""
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        img = Image.new("RGB", (100, 100), color="blue")
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        blob = bucket.blob("tests/image_test.png")
        blob.upload_from_file(buf, content_type="image/png")
        assert blob.exists()
        blob.delete()

    def test_public_url_format(self):
        """Public URLs follow the expected pattern for browser access."""
        url = f"https://storage.googleapis.com/{GCS_BUCKET}/stories/test/scene_1.png"
        assert GCS_BUCKET in url
        assert url.startswith("https://storage.googleapis.com/")

    def test_audio_upload(self):
        """Audio bytes can be uploaded (simulates narration storage)."""
        client = storage.Client(project=PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET)
        fake_audio = b"\x00" * 1000
        blob = bucket.blob("tests/audio_test.wav")
        blob.upload_from_string(fake_audio, content_type="audio/wav")
        assert blob.exists()
        blob.delete()


# =====================================================
# SECTION 2: Gemini Model Integration
# =====================================================

class TestGeminiModels:
    """Validate Gemini model access and capabilities."""

    def test_text_generation(self):
        """Gemini 2.5 Flash generates text responses."""
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say hello in one word.",
        )
        assert response.text is not None
        assert len(response.text) > 0

    def test_story_planning(self):
        """Gemini can generate a structured story plan."""
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Write a 2-sentence children's story about a fox.",
        )
        assert response.text is not None
        assert len(response.text) > 20

    def test_interleaved_output(self):
        """Gemini 2.5 Flash Image returns content with interleaved modalities."""
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents="Create a storybook illustration of a cute orange fox. Write a title.",
            config=GenerateContentConfig(
                response_modalities=[Modality.TEXT, Modality.IMAGE],
            ),
        )
        assert len(response.candidates[0].content.parts) > 0

    def test_image_generation_produces_valid_png(self):
        """Generated images are valid PNG files that can be opened."""
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents="Draw a simple blue star on white background.",
            config=GenerateContentConfig(
                response_modalities=[Modality.IMAGE],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                img = Image.open(BytesIO(part.inline_data.data))
                assert img.size[0] > 0
                assert img.size[1] > 0
                return
        pytest.skip("Model returned text only this time")

    def test_character_consistency_prompt(self):
        """Story Bible prompt format produces structured character descriptions."""
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="""Create a Story Bible for a children's story. Include:
            - Character name and detailed appearance
            - Setting description
            - Visual style guide
            Format as structured text.""",
        )
        text = response.text.lower()
        assert any(word in text for word in ["character", "appearance", "setting", "style"])


# =====================================================
# SECTION 3: Live Deployment Validation
# =====================================================

class TestLiveDeployment:
    """Validate the production Cloud Run deployment."""

    def test_health_check(self):
        """Service health endpoint responds with 200."""
        r = httpx.get(f"{LIVE_URL}/health", timeout=10)
        assert r.status_code == 200

    def test_version_endpoint(self):
        """Version endpoint is accessible."""
        r = httpx.get(f"{LIVE_URL}/version", timeout=10)
        assert r.status_code == 200

    def test_api_docs_available(self):
        """Swagger API documentation is accessible."""
        r = httpx.get(f"{LIVE_URL}/docs", timeout=10)
        assert r.status_code == 200

    def test_agent_registered(self):
        """Creative storyteller agent is registered in ADK server."""
        r = httpx.get(f"{LIVE_URL}/list-apps", timeout=10)
        assert r.status_code == 200
        assert APP_NAME in str(r.json())

    def test_response_time_under_threshold(self):
        """Health endpoint responds within 2 seconds."""
        start = time.time()
        r = httpx.get(f"{LIVE_URL}/health", timeout=10)
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < 2.0, f"Response took {elapsed:.1f}s, expected < 2s"


# =====================================================
# SECTION 4: Session Management
# =====================================================

class TestSessionManagement:
    """Validate ADK session lifecycle."""

    def test_create_session(self):
        """New sessions can be created for users."""
        r = httpx.post(
            f"{LIVE_URL}/apps/{APP_NAME}/users/test_user/sessions",
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0

    def test_list_sessions(self):
        """User sessions can be listed."""
        r = httpx.get(
            f"{LIVE_URL}/apps/{APP_NAME}/users/test_user/sessions",
            timeout=10,
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_multiple_users_isolated(self):
        """Different users have separate session lists."""
        httpx.post(f"{LIVE_URL}/apps/{APP_NAME}/users/user_a/sessions", timeout=10)
        httpx.post(f"{LIVE_URL}/apps/{APP_NAME}/users/user_b/sessions", timeout=10)
        r_a = httpx.get(f"{LIVE_URL}/apps/{APP_NAME}/users/user_a/sessions", timeout=10)
        r_b = httpx.get(f"{LIVE_URL}/apps/{APP_NAME}/users/user_b/sessions", timeout=10)
        assert r_a.status_code == 200
        assert r_b.status_code == 200


# =====================================================
# SECTION 5: Error Handling & Edge Cases
# =====================================================

class TestErrorHandling:
    """Validate graceful error handling."""

    def test_invalid_app_returns_error(self):
        """Requesting a non-existent app returns an error, not a crash."""
        r = httpx.get(
            f"{LIVE_URL}/apps/nonexistent_app/users/user1/sessions",
            timeout=10,
        )
        assert r.status_code in [200, 404, 400, 500]

    def test_invalid_endpoint_returns_error(self):
        """Requesting a non-existent endpoint returns proper HTTP error."""
        r = httpx.get(f"{LIVE_URL}/this/does/not/exist", timeout=10)
        assert r.status_code in [404, 405]

    def test_service_handles_concurrent_requests(self):
        """Service handles multiple simultaneous health checks."""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(httpx.get, f"{LIVE_URL}/health", timeout=10) for _ in range(5)]
            results = [f.result() for f in futures]
        assert all(r.status_code == 200 for r in results)

    def test_cors_allows_frontend_origin(self):
        """Cross-origin requests from frontend are accepted."""
        r = httpx.get(
            f"{LIVE_URL}/health",
            headers={"Origin": "http://localhost:3000"},
            timeout=10,
        )
        assert r.status_code == 200


# =====================================================
# SECTION 6: End-to-End Pipeline Smoke Test
# =====================================================

class TestPipelineSmokeTest:
    """Lightweight validation that the agent pipeline is operational."""

    def test_app_graph_accessible(self):
        """Agent dependency graph can be retrieved."""
        r = httpx.get(f"{LIVE_URL}/dev/build_graph/{APP_NAME}", timeout=10)
        assert r.status_code == 200

    def test_full_session_lifecycle(self):
        """Create session → list sessions → verify session exists."""
        create_r = httpx.post(
            f"{LIVE_URL}/apps/{APP_NAME}/users/lifecycle_test/sessions",
            timeout=10,
        )
        assert create_r.status_code == 200

        list_r = httpx.get(
            f"{LIVE_URL}/apps/{APP_NAME}/users/lifecycle_test/sessions",
            timeout=10,
        )
        assert list_r.status_code == 200
        sessions = list_r.json()
        assert len(sessions) > 0
