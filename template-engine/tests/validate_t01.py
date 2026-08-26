"""
Automated QA Validation Suite for T01 Bold Typographic Carousel HTML/CSS Renderer Engine
"""

import os
import sys
import json
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]

def run_qa_checks(project_root=None):
    if project_root is None:
        root = REPO_ROOT
    else:
        root = Path(project_root).resolve()

    output_png = root / "output" / "previews" / "MIROR-001-S01.png"
    spec_path = root / "template-engine" / "templates" / "T01-miror-text-carousel" / "design-spec.json"

    results = []

    def log_check(num, name, passed, message):
        status = "PASSED" if passed else "FAILED"
        results.append((f"{num}. {name}", passed, message))
        print(f"[{status}] {num}. {name}: {message}")

    print("=== STARTING AUTOMATED T01 QA CHECKS ===\n")

    # 1. Spec File
    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    log_check(1, "Design Spec Token File", True, "design-spec.json loaded successfully")

    # 2. Output PNG File Exists
    log_check(2, "Output PNG File", output_png.exists(), f"PNG present at {output_png}")

    # 3. Canvas 1080x1350
    if output_png.exists():
        with Image.open(output_png) as img:
            w, h = img.size
            fmt = img.format
            log_check(3, "Resolution (1080x1350)", w == 1080 and h == 1350 and fmt == "PNG", f"Fmt={fmt}, Dim={w}x{h}")

    # 4. Logo Left=50px, Top=50px Tokens
    s01_spec = spec["slides"]["S01"] if "slides" in spec else spec
    l_left = s01_spec["logo"]["left"]
    l_top = s01_spec["logo"]["top"]
    log_check(4, "Logo Absolute Position", l_left == 50 and l_top == 50, f"Logo left={l_left}px, top={l_top}px")

    all_passed = all(r[1] for r in results)
    print(f"\n=== QA SUMMARY: {'ALL PASSED' if all_passed else 'QA FAILURES DETECTED'} ({sum(1 for r in results if r[1])}/{len(results)}) ===")
    return all_passed


if __name__ == "__main__":
    success = run_qa_checks()
    sys.exit(0 if success else 1)
