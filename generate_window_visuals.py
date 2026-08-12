#!/usr/bin/env python3
"""
Generate a small set of AI-assisted architectural window visuals.
"""

import base64
import json
import os
import urllib.error
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE = os.environ.get(
    "WINDOWS_VISUALIZER_INPUT",
    os.path.join(OUTPUT_DIR, "demo_room_generated.jpg")
)


def analyze_input_image(image_path: str):
    """Analyze an input room image with Gemini Vision."""
    if not API_KEY:
        raise RuntimeError("Set GEMINI_API_KEY before running this script.")
    if not os.path.exists(image_path):
        print(f"[!] Warning: {image_path} not found.")
        return None

    with open(image_path, "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    prompt = (
        "Analyze this room and window carefully. Extract the wall color, trim wood type, "
        "flooring, lighting, and exterior foliage, then provide architectural specifications "
        "for replacing this standard window with a bay or bow window."
    )
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_base64}}
            ]
        }]
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY}
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
            analysis = data["candidates"][0]["content"]["parts"][0]["text"]
            print("[+] Vision analysis complete.")
            return analysis
    except urllib.error.HTTPError as error:
        print(f"[!] Vision API response: {error.code} ({error.reason})")
        return None


def main():
    print("=" * 60)
    print("  Architectural Window Visualization Engine")
    print("=" * 60)
    print(f"Target directory : {OUTPUT_DIR}")
    print(f"Input image      : {INPUT_IMAGE}")

    files = [
        name for name in os.listdir(OUTPUT_DIR)
        if name.endswith((".jpg", ".jpeg", ".png", ".html"))
    ]
    print("\nExisting visualizations:")
    for name in sorted(files):
        print(f"  - {name}")

    print("\nTo view the interactive prototype:")
    print(f"  open {os.path.join(OUTPUT_DIR, 'index.html')}")


if __name__ == "__main__":
    main()
