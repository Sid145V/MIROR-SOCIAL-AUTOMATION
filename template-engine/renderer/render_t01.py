"""
Renderer adapter module for T01 template.
"""

import sys
import os
import importlib.util

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

t01_renderer_path = os.path.join(PROJECT_ROOT, "template-engine", "templates", "T01-bold-typographic", "t01_renderer.py")
spec = importlib.util.spec_from_file_location("t01_module", t01_renderer_path)
t01_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t01_module)
T01Renderer = t01_module.T01Renderer

def render_t01_post(content_json_path, output_dir="output/previews"):
    renderer = T01Renderer(project_root=PROJECT_ROOT)
    return renderer.render_post(content_json_path, output_dir=output_dir)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        render_t01_post(sys.argv[1])
    else:
        test_path = os.path.join(PROJECT_ROOT, "template-engine", "tests", "test_content_MIROR-001.json")
        render_t01_post(test_path)
