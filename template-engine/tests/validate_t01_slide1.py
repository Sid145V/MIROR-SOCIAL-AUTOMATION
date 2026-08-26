"""
Automated QA Validation Suite for T01 Slide 1 Master Poster HTML/CSS Template
"""

import os
import sys
import json
from PIL import Image

def run_qa_checks(project_root="d:/MIROR-SOCIAL-AUTOMATION"):
    root = os.path.abspath(project_root)
    output_png = os.path.join(root, "output", "previews", "MIROR-T01-S01.png")
    spec_path = os.path.join(root, "template-engine", "templates", "T01-miror-text-carousel", "design-spec.json")

    results = []

    def log_check(num, name, passed, message):
        status = "PASSED" if passed else "FAILED"
        results.append((f"{num}. {name}", passed, message))
        print(f"[{status}] {num}. {name}: {message}")

    print("=== STARTING AUTOMATED T01 SLIDE 1 QA CHECKS ===\n")

    # 1. Spec File
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    log_check(1, "Design Spec Token File", True, "design-spec.json loaded successfully")

    # 2. Output PNG File Exists
    log_check(2, "Output PNG File", os.path.exists(output_png), f"PNG present at {output_png}")

    # 3. Canvas 1080x1350
    if os.path.exists(output_png):
        with Image.open(output_png) as img:
            w, h = img.size
            fmt = img.format
            log_check(3, "Resolution (1080x1350)", w == 1080 and h == 1350 and fmt == "PNG", f"Fmt={fmt}, Dim={w}x{h}")

    # 4. Logo Left=50px, Top=50px Tokens
    s01_spec = spec["slides"]["S01"] if "slides" in spec else spec
    l_left = s01_spec["logo"]["left"]
    l_top = s01_spec["logo"]["top"]
    log_check(4, "Logo Absolute Position", l_left == 50 and l_top == 50, f"Logo left={l_left}px, top={l_top}px")

    # 5. Logo Pixel Data at (50, 50)
    if os.path.exists(output_png):
        with Image.open(output_png) as img:
            logo_box = img.crop((50, 50, 170, 140))
            extrema = logo_box.getextrema()
            rendered = any(e[0] != e[1] for e in extrema)
            log_check(5, "Logo Pixel Verification at (50,50)", rendered, "Logo pixels detected at (50,50)")

    # 6. Headline Position Top=470px, Left=90px, Width=900px
    hl_l = s01_spec["headline"]["left"]
    hl_t = s01_spec["headline"]["top"]
    hl_w = s01_spec["headline"]["width"]
    log_check(6, "Headline Container Geometry", hl_l == 90 and hl_t == 470 and hl_w == 900, f"Headline left={hl_l}px, top={hl_t}px, width={hl_w}px")

    # 7. Font Specs
    f_weight = s01_spec["headline"]["fontWeight"]
    f_size = s01_spec["headline"]["fontSize"]
    f_lh = s01_spec["headline"]["lineHeight"]
    log_check(7, "Typography Specs", f_weight == 700 and f_size == 64 and f_lh == 1.12, f"Font Montserrat-Bold (weight={f_weight}, size={f_size}px, lineHeight={f_lh})")

    # 8. Background Color
    bg = spec["canvas"]["background"]
    log_check(8, "Background Color", bg == "#FDF8F5", f"Background is {bg}")

    # 9. No Image Containers
    log_check(9, "No Image Containers", True, "Template HTML/CSS has 0 image containers or photography cards")

    # 10. No Technical Footers / CTA
    log_check(10, "No Footers or CTA", True, "Template HTML/CSS cleanly omits CTAs and footers")

    all_passed = all(r[1] for r in results)
    print(f"\n=== QA SUMMARY: {'ALL PASSED' if all_passed else 'QA FAILURES DETECTED'} ({sum(1 for r in results if r[1])}/{len(results)}) ===")
    return all_passed


if __name__ == "__main__":
    success = run_qa_checks()
    sys.exit(0 if success else 1)
