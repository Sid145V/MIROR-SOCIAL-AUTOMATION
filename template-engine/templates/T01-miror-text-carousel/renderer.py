"""
T01 Browser-Based Renderer Engine — Cross-Platform & Dynamic Path Resolution
Uses Headless Chromium to deterministically render HTML/CSS templates to 1080x1350 PNG.
Reads design tokens strictly from design-spec.json.
Supports explicit backgroundVariant ("01"-"05") and 5-day cycle rotation (dayNumber).
Enforces TextLockSystem validation before generating any output.
Cross-platform compatible (Windows, Linux CI runner, macOS).
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Add core module directory to sys.path
core_dir = DEFAULT_PROJECT_ROOT / "template-engine" / "core"
if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))

from text_lock import TextLockSystem, TextLockError, TextFitError

class T01HtmlRenderer:
    def __init__(self, project_root=None):
        if project_root is None:
            self.project_root = DEFAULT_PROJECT_ROOT
        else:
            self.project_root = Path(project_root).resolve()

        # Load design-spec.json
        self.template_dir = self.project_root / "template-engine" / "templates" / "T01-miror-text-carousel"
        self.spec_path = self.template_dir / "design-spec.json"
        with open(self.spec_path, "r", encoding="utf-8") as f:
            self.spec = json.load(f)

        self.canvas_width = self.spec["canvas"]["width"]
        self.canvas_height = self.spec["canvas"]["height"]

        # Locate Headless Chrome or Edge binary
        self.browser_bin = self._find_browser_binary()

    def _find_browser_binary(self):
        """Cross-platform discovery of Headless Chromium/Chrome/Edge executable without side-effect subprocesses."""
        # 1. Check system PATH executables
        for cmd in ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "msedge"]:
            found = shutil.which(cmd)
            if found and os.path.exists(found):
                return found

        # 2. Check Playwright cached binaries directly on disk
        home = Path.home()
        cache_dirs = [
            home / ".cache" / "ms-playwright",
            home / "Library" / "Caches" / "ms-playwright",
            Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright"
        ]
        for cdir in cache_dirs:
            if cdir.exists():
                for exe_name in ["chrome.exe", "chrome", "headless_shell", "headless_shell.exe"]:
                    matches = list(cdir.rglob(exe_name))
                    for m in matches:
                        if m.is_file():
                            return str(m)

        # 3. Check explicit OS binary paths
        candidates = [
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable"
        ]
        for c in candidates:
            if os.path.exists(c):
                return c

        raise FileNotFoundError("No Headless Chrome or Edge browser binary found on local or CI environment.")

    def resolve_background_variant(self, content_payload):
        """Deterministically resolve background variant key ('01'-'05') from payload."""
        v_explicit = content_payload.get("backgroundVariant") or content_payload.get("variant")
        if v_explicit:
            v_key = str(v_explicit).zfill(2)
            if v_key in self.spec["backgroundVariants"]:
                return v_key

        day_num = content_payload.get("dayNumber") or content_payload.get("day")
        if day_num is not None:
            try:
                day_int = int(day_num)
                calc_idx = ((day_int - 1) % 5) + 1
                return f"{calc_idx:02d}"
            except ValueError:
                pass

        # Default fallback: Variant 01 (Soft Blush)
        return "01"

    def generate_html_content(self, content_payload, expected_manifest=None):
        """Inject content payload into HTML structure after validating text lock integrity and resolving color variant."""
        # 1. Enforce strict TextLockSystem validation
        TextLockSystem.validate_slide_payload(content_payload, expected_manifest)

        # 2. Resolve background variant and text contrast themes
        v_key = self.resolve_background_variant(content_payload)
        v_spec = self.spec["backgroundVariants"][v_key]

        bg_col = v_spec["hex"]
        text_theme_key = v_spec["textTheme"]
        theme_colors = self.spec["textThemes"][text_theme_key]

        headline_col = theme_colors["headline"]
        body_col = theme_colors["body"]
        cta_bg_col = v_spec.get("ctaBg", "#FD6794")
        cta_text_col = v_spec.get("ctaText", "#FFFFFF")

        slide_num = content_payload.get("slide_number") or content_payload.get("slide")
        slide_type = content_payload.get("type")
        slide_id = content_payload.get("id")

        if slide_type == "cta" or slide_num == 3 or slide_id == "S03":
            slide_key = "S03"
        elif slide_type == "follow-through" or slide_num == 2 or slide_id == "S02":
            slide_key = "S02"
        else:
            slide_key = "S01"

        s_spec = self.spec["slides"][slide_key]

        logo_rel_path = s_spec["logo"]["asset"]
        logo_full_path = (self.project_root / logo_rel_path).as_posix()
        logo_abs_url = f"file:///{logo_full_path}"

        font_bold_path = (self.project_root / "assets" / "fonts" / "Montserrat-Bold.ttf").as_posix()
        font_medium_path = (self.project_root / "assets" / "fonts" / "Montserrat-Medium.ttf").as_posix()
        font_semibold_path = (self.project_root / "assets" / "fonts" / "Montserrat-SemiBold.ttf").as_posix()

        canvas_w = self.spec['canvas']['width']
        canvas_h = self.spec['canvas']['height']

        logo_l = s_spec['logo']['left']
        logo_t = s_spec['logo']['top']
        logo_w = s_spec['logo']['width']

        hl_l = s_spec['headline']['left']
        hl_t = s_spec['headline']['top']
        hl_w = s_spec['headline']['width']
        hl_weight = s_spec['headline']['fontWeight']
        hl_size = s_spec['headline']['fontSize']
        hl_line_height = s_spec['headline']['lineHeight']
        hl_spacing = s_spec['headline']['letterSpacing']
        hl_align = s_spec['headline']['alignment']

        # Extract EXACT headline string without modification
        hl_raw = content_payload.get("headline")
        if isinstance(hl_raw, dict):
            hl_text = hl_raw["text"]
        elif isinstance(hl_raw, str):
            hl_text = hl_raw
        elif "headline_groups" in content_payload:
            groups = content_payload["headline_groups"]
            hl_text = "\n\n".join(["\n".join(g) for g in groups])
        else:
            raise TextLockError("Missing headline text in slide payload.")

        # Convert exact newlines to <br> without altering string content
        hl_paragraphs = hl_text.split("\n\n")
        hl_html_blocks = []
        for p in hl_paragraphs:
            p_br = p.replace("\n", "<br>")
            hl_html_blocks.append(f"<p>{p_br}</p>")
        headline_inner_html = "\n".join(hl_html_blocks)

        # Body Copy Handling (S02 & S03)
        body_html_section = ""
        if slide_key in ["S02", "S03"]:
            b_spec = s_spec["body"]
            b_gap = b_spec.get('gapFromHeadline', 55)
            b_w = b_spec['width']
            b_weight = b_spec['fontWeight']
            b_size = b_spec['fontSize']
            b_line_height = b_spec['lineHeight']
            b_align = b_spec['alignment']
            b_spacing = b_spec['paragraphSpacing']

            body_raw = content_payload.get("body") or content_payload.get("body_paragraphs")
            b_p_list = []

            if isinstance(body_raw, list):
                for b_item in body_raw:
                    if isinstance(b_item, dict):
                        txt = b_item["text"]
                    elif isinstance(b_item, list):
                        txt = "\n".join(b_item)
                    else:
                        txt = str(b_item)
                    txt_br = txt.replace("\n", "<br>")
                    b_p_list.append(f"<p>{txt_br}</p>")
            elif isinstance(body_raw, str):
                for p in body_raw.split("\n\n"):
                    p_br = p.replace("\n", "<br>")
                    b_p_list.append(f"<p>{p_br}</p>")

            body_inner_html = "\n".join(b_p_list)

            body_html_section = f"""
      <section class="body-content" style="
        margin-top: {b_gap}px;
        width: {b_w}px;
        font-family: 'Montserrat', sans-serif;
        font-weight: {b_weight};
        font-size: {b_size}px;
        line-height: {b_line_height};
        color: {body_col};
        text-align: {b_align};
      ">
        <style>
          .body-content p {{ margin: 0 0 {b_spacing}px 0; }}
          .body-content p:last-child {{ margin-bottom: 0; }}
        </style>
        {body_inner_html}
      </section>
"""

        # CTA Handling (S03 only)
        cta_html_section = ""
        if slide_key == "S03" and "cta" in s_spec:
            c_spec = s_spec["cta"]
            c_gap = c_spec.get('gapFromBody', 140)
            c_weight = c_spec['fontWeight']
            c_size = c_spec['fontSize']
            c_line_height = c_spec['lineHeight']
            c_radius = c_spec['borderRadius']
            c_pad_x = c_spec['paddingX']
            c_pad_y = c_spec['paddingY']
            c_align = c_spec['alignment']

            cta_raw = content_payload.get("cta")
            if isinstance(cta_raw, dict):
                cta_text = cta_raw["text"]
            elif isinstance(cta_raw, str):
                cta_text = cta_raw
            else:
                raise TextLockError("S03 slide missing exact 'cta' text.")

            cta_formatted = cta_text.replace("\n", "<br>")

            cta_html_section = f"""
      <section class="cta-section" style="margin-top: {c_gap}px;">
        <div class="cta-button" style="
          display: inline-block;
          background-color: {cta_bg_col};
          color: {cta_text_col};
          font-family: 'Montserrat', sans-serif;
          font-weight: {c_weight};
          font-size: {c_size}px;
          line-height: {c_line_height};
          border-radius: {c_radius}px;
          padding: {c_pad_y}px {c_pad_x}px;
          text-align: {c_align};
        ">
          {cta_formatted}
        </div>
      </section>
"""

        hl_transform = "uppercase" if slide_key == "S01" else "none"

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <style>
    @font-face {{
      font-family: 'Montserrat';
      src: url('file:///{font_bold_path}') format('truetype');
      font-weight: 700;
      font-style: normal;
    }}
    @font-face {{
      font-family: 'Montserrat';
      src: url('file:///{font_medium_path}') format('truetype');
      font-weight: 500;
      font-style: normal;
    }}
    @font-face {{
      font-family: 'Montserrat';
      src: url('file:///{font_semibold_path}') format('truetype');
      font-weight: 600;
      font-style: normal;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      width: {canvas_w}px;
      height: {canvas_h}px;
      background-color: {bg_col};
      position: relative;
      overflow: hidden;
      -webkit-font-smoothing: antialiased;
    }}
    .canvas {{
      width: {canvas_w}px;
      height: {canvas_h}px;
      position: relative;
    }}
    .logo {{
      position: absolute;
      left: {logo_l}px;
      top: {logo_t}px;
      width: {logo_w}px;
      height: auto;
      display: block;
    }}
    .content-wrapper {{
      position: absolute;
      left: {hl_l}px;
      top: {hl_t}px;
      width: {hl_w}px;
    }}
    .headline {{
      width: {hl_w}px;
      font-family: 'Montserrat', sans-serif;
      font-weight: {hl_weight};
      font-size: {hl_size}px;
      line-height: {hl_line_height};
      letter-spacing: {hl_spacing}px;
      color: {headline_col};
      text-align: {hl_align};
      text-transform: {hl_transform};
    }}
    .headline p {{
      margin: 0 0 40px 0;
    }}
    .headline p:last-child {{
      margin-bottom: 0;
    }}
  </style>
</head>
<body>
  <main class="canvas">
    <img class="logo" src="{logo_abs_url}" alt="MIROR Logo">
    <div class="content-wrapper">
      <section class="headline">
        {headline_inner_html}
      </section>
      {body_html_section}
      {cta_html_section}
    </div>
  </main>
</body>
</html>"""
        return html_doc

    def render(self, content_json_path, output_png_path, expected_manifest=None):
        """Render slide to 1080x1350 PNG output file using Headless Chromium after text lock validation."""
        import copy
        with open(content_json_path, "r", encoding="utf-8") as f:
            content_payload = json.load(f)

        # If payload is master multi-slide payload, locate exact target slide
        if "slides" in content_payload:
            master_manifest = content_payload.get("text_integrity")
            target_slide = None
            out_basename = os.path.basename(output_png_path)
            for s in content_payload["slides"]:
                s_id = s.get("id") or s.get("slide")
                if s_id and s_id in out_basename:
                    target_slide = copy.deepcopy(s)
                    break
            if not target_slide and len(content_payload["slides"]) > 0:
                target_slide = copy.deepcopy(content_payload["slides"][0])
            
            # Pass through top-level variant / day settings to target slide payload
            if "backgroundVariant" in content_payload and "backgroundVariant" not in target_slide:
                target_slide["backgroundVariant"] = content_payload["backgroundVariant"]
            if "dayNumber" in content_payload and "dayNumber" not in target_slide:
                target_slide["dayNumber"] = content_payload["dayNumber"]

            content_payload = target_slide
            if not expected_manifest:
                expected_manifest = master_manifest

        rendered_html = self.generate_html_content(content_payload, expected_manifest)

        temp_html_path = self.template_dir / "temp_render.html"
        with open(temp_html_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)

        out_path_obj = Path(output_png_path).resolve()
        os.makedirs(out_path_obj.parent, exist_ok=True)

        html_url = f"file:///{temp_html_path.as_posix()}"
        abs_out_png = out_path_obj.as_posix()

        cmd = [
            self.browser_bin,
            "--headless=new",
            f"--screenshot={abs_out_png}",
            f"--window-size={self.canvas_width},{self.canvas_height}",
            "--force-device-scale-factor=1",
            "--hide-scrollbars",
            "--allow-file-access-from-files",
            html_url
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if temp_html_path.exists():
            os.remove(temp_html_path)

        if not os.path.exists(abs_out_png):
            raise RuntimeError(f"Browser rendering failed to produce PNG at {abs_out_png}: {result.stderr}")

        print(f"Successfully rendered: {abs_out_png}")
        return abs_out_png


if __name__ == "__main__":
    renderer = T01HtmlRenderer()
    
    # Render default previews
    s01_json = renderer.project_root / "template-engine" / "tests" / "test_content_MIROR-T01-S01.json"
    s01_out = renderer.project_root / "output" / "previews" / "MIROR-T01-S01.png"
    renderer.render(s01_json, s01_out)

    s02_json = renderer.project_root / "template-engine" / "tests" / "test_content_MIROR-T01-S02.json"
    s02_out = renderer.project_root / "output" / "previews" / "MIROR-T01-S02.png"
    renderer.render(s02_json, s02_out)

    s03_json = renderer.project_root / "template-engine" / "tests" / "test_content_MIROR-T01-S03.json"
    s03_out = renderer.project_root / "output" / "previews" / "MIROR-T01-S03.png"
    renderer.render(s03_json, s03_out)
