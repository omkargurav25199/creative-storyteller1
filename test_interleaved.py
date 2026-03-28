import os
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ["GOOGLE_CLOUD_PROJECT"] = "hailmary-491613"
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

from google import genai
from google.genai.types import GenerateContentConfig, Modality
from io import BytesIO

client = genai.Client()

print("Testing Gemini interleaved text+image output...")
print("This may take 10-30 seconds...\n")

response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents="Draw a cute orange fox sitting in a moonlit forest. Include a short description.",
    config=GenerateContentConfig(
        response_modalities=[Modality.TEXT, Modality.IMAGE],
    ),
)

text_found = False
image_found = False

for part in response.candidates[0].content.parts:
    if part.text:
        print(f"TEXT received: {part.text[:100]}...")
        text_found = True
    elif part.inline_data:
        print(f"IMAGE received: {len(part.inline_data.data)} bytes, type: {part.inline_data.mime_type}")
        image_found = True
        from PIL import Image
        img = Image.open(BytesIO(part.inline_data.data))
        img.save("test_output.png")
        print(f"Image saved as test_output.png ({img.size[0]}x{img.size[1]})")

if text_found and image_found:
    print("\nSUCCESS! Interleaved output is working. You're ready to build.")
elif text_found and not image_found:
    print("\nText works but no image. Try a different model.")
else:
    print("\nFAILURE. Check your authentication and project setup.")
