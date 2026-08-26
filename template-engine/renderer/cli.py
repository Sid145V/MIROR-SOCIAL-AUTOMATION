"""
MIROR Social Automation — Template Engine CLI Entry Point
Renders deterministic Instagram creatives from JSON content payloads.
"""

import sys
import os
import argparse
import json
import importlib.util

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Dynamically import t01_renderer
t01_renderer_path = os.path.join(PROJECT_ROOT, "template-engine", "templates", "T01-bold-typographic", "t01_renderer.py")
spec = importlib.util.spec_from_file_location("t01_module", t01_renderer_path)
t01_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t01_module)
T01Renderer = t01_module.T01Renderer

def main():
    parser = argparse.ArgumentParser(description="MIROR Social Automation Template Renderer")
    parser.add_argument("--content", required=True, help="Path to input JSON content payload file")
    parser.add_argument("--output-dir", default="output/previews", help="Directory for output PNG preview renders")
    args = parser.parse_args()

    content_path = os.path.abspath(args.content)
    if not os.path.exists(content_path):
        print(f"Error: Content file not found at {content_path}")
        sys.exit(1)

    with open(content_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    template_id = data.get("template_id", "")
    if template_id == "T01":
        renderer = T01Renderer(project_root=PROJECT_ROOT)
        rendered_files = renderer.render_post(content_path, output_dir=args.output_dir)
        print(f"\nSuccessfully rendered {len(rendered_files)} slides for {data.get('content_id')}:")
        for file_path in rendered_files:
            print(f" - {file_path}")
    else:
        print(f"Error: Template ID '{template_id}' is not supported or not implemented yet.")
        sys.exit(1)

if __name__ == "__main__":
    main()
