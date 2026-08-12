#!/usr/bin/env python3
"""
Test Imagen Predict API on Google AI Studio.
"""

import os
import json
import base64
import urllib.request
import urllib.error

API_KEY = os.environ.get("GEMINI_API_KEY")
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE_PATH = os.environ.get(
    "WINDOWS_VISUALIZER_INPUT",
    os.path.join(PROJECT_DIR, "demo_room_generated.jpg")
)
SAMPLE_DIR = os.environ.get("WINDOWS_VISUALIZER_ASSET_DIR", PROJECT_DIR)

IMAGEN_MODELS = [
    "imagen-3.0-generate-002",
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001",
    "imagen-4.0-ultra-generate-001"
]


def test_imagen_predict(model_name: str, prompt: str, out_path: str):
    if not API_KEY:
        raise RuntimeError("Set GEMINI_API_KEY before running this script.")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:predict"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": 1, "aspectRatio": "4:3"}
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": API_KEY}
    )

    try:
        print(f"[*] Testing {model_name}...")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            predictions = data.get("predictions", [])
            if predictions:
                encoded = predictions[0].get("bytesBase64Encoded")
                if encoded:
                    with open(out_path, "wb") as output:
                        output.write(base64.b64decode(encoded))
                    print(f"[+] Successfully generated image with {model_name} -> {out_path}")
                    return True
    except urllib.error.HTTPError as error:
        print(f"[-] {model_name} HTTP {error.code}: {error.read().decode('utf-8')[:200]}")
    except Exception as error:
        print(f"[-] {model_name} failed: {error}")
    return False


if __name__ == "__main__":
    prompt = "Photorealistic architectural interior of a residential living room with a bay window, natural wood grain casing, sunlight, and green garden outside."
    for model in IMAGEN_MODELS:
        if test_imagen_predict(model, prompt, os.path.join(SAMPLE_DIR, f"test_{model}.jpg")):
            break
