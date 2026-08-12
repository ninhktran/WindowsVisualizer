# Windows Visualizer

Browser prototype for visualizing window replacements inside a room photo, rendered by Gemini.

## What works now

- Room-photo upload with drag and drop, sent to the local FastAPI server.
- Ten window styles: awning, bay, bow, casement, double-hung, garden, hopper, picture, sliding, and specialty.
- Eleven catalog finishes plus a custom color picker.
- Client-side chroma-key replacement with luminance preservation.
- Before/after split view.
- PNG export.
- Responsive desktop and mobile layout.

## How it works

The FastAPI server is required; there is no bundled-demo mode. The browser never receives an AI API key.

```text
Room photo -> Gemini vision (window polygon + confidence) -> Gemini image model (magenta-key window render) -> client-side finish shader -> export
```

With `GEMINI_API_KEY` configured, the server analyzes the room, then generates each window style in place. When a model is unavailable it falls back to deterministic geometry drawn server-side, still rendering through the same pipeline.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m uvicorn server.main:app --reload --port 8000
```

Open `http://localhost:8000`.

The server serves the studio UI; the static fallback is not supported.

## Optional AI scripts

Python generation scripts require a new Gemini key supplied through the environment. Never put the key in source code or frontend JavaScript.

```bash
export GEMINI_API_KEY="your-new-key"
python3 -m uvicorn server.main:app --reload --port 8000
```

Optional model overrides:

```bash
export GEMINI_MODEL="gemini-2.5-flash"
export GEMINI_IMAGE_MODEL="gemini-2.5-flash-image"
```

Install optional image-processing dependencies only when running the Python tools:

```bash
python3 -m pip install numpy pillow
```

## Roadmap

1. Add confidence and review states so users can correct the detected window region.
2. Add asynchronous job progress for slow image-generation providers.
3. Expand from one front-facing window to multiple windows and perspective-aware bay/bow geometry.
4. Keep finish swaps local in the browser for instant color exploration.
5. Never expose API keys or raw customer photos.
