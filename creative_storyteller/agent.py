"""Creative Storyteller - Production Agent (Video Fix).

Fix: Veo client forces GOOGLE_CLOUD_LOCATION=global by temporarily
overriding the env var, preventing ADK's us-central1 from interfering.
"""
import os, uuid, time, logging, re
from io import BytesIO
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google import genai
from google.genai.types import GenerateContentConfig, Modality

logger = logging.getLogger(__name__)
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GCS_BUCKET = os.getenv("GCS_BUCKET", "")
ARTIST_MODEL = os.getenv("ARTIST_MODEL", "gemini-2.5-flash-image")
TTS_MODEL = os.getenv("TTS_MODEL", "gemini-2.5-flash-preview-tts")
STORY_ID = f"story_{uuid.uuid4().hex[:8]}"

def _gcs(data, fn, ct):
    try:
        from google.cloud import storage as gcs
        gcs.Client(project=PROJECT_ID).bucket(GCS_BUCKET).blob(fn).upload_from_string(data, content_type=ct)
        return f"https://storage.googleapis.com/{GCS_BUCKET}/{fn}"
    except Exception as e:
        logger.error(f"GCS: {e}"); return ""

def _make_veo_client():
    """Create Veo client with location=global.
    Temporarily overrides env var because ADK sets GOOGLE_CLOUD_LOCATION=us-central1."""
    original = os.environ.get("GOOGLE_CLOUD_LOCATION", "")
    try:
        os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
        return genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    finally:
        if original:
            os.environ["GOOGLE_CLOUD_LOCATION"] = original

def _poll(client, op, timeout=300):
    t = 0
    while not op.done and t < timeout:
        time.sleep(15); t += 15
        try: op = client.operations.get(op)
        except Exception as e:
            logger.error(f"Poll error at {t}s: {e}"); break
    return op

# === TOOL 1: Illustrations ===
def generate_scene_illustrations(story_plan: str) -> dict:
    """Generate illustrations using Gemini interleaved text+image output.
    Args: story_plan: Complete story text.
    Returns: dict with scene_images list."""
    client = genai.Client()
    try:
        resp = client.models.generate_content(model=ARTIST_MODEL,
            contents=f"Illustrate each scene. Caption then illustration. Keep characters consistent.\n\n{story_plan}",
            config=GenerateContentConfig(response_modalities=[Modality.TEXT, Modality.IMAGE]))
        if not resp or not resp.candidates: return {"scene_images": [], "error": "No response"}
        c = resp.candidates[0]
        if not c.content or not c.content.parts: return {"scene_images": [], "error": "Empty"}
        imgs, txt, n = [], "", 1
        for p in c.content.parts:
            if getattr(p, 'text', None): txt = p.text
            inl = getattr(p, 'inline_data', None)
            if inl and getattr(inl, 'data', None):
                url = ""
                if GCS_BUCKET and PROJECT_ID:
                    try:
                        from PIL import Image
                        img = Image.open(BytesIO(inl.data)); buf = BytesIO(); img.save(buf, format="PNG")
                        url = _gcs(buf.getvalue(), f"stories/{STORY_ID}/scene_{n}.png", "image/png")
                    except: pass
                if not url: url = f"[scene_{n}_img]"
                imgs.append({"scene_number": n, "image_url": url, "description": txt[:200]}); n += 1; txt = ""
        return {"scene_images": imgs, "total_images": len(imgs)}
    except Exception as e: return {"scene_images": [], "error": str(e)}

# === TOOL 2: 8-Second Videos ===
def generate_scene_videos(illustration_data: str) -> dict:
    """Generate 8-second cinematic video per scene using Veo 3.1 on location=global.
    Args: illustration_data: Text with GCS image URLs.
    Returns: dict with scene_videos list."""
    videos = []
    urls = re.findall(r'https://storage\.googleapis\.com/[^\s\'"}\]]+\.png', illustration_data)
    if not urls:
        return {"scene_videos": [], "note": "No images found"}

    logger.info("Creating Veo client (location=global)...")
    try:
        veo = _make_veo_client()
        logger.info("Veo client OK")
    except Exception as e:
        return {"scene_videos": [], "error": f"Veo client failed: {e}"}

    for i, img_url in enumerate(urls[:4], 1):
        try:
            logger.info(f"Scene {i}: Downloading {img_url}")
            import httpx
            resp = httpx.get(img_url, timeout=30)
            if resp.status_code != 200:
                videos.append({"scene_number": i, "video_url": None, "error": f"HTTP {resp.status_code}"}); continue

            logger.info(f"Scene {i}: Got {len(resp.content)} bytes. Calling Veo...")
            from google.genai.types import Image as GI
            op = veo.models.generate_videos(
                model="veo-3.1-generate-001",
                prompt=f"Gentle cinematic animation of storybook scene {i}. Soft camera pan, dreamlike, subtle character motion. Wind, leaves, birdsong. Soft orchestral music.",
                image=GI(image_bytes=resp.content, mime_type="image/png"))

            logger.info(f"Scene {i}: Op started, name={getattr(op, 'name', '?')}, done={op.done}")
            op = _poll(veo, op, timeout=300)
            logger.info(f"Scene {i}: Poll done. done={op.done}, result={op.result is not None}, error={getattr(op, 'error', None)}")

            if op.done and op.result and op.result.generated_videos:
                vb = op.result.generated_videos[0].video.video_bytes
                if vb and GCS_BUCKET:
                    url = _gcs(vb, f"stories/{STORY_ID}/scene_{i}_video.mp4", "video/mp4")
                    videos.append({"scene_number": i, "video_url": url, "duration": 8})
                    logger.info(f"Scene {i}: SAVED {url}")
                else:
                    videos.append({"scene_number": i, "video_url": None, "error": "No bytes"})
            else:
                # If image-to-video was safety blocked, try text-to-video instead
                err = getattr(op, 'error', None)
                if err and 'blocked' in str(err):
                    logger.info(f"Scene {i}: Safety blocked, trying text-to-video fallback...")
                    try:
                        op2 = veo.models.generate_videos(
                            model="veo-3.1-generate-001",
                            prompt=f"Cinematic storybook animation scene {i}. Cute animal characters in a magical setting. Soft camera pan, dreamlike atmosphere. Wind, birdsong, soft orchestral music.")
                        op2 = _poll(veo, op2, timeout=300)
                        if op2.done and op2.result and op2.result.generated_videos:
                            vb = op2.result.generated_videos[0].video.video_bytes
                            if vb and GCS_BUCKET:
                                url = _gcs(vb, f"stories/{STORY_ID}/scene_{i}_video.mp4", "video/mp4")
                                videos.append({"scene_number": i, "video_url": url, "duration": 8})
                                logger.info(f"Scene {i}: Text-to-video fallback SAVED: {url}")
                                continue
                    except Exception as fb_err:
                        logger.error(f"Scene {i}: Fallback also failed: {fb_err}")
                videos.append({"scene_number": i, "video_url": None, "note": f"Failed: {err}"})
        except Exception as e:
            logger.error(f"Scene {i}: {type(e).__name__}: {e}")
            videos.append({"scene_number": i, "video_url": None, "error": str(e)})

    return {"scene_videos": videos, "total_videos": len([x for x in videos if x.get("video_url")])}

# === TOOL 4: Merge Videos into One ===
def merge_scene_videos_into_one(video_data: str) -> dict:
    """Download all scene videos from GCS and merge them into one continuous video.
    Args: video_data: Text containing video URLs from video producer.
    Returns: dict with merged_video_url."""
    import tempfile, os
    urls = re.findall(r'https://storage\.googleapis\.com/[^\s\'"}\]]+\.mp4', video_data)
    if not urls:
        return {"merged_video_url": None, "error": "No video URLs found to merge"}

    logger.info(f"Merging {len(urls)} videos into one...")
    temp_files = []
    try:
        import httpx
        try:
            from moviepy import VideoFileClip, concatenate_videoclips
        except ImportError:
            from moviepy.editor import VideoFileClip, concatenate_videoclips

        # Download each video to a temp file
        for i, url in enumerate(urls):
            resp = httpx.get(url, timeout=60)
            if resp.status_code == 200:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_scene_{i+1}.mp4")
                tmp.write(resp.content)
                tmp.close()
                temp_files.append(tmp.name)
                logger.info(f"Downloaded scene {i+1}: {len(resp.content)} bytes")

        if not temp_files:
            return {"merged_video_url": None, "error": "No videos could be downloaded"}

        # Merge all clips
        clips = [VideoFileClip(f) for f in temp_files]
        final = concatenate_videoclips(clips, method="compose")

        # Write merged video
        output_path = tempfile.NamedTemporaryFile(delete=False, suffix="_merged.mp4").name
        final.write_videofile(output_path, codec="libx264", audio_codec="aac",
                            temp_audiofile=tempfile.mktemp(suffix=".m4a"), logger=None)

        # Close clips
        for c in clips:
            c.close()
        final.close()

        # Upload merged video to GCS
        with open(output_path, "rb") as f:
            merged_bytes = f.read()

        merged_url = ""
        if GCS_BUCKET and PROJECT_ID:
            fn = f"stories/{STORY_ID}/full_story_video.mp4"
            merged_url = _gcs(merged_bytes, fn, "video/mp4")

        logger.info(f"Merged video saved: {merged_url} ({len(merged_bytes)} bytes)")

        # Cleanup temp files
        for f in temp_files:
            try: os.unlink(f)
            except: pass
        try: os.unlink(output_path)
        except: pass

        total_duration = sum(c.duration for c in clips) if clips else 0
        return {
            "merged_video_url": merged_url,
            "total_duration_seconds": round(total_duration, 1),
            "scenes_merged": len(temp_files),
        }

    except Exception as e:
        logger.error(f"Merge failed: {e}")
        for f in temp_files:
            try: os.unlink(f)
            except: pass
        return {"merged_video_url": None, "error": str(e)}


# === TOOL 3: Narration ===
def generate_scene_narrations(story_text: str) -> dict:
    """Voice narration via Gemini TTS.
    Args: story_text: Story text.
    Returns: dict with narrations."""
    client = genai.Client(); narrs = []
    scenes = [s.strip() for s in story_text.split("---") if len(s.strip()) > 50]
    if not scenes: scenes = [story_text[:2000]]
    for i, sc in enumerate(scenes[:4], 1):
        try:
            r = client.models.generate_content(model=TTS_MODEL,
                contents=f"Read this story aloud with warmth:\n\n{sc[:1500]}",
                config=GenerateContentConfig(response_modalities=[Modality.AUDIO]))
            if not r or not r.candidates: narrs.append({"scene_number": i, "audio_url": None}); continue
            c = r.candidates[0]
            if not c.content or not c.content.parts: narrs.append({"scene_number": i, "audio_url": None}); continue
            ok = False
            for p in c.content.parts:
                inl = getattr(p, 'inline_data', None)
                if inl and getattr(inl, 'data', None):
                    m = getattr(inl, 'mime_type', 'audio/wav')
                    if 'audio' in str(m) and GCS_BUCKET:
                        narrs.append({"scene_number": i, "audio_url": _gcs(inl.data, f"stories/{STORY_ID}/narration_{i}.wav", m)}); ok = True; break
            if not ok: narrs.append({"scene_number": i, "audio_url": None})
        except Exception as e: narrs.append({"scene_number": i, "audio_url": None, "error": str(e)})
    return {"scene_narrations": narrs, "total": len(narrs)}

# === AGENTS ===
story_planner = Agent(name="StoryPlanner", model="gemini-2.5-flash",
    instruction="""Write a complete storybook with 4 scenes.

CRITICAL RULE: All characters MUST be animals, creatures, or fantasy beings (foxes, owls, dragons, rabbits, cats, etc).
Do NOT use human characters. This is required for our video generation pipeline.

Format:
STORY BIBLE:
Title: [title]
Characters: [detailed ANIMAL/CREATURE appearance - fur color, eye color, markings]
Setting: [setting]
Visual Style: [art style]
---
SCENE 1: [title]
[2-3 paragraphs]
---
SCENE 2: [title]
[2-3 paragraphs]
---
SCENE 3: [title]
[2-3 paragraphs]
---
SCENE 4: [title]
[2-3 paragraphs]
---""",
    description="Plans and writes the story", output_key="story_plan")

illustrator = Agent(name="Illustrator", model="gemini-2.5-flash",
    instruction="Read {story_plan}. Call generate_scene_illustrations ONCE with full text. Report all image URLs.",
    description="Scene illustrations", tools=[generate_scene_illustrations], output_key="illustration_results")

narrator = Agent(name="Narrator", model="gemini-2.5-flash",
    instruction="Read {story_plan}. Call generate_scene_narrations ONCE. If fails, say 'Audio not available'.",
    description="Voice narration", tools=[generate_scene_narrations], output_key="narration_results")

video_producer = Agent(name="VideoProducer", model="gemini-2.5-flash",
    instruction="""Read {illustration_results}. Call generate_scene_videos ONCE.
Each scene gets an 8-second cinematic video with AI audio. Takes 1-2 min per scene.
Report all video URLs when done.""",
    description="8-second Veo 3.1 videos",
    tools=[generate_scene_videos], output_key="video_results")

video_merger = Agent(name="VideoMerger", model="gemini-2.5-flash",
    instruction="""Read {video_results}. Call merge_scene_videos_into_one ONCE with that text.
This will download all scene videos and combine them into ONE continuous story video.
Report the merged video URL.""",
    description="Merges scene videos into one",
    tools=[merge_scene_videos_into_one], output_key="merged_video")


assembler = Agent(name="StoryAssembler", model="gemini-2.5-flash",
    instruction="""Present the complete story:
- Story: {story_plan}
- Illustrations: {illustration_results}
- Individual scene videos: {video_results}
- FULL MERGED VIDEO: {merged_video}
- Narration: {narration_results}

Start with:
## [Story Title]
**Complete Story Video:** [merged_video URL from merged_video results]

Then for EACH scene:
### Scene [N]: [Title]
[Narrative text]
**Illustration:** [image URL]
**Scene clip:** [video URL]
---
End with production summary. COPY actual URLs.""",
    description="Final presentation")

# === PIPELINE ===
parallel_media = ParallelAgent(name="MediaProduction", sub_agents=[illustrator, narrator])
root_agent = SequentialAgent(name="CreativeStorytellerPipeline",
    sub_agents=[story_planner, parallel_media, video_producer, video_merger, assembler],
    description="Multimodal storytelling with merged final video.")