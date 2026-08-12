#!/usr/bin/env python3
"""
Deep Magenta Key Synthesizer
============================
Renders pure, deep, saturated RGB(255, 0, 255) (#FF00FF) on the window frame, sashes,
and grilles for all 5 architectural window styles (Awning, Bay, Bow, Hopper, Sliding)
with zero wall glare and open retracted blinds.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.environ.get("WINDOWS_VISUALIZER_ASSET_DIR", PROJECT_DIR)
BRAIN_DIR = os.environ.get("WINDOWS_VISUALIZER_BRAIN_DIR", os.path.join(PROJECT_DIR, "generated_sources"))
PURE_MAGENTA = np.array([255, 0, 255], dtype=np.uint8)

def make_deep_magenta_key(base_img_path, mask_generator_fn, out_path):
    img = Image.open(base_img_path).convert("RGB")
    w, h = img.size
    arr = np.array(img, dtype=np.float32)

    # Generate binary mask for frame
    mask = mask_generator_fn(w, h, arr) # float [0..1]

    # Paint frame in deep pure (255, 0, 255)
    out_arr = arr.copy()
    magenta_layer = np.zeros_like(arr)
    magenta_layer[..., 0] = 255.0
    magenta_layer[..., 1] = 0.0
    magenta_layer[..., 2] = 255.0

    mask_3d = mask[..., np.newaxis]
    out_arr = out_arr * (1.0 - mask_3d) + magenta_layer * mask_3d

    final_img = Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8))
    final_img.save(out_path, quality=96)
    print(f"[✓] Generated deep #FF00FF key for: {os.path.basename(out_path)}")
    return out_path

# ==========================================
# 1. AWNING WINDOW (Top-hinged outward push)
# ==========================================
def mask_awning(w, h, arr):
    # From awning render: frame casing + outward pushed bottom sash
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)

    # Outer casing
    x0, y0 = int(w * 0.252), int(h * 0.238)
    x1, y1 = int(w * 0.742), int(h * 0.785)
    draw.rectangle([x0, y0, x1, y1], outline=255, width=int(w * 0.024))
    draw.rectangle([x0, int(h * 0.755), x1, y1], fill=255) # bottom sill

    # Awning pushed sash trapezoid (hinged at top y0, pushed out at bottom)
    sx0, sy0 = int(w * 0.288), int(h * 0.280)
    sx1, sy1 = int(w * 0.706), int(h * 0.280)
    bx0, by0 = int(w * 0.315), int(h * 0.675)
    bx1, by1 = int(w * 0.680), int(h * 0.675)
    draw.line([(sx0, sy0), (sx1, sy1), (bx1, by0), (bx0, by0), (sx0, sy0)], fill=255, width=int(w * 0.016))

    # Scissor arms
    draw.line([(int(w * 0.285), int(h * 0.58)), (bx0, by0)], fill=255, width=6)
    draw.line([(int(w * 0.710), int(h * 0.58)), (bx1, by0)], fill=255, width=6)

    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return np.array(mask_img).astype(np.float32) / 255.0

# ==========================================
# 2. BAY WINDOW (3-Panel 45-degree angle)
# ==========================================
def mask_bay(w, h, arr):
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)

    # Left angled panel
    draw.polygon([
        (int(w * 0.218), int(h * 0.242)), (int(w * 0.362), int(h * 0.262)),
        (int(w * 0.362), int(h * 0.705)), (int(w * 0.218), int(h * 0.728))
    ], outline=255, width=int(w * 0.018))

    # Center picture panel
    draw.rectangle([int(w * 0.368), int(h * 0.268), int(w * 0.632), int(h * 0.696)], outline=255, width=int(w * 0.018))

    # Right angled panel
    draw.polygon([
        (int(w * 0.638), int(h * 0.262)), (int(w * 0.782), int(h * 0.242)),
        (int(w * 0.782), int(h * 0.728)), (int(w * 0.638), int(h * 0.705))
    ], outline=255, width=int(w * 0.018))

    # Center grid muntins
    mid_cx = int(w * 0.50)
    draw.line([(mid_cx, int(h * 0.27)), (mid_cx, int(h * 0.69))], fill=255, width=6)
    for gy in [0.41, 0.55]:
        draw.line([(int(w * 0.37), int(h * gy)), (int(w * 0.63), int(h * gy))], fill=255, width=6)

    # Bench top
    draw.rectangle([int(w * 0.142), int(h * 0.768), int(w * 0.858), int(h * 0.820)], fill=255)

    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return np.array(mask_img).astype(np.float32) / 255.0

# ==========================================
# 3. BOW WINDOW (5-Panel Curved Arc)
# ==========================================
def mask_bow(w, h, arr):
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)

    splits = [0.182, 0.312, 0.442, 0.572, 0.702, 0.832]
    # Arc height variation
    arc_tops = [0.242, 0.262, 0.270, 0.262, 0.242]
    arc_bots = [0.730, 0.710, 0.702, 0.710, 0.730]

    for i in range(5):
        xl = int(w * splits[i])
        xr = int(w * splits[i+1])
        yt = int(h * arc_tops[i])
        yb = int(h * arc_bots[i])
        draw.rectangle([xl, yt, xr, yb], outline=255, width=int(w * 0.016))

    # Curved bench base
    draw.rectangle([int(w * 0.125), int(h * 0.762), int(w * 0.875), int(h * 0.818)], fill=255)

    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return np.array(mask_img).astype(np.float32) / 255.0

# ==========================================
# 4. HOPPER WINDOW (Bottom-hinged tilt inward)
# ==========================================
def mask_hopper(w, h, arr):
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)

    # Outer perimeter frame
    x0, y0 = int(w * 0.250), int(h * 0.235)
    x1, y1 = int(w * 0.745), int(h * 0.785)
    draw.rectangle([x0, y0, x1, y1], outline=255, width=int(w * 0.024))
    draw.rectangle([x0, int(h * 0.755), x1, y1], fill=255) # bottom sill

    # Inward tilt upper sash
    tx0, ty0 = int(w * 0.285), int(h * 0.285)
    tx1, ty1 = int(w * 0.710), int(h * 0.285)
    bx0, by0 = int(w * 0.270), int(h * 0.745)
    bx1, by1 = int(w * 0.725), int(h * 0.745)
    draw.line([(tx0, ty0), (tx1, ty1), (bx1, by0), (bx0, by0), (tx0, ty0)], fill=255, width=int(w * 0.016))

    # Side friction arms & top latch
    draw.line([(tx0, ty0), (int(w * 0.260), int(h * 0.42))], fill=255, width=6)
    draw.line([(tx1, ty1), (int(w * 0.735), int(h * 0.42))], fill=255, width=6)
    draw.rectangle([int(w * 0.485), ty0 - 4, int(w * 0.515), ty0 + 12], fill=255)

    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return np.array(mask_img).astype(np.float32) / 255.0

# ==========================================
# 5. SLIDING WINDOW (Horizontal dual-glide tracks)
# ==========================================
def mask_sliding(w, h, arr):
    mask_img = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask_img)

    # Outer perimeter frame
    x0, y0 = int(w * 0.250), int(h * 0.235)
    x1, y1 = int(w * 0.745), int(h * 0.785)
    draw.rectangle([x0, y0, x1, y1], outline=255, width=int(w * 0.024))
    draw.rectangle([x0, int(h * 0.755), x1, y1], fill=255) # bottom sill

    # Center vertical overlapping meeting stile
    mid_x = int(w * 0.495)
    draw.rectangle([mid_x - int(w * 0.016), y0, mid_x + int(w * 0.016), y1], fill=255)

    # Left & right sliding sashes
    draw.rectangle([x0 + 10, y0 + 10, mid_x, y1 - 10], outline=255, width=int(w * 0.012))
    draw.rectangle([mid_x, y0 + 10, x1 - 10, y1 - 10], outline=255, width=int(w * 0.012))

    # Horizontal bottom track
    draw.rectangle([x0, int(h * 0.740), x1, int(h * 0.758)], fill=255)

    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1.0))
    return np.array(mask_img).astype(np.float32) / 255.0

def main():
    base_ref = os.path.join(SAMPLE_DIR, "master_baseplate_pristine.jpg")
    bay_ref = os.path.join(SAMPLE_DIR, "bay_window_3panel_interior.jpg")
    bow_ref = os.path.join(SAMPLE_DIR, "bow_window_5panel_interior.jpg")

    make_deep_magenta_key(base_ref, mask_awning, os.path.join(SAMPLE_DIR, "key_awning.jpg"))
    make_deep_magenta_key(bay_ref, mask_bay, os.path.join(SAMPLE_DIR, "key_bay.jpg"))
    make_deep_magenta_key(bow_ref, mask_bow, os.path.join(SAMPLE_DIR, "key_bow.jpg"))
    make_deep_magenta_key(base_ref, mask_hopper, os.path.join(SAMPLE_DIR, "key_hopper.jpg"))
    make_deep_magenta_key(base_ref, mask_sliding, os.path.join(SAMPLE_DIR, "key_sliding.jpg"))

if __name__ == "__main__":
    main()
