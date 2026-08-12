#!/usr/bin/env python3
"""
Generate photorealistic architectural window styles through Gemini models.
"""

import base64
import json
import os
import urllib.error
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE_PATH = os.environ.get(
    "WINDOWS_VISUALIZER_INPUT",
    os.path.join(PROJECT_DIR, "demo_room_generated.jpg")
)
SAMPLE_DIR = os.environ.get("WINDOWS_VISUALIZER_ASSET_DIR", PROJECT_DIR)

CANDIDATE_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3-pro-image",
    "gemini-3.1-flash-lite-image",
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image"
]


def load_image_base64(path: str) -> str:
    with open(path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def generate_window_render(style_name: str, style_desc: str, output_path: str):
    if not API_KEY:
        raise RuntimeError("Set GEMINI_API_KEY before running this script.")

    print(f"\n[*] Generating photorealistic {style_name}...")
    image_base64 = load_image_base64(INPUT_IMAGE_PATH)
    prompt = (
        f"Photorealistic architectural photo of the room from the reference image, replacing "
        f"the existing window with an authentic {style_desc}. "
        "The window blinds are completely retracted and open, revealing clear glass and lush "
        "outdoor green garden trees with natural daylight. The window frame casing, window sill, "
        "sashes, and grilles have realistic architectural wood texture painted in uniform magenta "
        "pink (#FF00FF). Maintain natural shadows and strict anti-glare separation from the room."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}
            ]
        }],
        "generationConfig": {"response_mime_type": "image/jpeg"}
    }

    for model in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY}
        )
        try:
            print(f"  -> Trying model: {model}...")
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                    inline_data = part.get("inline_data", {})
                    if inline_data.get("data"):
                        with open(output_path, "wb") as output:
                            output.write(base64.b64decode(inline_data["data"]))
                        print(f"[+] Generated with {model} -> {output_path}")
                        return True
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8")
            print(f"  [-] Model {model} returned HTTP {error.code}: {body[:200]}")
        except Exception as error:
            print(f"  [-] Model {model} failed: {error}")

    return False


if __name__ == "__main__":
    output = os.path.join(SAMPLE_DIR, "test_photorealistic_awning.jpg")
    generate_window_render(
        "Awning Window",
        "Awning Window (hinged at the top, opening outward at an angle from the bottom)",
        output
    )
