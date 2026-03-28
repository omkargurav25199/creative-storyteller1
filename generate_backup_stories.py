"""Generate 2 backup stories for demo day. Run this before the presentation."""

import os
import json
import time
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

from google import genai
from google.genai.types import GenerateContentConfig, Modality
from io import BytesIO
from PIL import Image

client = genai.Client()

BACKUP_STORIES = [
    {
        "name": "dragon_flowers",
        "prompt": """Create an illustrated storybook with 3 scenes.

Story: A tiny purple dragon named Ember discovers she can grow flowers instead of breathing fire. 
Style: soft watercolor, warm golden tones, storybook illustration.
Audience: children aged 5-8.

IMPORTANT: For each scene, write 2-3 sentences of narrative text, then generate one illustration showing that scene. Keep Ember's appearance consistent: small purple dragon with golden eyes, tiny wings, and a flower-shaped mark on her forehead.

Scene 1: Ember tries to breathe fire like the other dragons but flowers bloom from her mouth instead. She feels embarrassed.
Scene 2: Ember discovers her flowers can heal a sick forest animal. She starts to see her gift differently.
Scene 3: All the dragons gather to see Ember's garden. She's proud of who she is.""",
    },
    {
        "name": "moonlit_fox",
        "prompt": """Create an illustrated storybook with 3 scenes.

Story: A brave little fox named Luna follows glowing lantern flowers through a moonlit forest to find a lost star.
Style: soft watercolor, cool blue and silver tones with warm lantern glows, storybook illustration.
Audience: children aged 5-8.

IMPORTANT: For each scene, write 2-3 sentences of narrative text, then generate one illustration showing that scene. Keep Luna's appearance consistent: small orange fox with bright green eyes and a fluffy white-tipped tail.

Scene 1: Luna discovers a trail of glowing lantern flowers in the forest at night. She decides to follow them.
Scene 2: The trail leads Luna across a sparkling stream and through a grove of ancient trees. She meets a wise owl who tells her a star fell nearby.
Scene 3: Luna finds the fallen star in a meadow. She nudges it gently with her nose and it floats back up to the sky, lighting up the whole forest.""",
    },
]

os.makedirs("backup_stories", exist_ok=True)

for story in BACKUP_STORIES:
    print(f"\n{'='*60}")
    print(f"Generating: {story['name']}")
    print(f"{'='*60}")
    print("This may take 30-60 seconds...\n")

    start = time.time()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=story["prompt"],
            config=GenerateContentConfig(
                response_modalities=[Modality.TEXT, Modality.IMAGE],
            ),
        )

        story_dir = f"backup_stories/{story['name']}"
        os.makedirs(story_dir, exist_ok=True)

        text_parts = []
        image_count = 0

        for part in response.candidates[0].content.parts:
            if part.text:
                text_parts.append(part.text)
                print(f"TEXT: {part.text[:80]}...")
            elif part.inline_data:
                image_count += 1
                img = Image.open(BytesIO(part.inline_data.data))
                img_path = f"{story_dir}/scene_{image_count}.png"
                img.save(img_path)
                print(f"IMAGE saved: {img_path} ({img.size[0]}x{img.size[1]})")

        # Save the full text
        with open(f"{story_dir}/story.txt", "w", encoding="utf-8") as f:
            f.write("\n\n".join(text_parts))

        elapsed = time.time() - start
        print(f"\nDone! {len(text_parts)} text blocks + {image_count} images in {elapsed:.1f}s")

    except Exception as e:
        print(f"ERROR generating {story['name']}: {e}")
        print("You can retry this script later.")

print(f"\n{'='*60}")
print("Backup stories saved in backup_stories/ folder")
print("Open the images to verify they look good!")
print(f"{'='*60}")
