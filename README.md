# Creative Storyteller

### Multimodal AI Storytelling — Text, Images, Video & Audio in One Fluid Experience

Creative Storyteller is a production-grade AI storytelling platform that breaks the "text box" paradigm. Instead of generating text in one tool, images in another, and video somewhere else, it produces a **complete illustrated, animated, and narrated storybook** from a single prompt — all powered by Google's AI stack.

**Give it a prompt like:**
> *"Create a storybook about a brave little fox named Luna who discovers a hidden garden of glowing flowers in a moonlit forest"*

**And it produces:**
- 📖 A 4-scene narrative with rich prose
- 🎨 AI-generated illustrations for each scene (Gemini Nano Banana interleaved output)
- 🎬 8-second cinematic video clips per scene with AI-generated ambient audio (Veo 3.1)
- 🔊 Voice narration per scene (Gemini TTS)
- 🎞️ One merged final video combining all scene clips into a continuous story

---

## Live Demo

**Deployed URL:** `https://creative-storyteller-XXXXX-uc.a.run.app`
*(Replace with actual Cloud Run URL after deployment)*

---

## Architecture

```
User Prompt
    │
    ▼
┌──────────────────────────────────────────────────────────┐
│              SequentialAgent Pipeline (ADK)                │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Step 1: STORY PLANNER (gemini-2.5-flash)           │  │
│  │  Writes story bible + 4-scene narrative              │  │
│  │  Output → state["story_plan"]                        │  │
│  └──────────────────────┬──────────────────────────────┘  │
│                         ▼                                  │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Step 2: PARALLEL MEDIA PRODUCTION                    │ │
│  │  ┌──────────────────┐  ┌───────────────────────────┐  │ │
│  │  │ ILLUSTRATOR      │  │ NARRATOR                  │  │ │
│  │  │ Nano Banana      │  │ Gemini TTS                │  │ │
│  │  │ text+image       │  │ voice audio               │  │ │
│  │  │ interleaved      │  │ (optional)                │  │ │
│  │  └────────┬─────────┘  └─────────────┬─────────────┘  │ │
│  │           ▼                           ▼                │ │
│  │  state["illustration_results"]  state["narration"]     │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Step 3: VIDEO PRODUCER (Veo 3.1, location=global)   │  │
│  │  Animates each illustration → 8s cinematic clips     │  │
│  │  with AI-generated ambient audio & music             │  │
│  │  Output → state["video_results"]                     │  │
│  └──────────────────────┬──────────────────────────────┘  │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Step 4: VIDEO MERGER (MoviePy)                      │  │
│  │  Downloads all scene clips → merges into one MP4     │  │
│  │  Output → state["merged_video"]                      │  │
│  └──────────────────────┬──────────────────────────────┘  │
│                         ▼                                  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Step 5: STORY ASSEMBLER (gemini-2.5-flash)          │  │
│  │  Reads all state → presents final story with URLs    │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
    │
    ▼
Complete Story: text + images + videos + audio + merged video
All assets stored on Google Cloud Storage with public URLs
```

### Multi-Agent Communication

Agents communicate through **shared session state** — the official ADK pattern:

| Agent | Reads from state | Writes to state |
|-------|-----------------|-----------------|
| StoryPlanner | user prompt | `story_plan` |
| Illustrator | `story_plan` | `illustration_results` |
| Narrator | `story_plan` | `narration_results` |
| VideoProducer | `illustration_results` | `video_results` |
| VideoMerger | `video_results` | `merged_video` |
| StoryAssembler | all 5 keys above | final presentation |

---

## Google Tech Stack

Every component uses **Google Cloud / Google AI exclusively**:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Agent Framework** | Google ADK (Agent Development Kit) | Multi-agent orchestration with SequentialAgent + ParallelAgent |
| **Story Writing** | Gemini 2.5 Flash | Narrative text generation and agent reasoning |
| **Illustrations** | Gemini 2.5 Flash Image (Nano Banana) | Native interleaved text+image generation |
| **Video Generation** | Veo 3.1 (`veo-3.1-generate-001`) | Image-to-video animation with native AI audio |
| **Voice Narration** | Gemini 2.5 Flash Preview TTS | Text-to-speech audio generation |
| **Video Merging** | MoviePy (FFmpeg) | Concatenates scene clips into final video |
| **Deployment** | Google Cloud Run | Serverless container hosting |
| **Media Storage** | Google Cloud Storage (GCS) | Images, videos, audio assets |
| **Auth (planned)** | Firebase Authentication | User login |
| **Database (planned)** | Cloud Firestore | Story persistence and user data |
| **Monitoring** | Cloud Logging + Cloud Trace | Observability |
| **AI Platform** | Vertex AI | Model serving backend |

### Key Technical Differentiators

1. **Native Interleaved Output**: Uses Gemini's `response_modalities=[Modality.TEXT, Modality.IMAGE]` to generate text and illustrations together in a single API call — not separate text and image calls stitched together.

2. **Veo 3.1 Image-to-Video**: Animates static illustrations into 8-second cinematic clips with AI-generated ambient audio (wind, birdsong, orchestral music). Requires `location=global` on Vertex AI.

3. **Multi-Agent Pipeline**: Not a monolithic prompt — five specialist agents with clear responsibilities communicating through shared state.

4. **Parallel Execution**: Illustration and narration generation run concurrently via `ParallelAgent`, cutting total generation time.

5. **Graceful Degradation**: If video fails, you still get text + images. If audio fails, you still get text + images + video. The story never breaks completely.

---

## Project Structure

```
clean-project/
├── creative_storyteller/
│   ├── __init__.py          # ADK package init: from . import agent
│   ├── agent.py             # All agents, tools, and pipeline definition
│   └── .env                 # Environment config (not in git)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Cloud Run container definition
├── .dockerignore            # Files excluded from container
├── .gitignore               # Files excluded from git
└── README.md                # This file
```

**Why one file?** ADK expects a simple structure: one folder, one `agent.py`, one `root_agent` variable. Complex multi-folder structures with relative imports break ADK's agent loader. All tools are defined as functions in `agent.py` and registered via `FunctionTool` on the agents that use them.

---

## Setup Guide

### Prerequisites

- Python 3.11+
- Google Cloud account with billing enabled
- Google Cloud SDK (`gcloud` CLI) installed and authenticated
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/creative-storyteller.git
cd creative-storyteller
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Google Cloud Project Setup

```bash
# Set your project
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  logging.googleapis.com

# Create service account
gcloud iam service-accounts create storyteller-agent \
  --display-name="Creative Storyteller Agent"

SA_EMAIL="storyteller-agent@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant permissions
for ROLE in roles/aiplatform.user roles/storage.objectAdmin roles/logging.logWriter; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SA_EMAIL}" --role="$ROLE" --quiet
done

# Create storage bucket
gsutil mb -l us-central1 gs://${PROJECT_ID}-media
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-media

# Authenticate locally
gcloud auth application-default login
```

### Step 4: Configure Environment

Create `creative_storyteller/.env`:

```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GCS_BUCKET=your-project-id-media
ARTIST_MODEL=gemini-2.5-flash-image
TTS_MODEL=gemini-2.5-flash-preview-tts
```

### Step 5: Run Locally

```bash
# From the clean-project/ directory (NOT from inside creative_storyteller/)
python -c "from google.adk.cli import main; main()" web creative_storyteller
```

Open `http://127.0.0.1:8000` in your browser. Select `creative_storyteller` from the dropdown.

### Step 6: Test with a Prompt

Try:
> "Create a storybook about a brave little fox named Luna who discovers a hidden garden of glowing flowers in a moonlit forest"

**Important:** Use animal/creature characters (fox, owl, dragon, rabbit), not humans. Veo's safety filter blocks human face animation.

---

## Deployment to Google Cloud Run

```bash
gcloud run deploy creative-storyteller \
  --source . \
  --region us-central1 \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --memory 4Gi \
  --timeout 900 \
  --cpu 2 \
  --concurrency 5 \
  --service-account $SA_EMAIL \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GCS_BUCKET=${PROJECT_ID}-media,ARTIST_MODEL=gemini-2.5-flash-image,TTS_MODEL=gemini-2.5-flash-preview-tts"
```

Deployment takes 5-10 minutes. The output includes a public URL.

---

## Cost Estimation

| Component | Cost per story (4 scenes) |
|-----------|--------------------------|
| Gemini 2.5 Flash (text) | ~$0.01 |
| Nano Banana (illustrations) | ~$0.05 |
| Veo 3.1 (4 × 8s video) | ~$12.80 |
| Gemini TTS (narration) | ~$0.02 |
| Cloud Storage | ~$0.01 |
| Cloud Run | ~$0.01 |
| **Total per story** | **~$12.90** |

With $75 in credits, you can generate approximately **5-6 complete stories** with video.

---

## Sample Output

A single story generation produces:

| Asset | Format | Example URL |
|-------|--------|-------------|
| Scene 1 illustration | PNG | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/scene_1.png` |
| Scene 1 video (8s) | MP4 | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/scene_1_video.mp4` |
| Scene 2 illustration | PNG | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/scene_2.png` |
| Scene 2 video (8s) | MP4 | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/scene_2_video.mp4` |
| Scene 3 illustration | PNG | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/scene_3.png` |
| Scene 3 video (8s) | MP4 | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/scene_3_video.mp4` |
| Full merged video | MP4 | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/full_story_video.mp4` |
| Voice narration | WAV | `https://storage.googleapis.com/BUCKET/stories/STORY_ID/narration_1.wav` |

All URLs are publicly accessible and playable directly in the browser.

---

## Generation Timeline

| Step | Duration | What happens |
|------|----------|-------------|
| Story planning | ~30 seconds | Gemini writes story bible + 4-scene narrative |
| Illustrations | ~30 seconds | Nano Banana generates 3-4 scene images |
| Narration | ~15 seconds | Gemini TTS generates voice audio (parallel with illustrations) |
| Video generation | ~5-8 minutes | Veo 3.1 creates 8s cinematic clip per scene |
| Video merging | ~30 seconds | MoviePy concatenates clips into one video |
| Assembly | ~10 seconds | Final agent presents everything with URLs |
| **Total** | **~7-10 minutes** | Complete multimodal story |

---

## Known Limitations

1. **Veo safety filter blocks human faces.** Use animal or fantasy characters only. Human characters in illustrations will cause video generation to fail silently.

2. **TTS may return 400 on Vertex AI.** The `gemini-2.5-flash-preview-tts` model has intermittent issues on Vertex AI. Narration is treated as optional — the story works without it.

3. **Veo requires `location=global`.** The Veo video generation API only works with the `global` location on Vertex AI, not `us-central1`. The agent handles this automatically by creating a separate client.

4. **Video generation is slow.** Each 8-second Veo clip takes 1-2 minutes. A 4-scene story takes 5-8 minutes for video alone. This is a Veo API limitation, not a code issue.

5. **ADK dev UI doesn't render media.** The ADK web interface shows text output only — images, videos, and audio appear as URLs. The actual media is accessible by opening the URLs in a browser.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `adk: command not found` | Use `python -c "from google.adk.cli import main; main()" web creative_storyteller` instead |
| Videos all "Timed out" | Check that `GOOGLE_CLOUD_LOCATION` is being overridden to `global` for Veo calls (see `_make_veo_client()` in agent.py) |
| Videos "blocked by safety settings" | Your illustrations contain human faces. Use animal characters only |
| TTS returns 400 | Known Vertex AI issue with TTS preview models. Narration is optional — story works without it |
| `No module named 'creative_storyteller'` | Make sure you're running from the parent directory (`clean-project/`), not from inside `creative_storyteller/` |
| Illustrations return empty | Check GCS bucket permissions: `gsutil iam ch allUsers:objectViewer gs://BUCKET` |
| Cloud Run deploy stuck | First deploy creates Artifact Registry, takes 10-15 minutes. Check Cloud Build logs in GCP Console |

---

## Competition: Judging Criteria Mapping

### Innovation & Multimodal UX (40%)
- Breaks the text-box paradigm: story flows as text → illustrations → video → audio
- Single prompt produces a complete multimodal experience
- Gemini's native interleaved output keeps narrative and visuals coherent
- Veo 3.1 adds cinematic motion and AI-generated ambient audio

### Technical Implementation & Agent Architecture (30%)
- Google ADK multi-agent system: SequentialAgent + ParallelAgent
- 5 specialist agents communicating through shared session state
- Graceful degradation: no single failure breaks the story
- Retry logic with exponential backoff on API calls
- Cloud-native: Vertex AI, Cloud Storage, Cloud Run

### Demo & Presentation (30%)
- Working deployed URL on Google Cloud Run
- Real-time generation visible in ADK web UI
- All assets stored on GCS with public URLs
- Architecture diagram showing agent pipeline

---

## Tech References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [ADK Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [Gemini Nano Banana Image Generation](https://ai.google.dev/gemini-api/docs/image-generation)
- [Veo 3.1 Video Generation](https://ai.google.dev/gemini-api/docs/video)
- [Veo on Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/video/overview)
- [ADK Cloud Run Deployment](https://google.github.io/adk-docs/deploy/cloud-run/)
- [Google GenAI SDK](https://github.com/google/generative-ai-python)

---

## Contributors

- [Your Name] — Backend / AI Agents
- [Partner 1] — Frontend
- [Partner 2] — DevOps / QA

---

## License

Built for the Google AI Hackathon 2026.
