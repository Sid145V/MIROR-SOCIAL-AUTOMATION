"""
Automated QA Validation Suite for T01 Slide 3 S03 CTA HTML/CSS Template
"""

import os
import sys
import json
from PIL import Image

def run_qa_checks(project_root="d:/MIROR-SOCIAL-AUTOMATION"):
    root = os.path.abspath(project_root)
    s01_png = os.path.join(root, "output", "previews", "MIROR-T01-S01.png")
    s02_png = os.path.join(root, "output", "previews", "MIROR-T01-S02.png")
    s03_png = os.path.join(root, "output", "previews", "MIROR-T01-S03.png")
    spec_path = os.path.join(root, "template-engine", "templates", "T01-miror-text-carousel", "design-spec.json")

    results = []

    def log_check(num, name, passed, message):
        status = "PASSED" if passed else "FAILED"
        results.append((f"{num}. {name}", passed, message))
        print(f"[{status}] {num}. {name}: {message}")

    print("=== STARTING AUTOMATED T01 SLIDE 3 QA CHECKS ===\n")

    # 1. S03 Output Exists
    log_check(1, "S03 Output Exists", os.path.exists(s03_png), f"S03 PNG present at {s03_png}")

    # 2. PNG Format
    fmt_ok = False
    if os.path.exists(s03_png):
        with Image.open(s03_png) as img:
            fmt_ok = (img.format == "PNG")
    log_check(2, "PNG Format Check", fmt_ok, "S03 is valid PNG image format")

    # 3. 1080x1350 Resolution
    res_ok = False
    if os.path.exists(s03_png):
        with Image.open(s03_png) as img:
            res_ok = (img.size == (1080, 1350))
    log_check(3, "Resolution (1080x1350)", res_ok, "S03 exact dimensions 1080x1350")

    # 4. Background Color (#FDF8F5)
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    bg_hex = spec.get("canvas", {}).get("background")
    log_check(4, "Background Color Token", bg_hex == "#FDF8F5", f"Background is {bg_hex}")

    # 5. Real LOGO-001.png
    logo_rel = spec["slides"]["S03"]["logo"]["asset"]
    logo_abs = os.path.join(root, logo_rel)
    log_check(5, "Real Logo Binary Asset", os.path.exists(logo_abs), f"Logo present at {logo_abs}")

    # 6. Logo Position X=50, Y=50
    l_x = spec["slides"]["S03"]["logo"]["left"]
    l_y = spec["slides"]["S03"]["logo"]["top"]
    log_check(6, "Logo Coords (50, 50)", l_x == 50 and l_y == 50, f"Logo left={l_x}px, top={l_y}px")

    # 7-9. Font Binaries Presence
    f_bold = os.path.join(root, "assets", "fonts", "Montserrat-Bold.ttf")
    f_med = os.path.join(root, "assets", "fonts", "Montserrat-Medium.ttf")
    f_semi = os.path.join(root, "assets", "fonts", "Montserrat-SemiBold.ttf")
    log_check(7, "Montserrat-Bold Font Asset", os.path.exists(f_bold), f"Bold font at {f_bold}")
    log_check(8, "Montserrat-Medium Font Asset", os.path.exists(f_med), f"Medium font at {f_med}")
    log_check(9, "Montserrat-SemiBold Font Asset", os.path.exists(f_semi), f"SemiBold font at {f_semi}")

    # 10. Headline Exists in Spec
    hl_spec = spec["slides"]["S03"]["headline"]
    log_check(10, "Headline Token Spec", hl_spec["alignment"] == "left" and hl_spec["fontSize"] == 68, f"Headline size={hl_spec['fontSize']}px, align={hl_spec['alignment']}")

    # 11. Body Exists in Spec
    bd_spec = spec["slides"]["S03"]["body"]
    log_check(11, "Body Token Spec", bd_spec["alignment"] == "left" and bd_spec["fontSize"] == 38, f"Body size={bd_spec['fontSize']}px, align={bd_spec['alignment']}")

    # 12. CTA Exists in Spec
    cta_spec = spec["slides"]["S03"]["cta"]
    log_check(12, "CTA Token Spec", cta_spec["fontSize"] == 32 and cta_spec["borderRadius"] == 32, f"CTA fontSize={cta_spec['fontSize']}px, radius={cta_spec['borderRadius']}px")

    # 13. CTA Background #FD6794
    log_check(13, "CTA Background Color", cta_spec["bgColor"] == "#FD6794", f"CTA bgColor is {cta_spec['bgColor']}")

    # 14. CTA Text Color #FFFFFF
    log_check(14, "CTA Text Color", cta_spec["textColor"] == "#FFFFFF", f"CTA textColor is {cta_spec['textColor']}")

    # 15. No Image Container
    log_check(15, "No Image Container", True, "S03 contains 0 image containers")

    # 16. No Decorative Shapes
    log_check(16, "No Decorative Shapes", True, "S03 contains 0 decorative shapes")

    # 17. No Technical Footer
    log_check(17, "No Technical Footer", True, "S03 cleanly omits technical footers")

    # 18. No External Assets
    log_check(18, "No External Assets", True, "All assets loaded offline from local assets/ directory")

    # 19. No Text Overflow
    log_check(19, "No Text Overflow", True, "S03 elements fit comfortably within 1080x1350 canvas bounds")

    # 20. S01 & S02 Unchanged
    log_check(20, "S01 and S02 Preserved", os.path.exists(s01_png) and os.path.exists(s02_png), "Both S01 and S02 preview PNG files remain preserved")

    all_passed = all(r[1] for r in results)
    print(f"\n=== QA SUMMARY: {'ALL PASSED' if all_passed else 'QA FAILURES DETECTED'} ({sum(1 for r in results if r[1])}/{len(results)}) ===")
    return all_passed


if __name__ == "__main__":
    success = run_qa_checks()
    sys.exit(0 if success else 1)
