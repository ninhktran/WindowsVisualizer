#!/usr/bin/env python3
"""
Build and Organize All 10 Architectural Window Style Keys
=========================================================
Generates and normalizes pure Neon Magenta (#FF00FF) key images for all 10 window styles:
1. Awning Windows
2. Bay Windows (3-Panel)
3. Bow Windows (5-Panel)
4. Casement Windows
5. Double-Hung Windows
6. Garden Windows
7. Hopper Windows
8. Picture Windows
9. Sliding Windows
10. Specialty Windows (Arched / Geometric)
"""

import os
import shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.environ.get("WINDOWS_VISUALIZER_ASSET_DIR", PROJECT_DIR)
BRAIN_DIR = os.environ.get("WINDOWS_VISUALIZER_BRAIN_DIR", os.path.join(PROJECT_DIR, "generated_sources"))

def create_all_10_styles():
    print("[*] Generating all 10 architectural window styles with pure #FF00FF keys...")

    # 1. Awning Window
    awning_src = os.path.join(BRAIN_DIR, "window_key_awning_1786157664238.jpg")
    if os.path.exists(awning_src):
        shutil.copy(awning_src, os.path.join(SAMPLE_DIR, "key_awning.jpg"))
        print("[✓] 1. Awning Window ready.")

    # 2. Casement Window
    casement_src = os.path.join(SAMPLE_DIR, "key_casement.jpg")
    if os.path.exists(casement_src):
        print("[✓] 2. Casement Window ready.")

    # 3. Picture Window
    picture_src = os.path.join(SAMPLE_DIR, "key_picture.jpg")
    if os.path.exists(picture_src):
        print("[✓] 3. Picture Window ready.")

    # 4. Double-Hung Window
    dh_src = os.path.join(SAMPLE_DIR, "key_double_hung.jpg")
    if os.path.exists(dh_src):
        print("[✓] 4. Double-Hung Window ready.")

    # 5. Garden Window
    garden_src = os.path.join(SAMPLE_DIR, "key_garden.jpg")
    if os.path.exists(garden_src):
        print("[✓] 5. Garden Window ready.")

    # 6. Bay Window (3-Panel 45-degree angle)
    bay_img = Image.open(os.path.join(SAMPLE_DIR, "bay_window_3panel_interior.jpg")).convert("RGB")
    bw, bh = bay_img.size
    # Key the 3-panel frames in #FF00FF
    bay_arr = np.array(bay_img)
    # 3-Panel frame coordinates
    # Left angled panel
    draw_bay = ImageDraw.Draw(bay_img)
    pink_rgb = (255, 0, 255)
    # Paint bay frame in pure #FF00FF
    draw_bay.line([(int(bw*0.22), int(bh*0.24)), (int(bw*0.365), int(bh*0.26)), (int(bw*0.365), int(bh*0.71)), (int(bw*0.22), int(bh*0.73)), (int(bw*0.22), int(bh*0.24))], fill=pink_rgb, width=14)
    # Center picture panel
    draw_bay.rectangle([int(bw*0.370), int(bh*0.268), int(bw*0.630), int(bh*0.695)], outline=pink_rgb, width=14)
    # Right angled panel
    draw_bay.line([(int(bw*0.635), int(bh*0.26)), (int(bw*0.78), int(bh*0.24)), (int(bw*0.78), int(bh*0.73)), (int(bw*0.635), int(bh*0.71)), (int(bw*0.635), int(bh*0.26))], fill=pink_rgb, width=14)
    # Bench top
    draw_bay.rectangle([int(bw*0.145), int(bh*0.77), int(bw*0.855), int(bh*0.815)], fill=pink_rgb)
    bay_img.save(os.path.join(SAMPLE_DIR, "key_bay.jpg"), quality=95)
    print("[✓] 6. Bay Window (3-Panel) ready.")

    # 7. Bow Window (5-Panel Curved Arc)
    bow_img = Image.open(os.path.join(SAMPLE_DIR, "bow_window_5panel_interior.jpg")).convert("RGB")
    bow_w, bow_h = bow_img.size
    draw_bow = ImageDraw.Draw(bow_img)
    # 5 vertical panel divisions
    x_splits = [0.185, 0.315, 0.445, 0.575, 0.705, 0.835]
    for i in range(5):
        x_left = int(bow_w * x_splits[i])
        x_right = int(bow_w * x_splits[i+1])
        draw_bow.rectangle([x_left, int(bow_h * 0.235), x_right, int(bow_h * 0.735)], outline=pink_rgb, width=12)
    draw_bow.rectangle([int(bow_w * 0.13), int(bow_h * 0.765), int(bow_w * 0.87), int(bow_h * 0.815)], fill=pink_rgb)
    bow_img.save(os.path.join(SAMPLE_DIR, "key_bow.jpg"), quality=95)
    print("[✓] 7. Bow Window (5-Panel) ready.")

    # 8. Sliding Window (Horizontal glide 2-track glass)
    slide_img = Image.open(os.path.join(SAMPLE_DIR, "key_picture.jpg")).convert("RGB")
    sw, sh = slide_img.size
    draw_slide = ImageDraw.Draw(slide_img)
    # Add center vertical sliding sash overlap and horizontal glide track
    draw_slide.rectangle([int(sw * 0.485), int(sh * 0.245), int(sw * 0.515), int(sh * 0.775)], fill=pink_rgb)
    # Sliding handles
    draw_slide.rectangle([int(sw * 0.470), int(sh * 0.48), int(sw * 0.482), int(sh * 0.54)], fill=pink_rgb)
    draw_slide.rectangle([int(sw * 0.518), int(sh * 0.48), int(sw * 0.530), int(sh * 0.54)], fill=pink_rgb)
    slide_img.save(os.path.join(SAMPLE_DIR, "key_sliding.jpg"), quality=95)
    print("[✓] 8. Sliding Window ready.")

    # 9. Hopper Window (Bottom-hinged inward tilt sash with top handles)
    hopper_img = Image.open(os.path.join(SAMPLE_DIR, "key_casement.jpg")).convert("RGB")
    hw, hh = hopper_img.size
    draw_hopper = ImageDraw.Draw(hopper_img)
    # Draw inward tilt support arms and top latch
    draw_hopper.line([(int(hw*0.27), int(hh*0.35)), (int(hw*0.32), int(hh*0.72))], fill=pink_rgb, width=8)
    draw_hopper.line([(int(hw*0.73), int(hh*0.35)), (int(hw*0.68), int(hh*0.72))], fill=pink_rgb, width=8)
    draw_hopper.rectangle([int(hw*0.48), int(hh*0.25), int(hw*0.52), int(hh*0.28)], fill=pink_rgb)
    hopper_img.save(os.path.join(SAMPLE_DIR, "key_hopper.jpg"), quality=95)
    print("[✓] 9. Hopper Window ready.")

    # 10. Specialty Window (Arched Transom & Geometric Sunburst)
    spec_img = Image.open(os.path.join(SAMPLE_DIR, "key_picture.jpg")).convert("RGB")
    spw, sph = spec_img.size
    draw_spec = ImageDraw.Draw(spec_img)
    # Top graceful arch
    draw_spec.arc([int(spw*0.26), int(sph*0.14), int(spw*0.74), int(sph*0.48)], 180, 0, fill=pink_rgb, width=14)
    # Sunburst radial spokes
    arch_cx, arch_cy = int(spw * 0.50), int(sph * 0.31)
    for angle in [210, 240, 270, 300, 330]:
        rad = np.radians(angle)
        ex = arch_cx + int(np.cos(rad) * (spw * 0.23))
        ey = arch_cy + int(np.sin(rad) * (sph * 0.16))
        draw_spec.line([(arch_cx, arch_cy), (ex, ey)], fill=pink_rgb, width=6)
    # Horizontal transom bar
    draw_spec.rectangle([int(spw*0.25), int(sph*0.30), int(spw*0.75), int(sph*0.32)], fill=pink_rgb)
    spec_img.save(os.path.join(SAMPLE_DIR, "key_specialty.jpg"), quality=95)
    print("[✓] 10. Specialty Window (Arched) ready.")

if __name__ == "__main__":
    create_all_10_styles()
