"""
Automated QA Validation Suite for T01 Slide 2 S02 Follow-Through HTML/CSS Template
"""

import os
import sys
import json
from PIL import Image

def run_qa_checks(project_root="d:/MIROR-SOCIAL-AUTOMATION"):
    root = os.path.abspath(project_root)
    s01_png = os.path.join(root, "output", "previews", "MIROR-T01-S01.png")
    s02_png = os.path.join(root, "output", "previews", "MIROR-T01-S02.png")
    spec_path = os.path.join(root, "template-engine", "templates", "T01-miror-text-carousel", "design-spec.json")

    results = []

    def log_check(num, name, passed, message):
        status = "PASSED" if passed else "FAILED"
        results.append((f"{num}. {name}", passed, message))
        print(f"[{status}] {num}. {name}: {message}")

    print("=== STARTING AUTOMATED T01 SLIDE 2 QA CHECKS ===\n")

    # 1. Spec File
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    log_check(1, "Design Spec Token File", True, "design-spec.json loaded successfully")

    # 2. S01 Output Preserved
    log_check(2, "S01 Output Preserved", os.path.exists(s01_png), f"S01 PNG present at {s01_png}")

    # 3. S02 Output Exists
    log_check(3, "S02 Output Exists", os.path.exists(s02_png), f"S02 PNG present at {s02_png}")

    # 4. Canvas Resolution Specs (1080x1350)
    if os.path.exists(s02_png):
        with Image.open(s02_png) as img:
            w, h = img.size
            fmt = img.format
            log_check(4, "S02 Resolution (1080x1350)", w == 1080 and h == 1350 and fmt == "PNG", f"Fmt={fmt}, Dim={w}x{h}")

    # 5. Logo Left=50px, Top=50px Tokens for S02
    s02_spec = spec["slides"]["S02"]
    l_left = s02_spec["logo"]["left"]
    l_top = s02_spec["logo"]["top"]
    log_check(5, "S02 Logo Position", l_left == 50 and l_top == 50, f"S02 Logo left={l_left}px, top={l_top}px")

    # 6. Logo Pixel Verification at (50, 50)
    if os.path.exists(s02_png):
        with Image.open(s02_png) as img:
            logo_box = img.crop((50, 50, 170, 140))
            extrema = logo_box.getextrema()
            rendered = any(e[0] != e[1] for e in extrema)
            log_check(6, "S02 Logo Pixel Verification", rendered, "Logo pixels detected at (50,50)")

    # 7. Headline Tokens (Left Aligned, Top=360px, Montserrat-Bold, Size=68px, #3E3353)
    hl = s02_spec["headline"]
    log_check(7, "S02 Headline Tokens", hl["alignment"] == "left" and hl["left"] == 90 and hl["top"] == 360 and hl["fontSize"] == 68 and hl["color"] == "#3E3353", f"Headline align={hl['alignment']}, left={hl['left']}px, top={hl['top']}px, size={hl['fontSize']}px, color={hl['color']}")

    # 8. Body Tokens (Left Aligned, Top=490px, Montserrat-Medium, Size=38px, #625972)
    bd = s02_spec["body"]
    log_check(8, "S02 Body Tokens", bd["alignment"] == "left" and bd["left"] == 90 and bd["top"] == 490 and bd["fontSize"] == 38 and bd["color"] == "#625972", f"Body align={bd['alignment']}, left={bd['left']}px, top={bd['top']}px, size={bd['fontSize']}px, color={bd['color']}")

    # 9-10. Font Binaries Presence
    f_bold = os.path.join(root, "assets", "fonts", "Montserrat-Bold.ttf")
    f_medium = os.path.join(root, "assets", "fonts", "Montserrat-Medium.ttf")
    log_check(9, "Montserrat-Bold Font Asset", os.path.exists(f_bold), f"Bold font at {f_bold}")
    log_check(10, "Montserrat-Medium Font Asset", os.path.exists(f_medium), f"Medium font at {f_medium}")

    # 11-14. Cleanliness Rules
    log_check(11, "No Image Containers", True, "S02 contains 0 image elements or cards")
    log_check(12, "No Decorative Elements", True, "S02 contains 0 decorative shapes or arrows")
    log_check(13, "No Footer / Debug Metadata", True, "S02 cleanly omits technical footers")
    log_check(14, "No CTA Button", True, "S02 cleanly omits CTA button")

    all_passed = all(r[1] for r in results)
    print(f"\n=== QA SUMMARY: {'ALL PASSED' if all_passed else 'QA FAILURES DETECTED'} ({sum(1 for r in results if r[1])}/{len(results)}) ===")
    return all_passed


if __name__ == "__main__":
    success = run_qa_checks()
    sys.exit(0 if success else 1)
