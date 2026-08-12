#!/usr/bin/env python3
"""
Test Google AI Studio Models for Photorealistic Image Generation
"""

import os
import json
import urllib.request

API_KEY = os.environ.get("GEMINI_API_KEY")


def list_available_models():
    if not API_KEY:
        raise RuntimeError("Set GEMINI_API_KEY before running this script.")

    url = "https://generativelanguage.googleapis.com/v1beta/models"
    try:
        req = urllib.request.Request(url, headers={"x-goog-api-key": API_KEY})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(f"[+] Total models available: {len(data.get('models', []))}")
            for model in data.get("models", []):
                name = model.get("name")
                methods = model.get("supportedGenerationMethods", [])
                if "generateImages" in methods or "image" in name.lower() or "imagen" in name.lower():
                    print(f"  {name} | Methods: {methods}")
    except Exception as error:
        print(f"[-] Error listing models: {error}")


if __name__ == "__main__":
    list_available_models()
