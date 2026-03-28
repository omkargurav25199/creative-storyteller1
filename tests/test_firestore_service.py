"""Firestore service tests — validates all CRUD operations."""

import os
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"

import pytest
from google.cloud import firestore
from creative_storyteller.tools.firestore_service import (
    create_story,
    update_story_meta,
    save_scene,
    complete_story,
    fail_story,
    get_story,
)


@pytest.fixture
def cleanup_story():
    """Fixture that cleans up test stories after each test."""
    story_ids = []
    yield story_ids
    db = firestore.Client(project="hailmary-491613")
    for sid in story_ids:
        # Delete scenes subcollection
        scenes = db.collection("stories").document(sid).collection("scenes").stream()
        for scene in scenes:
            scene.reference.delete()
        # Delete story
        db.collection("stories").document(sid).delete()


def test_create_story(cleanup_story):
    """Story creation returns a valid ID and sets correct fields."""
    story_id = create_story(
        user_id="test_user",
        prompt="A cat learns to paint",
        style="watercolor",
        audience="children",
        num_scenes=4,
    )
    cleanup_story.append(story_id)
    assert story_id is not None
    assert len(story_id) > 0

    story = get_story(story_id)
    assert story["prompt"] == "A cat learns to paint"
    assert story["style"] == "watercolor"
    assert story["audience"] == "children"
    assert story["status"] == "generating"
    assert story["sceneCount"] == 4


def test_update_story_meta(cleanup_story):
    """Story metadata can be updated with title and story bible."""
    story_id = create_story("test_user", "test", "comic", "teens", 3)
    cleanup_story.append(story_id)

    story_bible = {
        "characters": [{"name": "Luna", "type": "fox", "appearance": "orange fur"}],
        "setting": "moonlit forest",
        "visualStyle": "soft watercolor",
    }
    update_story_meta(story_id, "Luna's Adventure", story_bible)

    story = get_story(story_id)
    assert story["title"] == "Luna's Adventure"
    assert story["storyBible"]["characters"][0]["name"] == "Luna"
    assert story["storyBible"]["setting"] == "moonlit forest"


def test_save_scene(cleanup_story):
    """Scenes are saved correctly as subcollections."""
    story_id = create_story("test_user", "test", "anime", "adults", 2)
    cleanup_story.append(story_id)

    save_scene(
        story_id=story_id,
        scene_number=1,
        text="Luna stepped into the forest...",
        image_url="https://storage.googleapis.com/test/scene1.png",
        audio_url="https://storage.googleapis.com/test/scene1.wav",
    )

    story = get_story(story_id)
    assert len(story["scenes"]) == 1
    assert story["scenes"][0]["text"] == "Luna stepped into the forest..."
    assert story["scenes"][0]["imageUrl"] is not None
    assert story["scenes"][0]["audioUrl"] is not None
    assert story["scenes"][0]["status"] == "completed"


def test_save_scene_without_image(cleanup_story):
    """Scene without image is marked as image_failed."""
    story_id = create_story("test_user", "test", "storybook", "children", 2)
    cleanup_story.append(story_id)

    save_scene(story_id=story_id, scene_number=1, text="The sun rose slowly...")

    story = get_story(story_id)
    assert story["scenes"][0]["status"] == "image_failed"
    assert story["scenes"][0]["imageUrl"] is None


def test_multiple_scenes_ordered(cleanup_story):
    """Multiple scenes are returned in correct order."""
    story_id = create_story("test_user", "test", "comic", "teens", 3)
    cleanup_story.append(story_id)

    save_scene(story_id, 3, "Third scene text")
    save_scene(story_id, 1, "First scene text")
    save_scene(story_id, 2, "Second scene text")

    story = get_story(story_id)
    assert len(story["scenes"]) == 3
    assert story["scenes"][0]["text"] == "First scene text"
    assert story["scenes"][1]["text"] == "Second scene text"
    assert story["scenes"][2]["text"] == "Third scene text"


def test_complete_story(cleanup_story):
    """Story status changes to completed."""
    story_id = create_story("test_user", "test", "watercolor", "children", 2)
    cleanup_story.append(story_id)

    complete_story(story_id)

    story = get_story(story_id)
    assert story["status"] == "completed"


def test_fail_story(cleanup_story):
    """Story status changes to error with message."""
    story_id = create_story("test_user", "test", "watercolor", "children", 2)
    cleanup_story.append(story_id)

    fail_story(story_id, "Gemini API timeout")

    story = get_story(story_id)
    assert story["status"] == "error"
    assert story["error"] == "Gemini API timeout"


def test_get_nonexistent_story():
    """Getting a story that doesn't exist returns None."""
    result = get_story("this_story_does_not_exist_at_all")
    assert result is None
