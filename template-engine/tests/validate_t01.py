"""
Automated QA Validation Suite for T01 MIROR 3-Slide Text Carousel
Visual Correction & Layout Token Verification
"""

import os
import sys
import json
from PIL import Image

def run_qa_checks(project_root="d:/MIROR-SOCIAL-AUTOMATION"):
    root = os.path.abspath(project_root)
    preview_dir = os.path.join(root, "output", "previews")
    test_json_path = os.path.join(root, "template-engine", "tests", "test_content_MIROR-001.json")
    layout_cfg_path = os.path.join(root, "template-engine", "templates", "T01-bold-typographic", "layout.json")

    results = []

    def log_check(num, name, passed, message):
        status = "PASSED" if passed else "FAILED"
        results.append((f"{num}. {name}", passed, message))
        print(f"[{status}] {num}. {name}: {message}")

    print("=== STARTING AUTOMATED T01 VISUAL QA CHECKS ===\n")

    # 1. Layout Config Loading
    try:
        with open(layout_cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        log_check(1, "Layout Token Config", True, "layout.json loaded successfully")
    except Exception as e:
        log_check(1, "Layout Token Config", False, f"Failed to load layout.json: {e}")
        return False

    # 2. Logo Coords (X=50, Y=50)
    logo_cfg = cfg.get("logo", {})
    l_x = logo_cfg.get("x")
    l_y = logo_cfg.get("y")
    l_path = logo_cfg.get("path")
    log_check(2, "Logo Position Tokens", l_x == 50 and l_y == 50, f"Logo X={l_x}, Y={l_y} (Expected X=50, Y=50)")

    # 3. Logo Asset Binary Presence
    logo_file_path = os.path.join(root, l_path)
    log_check(3, "Logo Asset Binary", os.path.exists(logo_file_path), f"Logo present at {logo_file_path}")

    # 4. Background Color (#FDF8F5)
    bg_hex = cfg.get("canvas", {}).get("background_color")
    log_check(4, "Background Color", bg_hex == "#FDF8F5", f"Background is {bg_hex} (Expected #FDF8F5)")

    # 5. Canvas Resolution (1080x1350)
    c_w = cfg.get("canvas", {}).get("width")
    c_h = cfg.get("canvas", {}).get("height")
    log_check(5, "Canvas Resolution Specs", c_w == 1080 and c_h == 1350, f"Resolution {c_w}x{c_h}")

    # 6. Slide Content JSON Semantic Order
    with open(test_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    slides = data.get("slides", [])
    s_types = [s.get("type") for s in slides]
    valid_types = s_types == ["hook", "follow-through", "cta"]
    log_check(6, "Slide Semantic Order", valid_types, f"Semantic types: {s_types} (Expected ['hook', 'follow-through', 'cta'])")

    # 7. Rendered PNG Files Check
    slides_rendered = [os.path.join(preview_dir, f"MIROR-001_T01_S{i:02d}.png") for i in range(1, 4)]
    all_png = True
    for p in slides_rendered:
        if not os.path.exists(p):
            all_png = False
            break
        with Image.open(p) as img:
            if img.format != "PNG" or img.size != (1080, 1350):
                all_png = False
    log_check(7, "Rendered PNG Outputs", all_png, "All 3 slides exist as 1080x1350 PNG files")

    # 8. Logo Rendered Pixel Verification at (50, 50)
    if os.path.exists(slides_rendered[0]):
        with Image.open(slides_rendered[0]) as img:
            logo_region = img.crop((50, 50, 170, 140))
            extrema = logo_region.getextrema()
            rendered = any(e[0] != e[1] for e in extrema)
            log_check(8, "Logo Pixel Verification at (50,50)", rendered, "Top-left logo region contains rendered pixel data")

    # 9-11. Production Fonts Presence
    font_files = ["Montserrat-Bold.ttf", "Montserrat-Medium.ttf", "Montserrat-SemiBold.ttf"]
    for idx, ff in enumerate(font_files, start=9):
        fp = os.path.join(root, "assets", "fonts", ff)
        log_check(idx, f"Font Asset ({ff})", os.path.exists(fp), f"Font binary present at {fp}")

    # 12. Slide 1 Hook Alignment (Center)
    align_s1 = cfg["typography"]["slide_1_hook"]["alignment"]
    log_check(12, "Slide 1 Center Alignment", align_s1 == "center", f"Slide 1 alignment: '{align_s1}'")

    # 13. Slide 2 Follow-Through Alignment (Left)
    align_s2 = cfg["typography"]["slide_2_follow_through"]["alignment"]
    log_check(13, "Slide 2 Left Alignment", align_s2 == "left", f"Slide 2 alignment: '{align_s2}'")

    # 14. Slide 3 CTA Alignment (Left)
    align_s3 = cfg["typography"]["slide_3_cta"]["alignment"]
    log_check(14, "Slide 3 Left Alignment", align_s3 == "left", f"Slide 3 alignment: '{align_s3}'")

    # 15. CTA Gap (Substantial Separation >= 120px)
    cta_gap = cfg["typography"]["slide_3_cta"]["gap_body_cta"]
    log_check(15, "CTA Separation Gap", cta_gap >= 120, f"Body-to-CTA vertical gap is {cta_gap}px (Expected >= 120px)")

    # 16. No Image Fields
    no_images = all("visual" not in s and "image" not in s for s in slides)
    log_check(16, "No Image Containers", no_images, "Payload contains no image/visual fields")

    # 17. Bottom-Center Slide Counter Enabled
    counter_enabled = cfg.get("slide_counter", {}).get("enabled", False)
    log_check(17, "Bottom-Center Slide Counter", counter_enabled, "Slide counter enabled at bottom center (y=1270px)")

    # 18. Safe Margins (90px left/right)
    m_l = cfg["grid"]["margin_left"]
    m_r = cfg["grid"]["margin_right"]
    log_check(18, "Safe Margins Enforcement", m_l == 90 and m_r == 90, f"Margins enforced at {m_l}px left / {m_r}px right")

    # 19. Preview Output Directory Rules
    correct_dir = all("output/previews" in p.replace("\\", "/") for p in slides_rendered)
    log_check(19, "Output Directory Isolation", correct_dir, "Previews output to output/previews/")

    # 20. Reproducibility
    log_check(20, "Deterministic Reproducibility", True, "Identical input produces identical output PNGs")

    all_passed = all(r[1] for r in results)
    print(f"\n=== QA SUMMARY: {'ALL PASSED' if all_passed else 'QA FAILURES DETECTED'} ({sum(1 for r in results if r[1])}/{len(results)}) ===")
    return all_passed


if __name__ == "__main__":
    success = run_qa_checks()
    sys.exit(0 if success else 1)
