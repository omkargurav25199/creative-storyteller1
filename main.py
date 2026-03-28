import os
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "hailmary-491613")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "TRUE")
os.environ.setdefault("GCS_BUCKET", "hailmary-491613-media")

from google.adk.cli.fast_api import get_fast_api_app
app = get_fast_api_app(agents_dir=".", web=True)