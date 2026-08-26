"""
T01 Renderer Legacy Compatibility Wrapper
"""

import os
import sys
import json
from pathlib import Path

DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[3]

class T01Renderer:
    def __init__(self, project_root=None):
        if project_root is None:
            self.project_root = DEFAULT_PROJECT_ROOT
        else:
            self.project_root = Path(project_root).resolve()

        spec_path = self.project_root / "template-engine" / "templates" / "T01-miror-text-carousel" / "design-spec.json"
        with open(spec_path, "r", encoding="utf-8") as f:
            self.spec = json.load(f)

    def render(self, content_json_path, output_png_path):
        from renderer import T01HtmlRenderer
        html_renderer = T01HtmlRenderer(self.project_root)
        return html_renderer.render(content_json_path, output_png_path)
