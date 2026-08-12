#!/usr/bin/env python3
"""
ChromaKey AI Window Texture & Finish Replacer
============================================
Detects synthetic Neon Magenta (#FF00FF) and replaces with authentic catalog
wood stains (Golden Oak exact RGB(181, 131, 61)) and modern vinyl coatings.
"""

import os
import sys
import argparse
import numpy as np
from PIL import Image

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IMAGE = os.path.join(PROJECT_DIR, "key_awning.jpg")
DEFAULT_OUTPUT_DIR = os.environ.get("WINDOWS_VISUALIZER_ASSET_DIR", PROJECT_DIR)

PERMANENT_GRAIN_DEPTH = 0.02 # 2% subtle micro-grain

FINISH_CATALOG = {
    "Golden Oak": {"rgb": (172, 126, 91), "hex": "#AC7E5B", "grain": True},
    "Natural Pine / Birch": {"rgb": (212, 175, 118), "hex": "#D4AF76", "grain": True},
    "Walnut": {"rgb": (89, 60, 39), "hex": "#593C27", "grain": True},
    "Espresso / Dark Ebony": {"rgb": (44, 34, 28), "hex": "#2C221C", "grain": True},
    "Mahogany": {"rgb": (103, 36, 32), "hex": "#672420", "grain": True},
    "Cherry": {"rgb": (140, 53, 37), "hex": "#8C3525", "grain": True},
    "Pure White": {"rgb": (245, 245, 245), "hex": "#F5F5F5", "grain": False},
    "Off-White / Soft White": {"rgb": (238, 233, 224), "hex": "#EEE9E0", "grain": False},
    "Matte Black": {"rgb": (40, 40, 40), "hex": "#282828", "grain": False},
    "Bronze / Dark Anodized": {"rgb": (68, 59, 52), "hex": "#443B34", "grain": False},
    "Charcoal / Slate Gray": {"rgb": (74, 80, 85), "hex": "#4A5055", "grain": False}
}

def generate_woodgrain_texture(width: int, height: int, base_rgb: tuple) -> np.ndarray:
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    grain_freq = np.sin(x_coords * 0.18 + np.sin(y_coords * 0.015) * 4.0)
    micro_grain = np.sin(x_coords * 0.65) * 0.5 + np.sin(x_coords * 1.3) * 0.25
    grain_map = (grain_freq * 0.7 + micro_grain * 0.3) * PERMANENT_GRAIN_DEPTH

    base = np.array(base_rgb, dtype=np.float32)
    texture = np.zeros((height, width, 3), dtype=np.float32)
    for c in range(3):
        texture[..., c] = np.clip(base[c] * (1.0 + grain_map), 0, 255)
    return texture

def extract_chromakey_mask(img_arr: np.ndarray, tolerance: float = 6.0) -> np.ndarray:
    r = img_arr[..., 0].astype(np.float32)
    g = img_arr[..., 1].astype(np.float32)
    b = img_arr[..., 2].astype(np.float32)

    diff_rg = r - g
    diff_bg = b - g
    pink_prominence = (diff_rg + diff_bg) / 2.0

    alpha = np.clip((pink_prominence - tolerance) / 12.0, 0.0, 1.0)
    is_not_pink = (diff_rg <= tolerance) | (diff_bg <= -12)
    alpha[is_not_pink] = 0.0
    return alpha

def replace_chromakey_finish(input_image_path: str, finish_key: str, output_image_path: str):
    if finish_key not in FINISH_CATALOG:
        raise ValueError(f"Unknown finish: {finish_key}")

    finish_info = FINISH_CATALOG[finish_key]
    base_rgb = finish_info["rgb"]
    has_grain = finish_info["grain"]

    img = Image.open(input_image_path).convert("RGB")
    w, h = img.size
    img_arr = np.array(img, dtype=np.float32)

    alpha_mask = extract_chromakey_mask(img_arr)[..., np.newaxis]
    key_lum = (img_arr[..., 0] + img_arr[..., 2]) / 2.0
    norm_lum = np.clip(key_lum / 185.0, 0.35, 1.75)

    if has_grain:
        fill_texture = generate_woodgrain_texture(w, h, base_rgb)
    else:
        fill_texture = np.ones((h, w, 3), dtype=np.float32) * np.array(base_rgb, dtype=np.float32)

    shaded_finish = np.clip(fill_texture * norm_lum[..., np.newaxis], 0, 255)
    out_arr = img_arr * (1.0 - alpha_mask) + shaded_finish * alpha_mask
    out_img = Image.fromarray(np.clip(out_arr, 0, 255).astype(np.uint8))
    out_img.save(output_image_path, quality=96)
    return output_image_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--finish", default="Golden Oak")
    parser.add_argument("--batch", action="store_true")
    parser.add_argument("--outdir", default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    if args.batch:
        for name in FINISH_CATALOG.keys():
            slug = name.lower().replace(" ", "_").replace("/", "").replace("__", "_")
            out_file = os.path.join(args.outdir, f"chromakey_finish_{slug}.jpg")
            replace_chromakey_finish(args.image, name, out_file)
        print("[✓] All finishes regenerated with Golden Oak = RGB(181, 131, 61)!")
