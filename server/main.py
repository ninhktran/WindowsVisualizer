from __future__ import annotations

import base64
import io
import json
import os
import secrets
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageDraw, ImageOps
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = Path(
    os.environ.get(
        "WINDOWS_VISUALIZER_DATA_DIR",
        str(Path(tempfile.gettempdir()) / "windows-visualizer")
    )
)
DATA_ROOT.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PIXELS = 20_000_000
JOB_TTL_SECONDS = 60 * 60
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
STYLE_KEYS = {
    "awning",
    "bay",
    "bow",
    "casement",
    "double_hung",
    "garden",
    "hopper",
    "picture",
    "sliding",
    "specialty",
}

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_IMAGE_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")

jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()

app = FastAPI(title="Windows Visualizer API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class Point(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class RenderRequest(BaseModel):
    style: str
    polygon: Optional[List[Point]] = None
    use_ai: bool = True


def cleanup_jobs() -> None:
    cutoff = time.time() - JOB_TTL_SECONDS
    expired: list[str] = []
    with jobs_lock:
        for job_id, job in jobs.items():
            if job["created_at"] < cutoff:
                expired.append(job_id)
        for job_id in expired:
            jobs.pop(job_id, None)
    for job_id in expired:
        shutil.rmtree(DATA_ROOT / job_id, ignore_errors=True)


def get_job(job_id: str) -> dict[str, Any]:
    cleanup_jobs()
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found or expired")
    return job


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def fallback_polygon() -> list[dict[str, float]]:
    return [
        {"x": 0.22, "y": 0.20},
        {"x": 0.78, "y": 0.20},
        {"x": 0.78, "y": 0.82},
        {"x": 0.22, "y": 0.82},
    ]


def extract_json(text: str) -> dict[str, Any] | None:
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def normalize_analysis(payload: dict[str, Any] | None, width: int, height: int) -> dict[str, Any]:
    raw_window = payload.get("window") if isinstance(payload, dict) else None
    raw_polygon = raw_window.get("polygon") if isinstance(raw_window, dict) else None
    polygon: list[dict[str, float]] = []
    if isinstance(raw_polygon, list):
        for point in raw_polygon[:8]:
            if isinstance(point, dict) and "x" in point and "y" in point:
                polygon.append({"x": clamp(point["x"]), "y": clamp(point["y"])})
    if len(polygon) < 4:
        polygon = fallback_polygon()

    confidence = raw_window.get("confidence", 0.25) if isinstance(raw_window, dict) else 0.25
    try:
        confidence = clamp(float(confidence))
    except (TypeError, ValueError):
        confidence = 0.25

    palette = payload.get("palette", []) if isinstance(payload, dict) else []
    if not isinstance(palette, list):
        palette = []

    return {
        "room_summary": str(payload.get("room_summary", "Front-facing room window preview.")) if isinstance(payload, dict) else "Front-facing room window preview.",
        "window": {
            "polygon": polygon,
            "confidence": confidence,
            "description": str(raw_window.get("description", "Detected front-facing window region.")) if isinstance(raw_window, dict) else "Detected front-facing window region.",
            "image_width": width,
            "image_height": height,
        },
        "palette": palette[:8],
    }


def call_gemini(model: str, body: dict[str, Any], *, image_key: str | None = None) -> dict[str, Any]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    request = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Gemini request failed ({error.code}): {detail}") from error
    if not isinstance(result, dict):
        raise RuntimeError("Gemini returned an invalid response")
    return result


def analyze_with_gemini(image_bytes: bytes, mime_type: str, width: int, height: int) -> dict[str, Any]:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    prompt = (
        "Analyze this residential room photo for a Windows Visualizer prototype. "
        "Find one front-facing window or window opening. Return JSON only with this shape: "
        '{"room_summary":"...","window":{"polygon":[{"x":0.2,"y":0.2},'
        '{"x":0.8,"y":0.2},{"x":0.8,"y":0.8},{"x":0.2,"y":0.8}],'
        '"confidence":0.0,"description":"..."},"palette":[]}. '
        "Coordinates must be normalized from 0 to 1 in clockwise order. "
        "Use a conservative confidence score. Do not invent a window if none is visible."
    )
    result = call_gemini(GEMINI_MODEL, {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime_type, "data": encoded}},
            ]
        }],
        "generationConfig": {"response_mime_type": "application/json"},
    })
    parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    text = "\n".join(str(part.get("text", "")) for part in parts if isinstance(part, dict))
    parsed = extract_json(text)
    if not parsed:
        raise RuntimeError("Gemini returned no structured window analysis")
    return normalize_analysis(parsed, width, height)


def style_description(style: str) -> str:
    return {
        "awning": "a top-hinged awning window",
        "bay": "a three-panel bay window",
        "bow": "a five-panel bow window",
        "casement": "a side-hinged casement window",
        "double_hung": "a classic double-hung window",
        "garden": "a projecting garden window",
        "hopper": "a bottom-hinged hopper window",
        "picture": "a wide picture window",
        "sliding": "a horizontal sliding window",
        "specialty": "a custom specialty window",
    }.get(style, "a replacement window")


def image_part(result: dict[str, Any]) -> bytes | None:
    parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        if not isinstance(part, dict):
            continue
        data = part.get("inline_data") or part.get("inlineData")
        if isinstance(data, dict) and data.get("data"):
            try:
                return base64.b64decode(data["data"])
            except (TypeError, ValueError):
                return None
    return None


def generate_key_with_gemini(job: dict[str, Any], style: str) -> Image.Image:
    original = Path(job["original_path"])
    image_bytes = original.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")
    polygon = job["analysis"]["window"]["polygon"]
    prompt = (
        f"Edit this exact residential room photo by replacing only the detected window opening "
        f"with {style_description(style)}. Preserve the room, camera angle, walls, floor, and lighting. "
        "Open the blinds and show a natural green outdoor view. Paint only the window casing, sash, "
        "muntins, and sill a uniform pure magenta #FF00FF for downstream chroma-key replacement. "
        "Do not tint, glow, reflect, or recolor surrounding walls, ceiling, floor, or furniture. "
        f"Detected normalized window polygon: {json.dumps(polygon)}."
    )
    result = call_gemini(GEMINI_IMAGE_MODEL, {
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "image/jpeg", "data": encoded}},
            ]
        }],
        "generationConfig": {"response_mime_type": "image/jpeg"},
    })
    data = image_part(result)
    if not data:
        raise RuntimeError("Gemini image model returned no image")
    return ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")


def polygon_pixels(polygon: list[dict[str, float]], width: int, height: int) -> list[tuple[int, int]]:
    return [(round(point["x"] * width), round(point["y"] * height)) for point in polygon]


def render_local_key(job: dict[str, Any], style: str) -> Image.Image:
    image = Image.open(job["original_path"]).convert("RGB")
    width, height = image.size
    points = polygon_pixels(job["analysis"]["window"]["polygon"], width, height)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    line_width = max(4, round(min(width, height) * 0.012))
    magenta = (255, 0, 255, 255)
    shadow = (0, 0, 0, 75)

    draw.line(points + [points[0]], fill=shadow, width=line_width * 2, joint="curve")
    draw.polygon(points, fill=(38, 96, 130, 35))
    draw.line(points + [points[0]], fill=magenta, width=line_width, joint="curve")

    top_left, top_right, bottom_right, bottom_left = points[:4]
    def interpolate(left: tuple[int, int], right: tuple[int, int], amount: float) -> tuple[int, int]:
        return (
            round(left[0] + (right[0] - left[0]) * amount),
            round(left[1] + (right[1] - left[1]) * amount),
        )

    if style in {"double_hung", "awning", "hopper", "garden"}:
        middle_left = interpolate(top_left, bottom_left, 0.5)
        middle_right = interpolate(top_right, bottom_right, 0.5)
        draw.line([middle_left, middle_right], fill=magenta, width=line_width, joint="curve")
    if style in {"double_hung", "casement", "sliding", "garden"}:
        middle_top = interpolate(top_left, top_right, 0.5)
        middle_bottom = interpolate(bottom_left, bottom_right, 0.5)
        draw.line([middle_top, middle_bottom], fill=magenta, width=line_width, joint="curve")

    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def write_job_image(job: dict[str, Any], style: str, image: Image.Image) -> Path:
    output = Path(job["root"]) / f"{style}.jpg"
    image.save(output, format="JPEG", quality=90, optimize=False)
    return output


async def save_upload(upload: UploadFile, destination: Path) -> tuple[bytes, str, int, int]:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Use JPG, PNG, or WebP images.")
    if upload.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Unsupported image MIME type.")

    data = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller.")
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.width * source.height > MAX_PIXELS:
                raise HTTPException(status_code=413, detail="Image has too many pixels.")
            normalized = ImageOps.exif_transpose(source).convert("RGB")
            width, height = normalized.size
            normalized.save(destination, format="JPEG", quality=92, optimize=True)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=415, detail="Could not decode image.") from error
    return destination.read_bytes(), "image/jpeg", width, height


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "ai_configured": bool(GEMINI_API_KEY)}


@app.post("/api/analyze")
async def analyze(upload: UploadFile = File(...)) -> dict[str, Any]:
    cleanup_jobs()
    job_id = secrets.token_urlsafe(12)
    root = DATA_ROOT / job_id
    root.mkdir(parents=True, exist_ok=False)
    original_path = root / "original.jpg"
    try:
        image_bytes, mime_type, width, height = await save_upload(upload, original_path)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise

    provider = "fallback"
    analysis_error = None
    try:
        analysis = analyze_with_gemini(image_bytes, mime_type, width, height)
        provider = "gemini"
    except Exception as error:
        analysis = normalize_analysis(None, width, height)
        analysis_error = str(error)

    job = {
        "id": job_id,
        "root": str(root),
        "original_path": str(original_path),
        "created_at": time.time(),
        "status": "ready",
        "provider": provider,
        "analysis": analysis,
        "analysis_error": analysis_error,
    }
    with jobs_lock:
        jobs[job_id] = job
    return {
        "job_id": job_id,
        "status": "ready",
        "provider": provider,
        "analysis": analysis,
        "message": "AI analysis complete." if provider == "gemini" else "Using centered-window fallback. Configure GEMINI_API_KEY for AI analysis.",
    }


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    return {
        "job_id": job["id"],
        "status": job["status"],
        "provider": job["provider"],
        "analysis": job["analysis"],
    }


@app.post("/api/jobs/{job_id}/render")
def render(job_id: str, request: RenderRequest) -> dict[str, Any]:
    job = get_job(job_id)
    style = request.style.strip().lower()
    if style not in STYLE_KEYS:
        raise HTTPException(status_code=400, detail="Unsupported window style.")

    if request.polygon and len(request.polygon) >= 4:
        job["analysis"]["window"]["polygon"] = [point.model_dump() for point in request.polygon[:8]]

    job["status"] = "rendering"
    provider = "local-fallback"
    try:
        if request.use_ai and GEMINI_API_KEY:
            try:
                image = generate_key_with_gemini(job, style)
                provider = "gemini"
            except Exception as error:
                job["analysis_error"] = str(error)
                image = render_local_key(job, style)
        else:
            image = render_local_key(job, style)
        output = write_job_image(job, style, image)
    finally:
        job["status"] = "ready"

    return {
        "job_id": job_id,
        "style": style,
        "provider": provider,
        "result_url": f"/api/jobs/{job_id}/result/{style}.jpg",
    }


@app.get("/api/jobs/{job_id}/result/{style}.jpg")
def result(job_id: str, style: str) -> FileResponse:
    job = get_job(job_id)
    if style not in STYLE_KEYS:
        raise HTTPException(status_code=404, detail="Result not found")
    output = Path(job["root"]) / f"{style}.jpg"
    if not output.is_file():
        raise HTTPException(status_code=404, detail="Render not ready")
    return FileResponse(output, media_type="image/jpeg", filename=f"windows-visualizer-{style}.jpg")


app.mount("/", StaticFiles(directory=ROOT, html=True), name="static")
