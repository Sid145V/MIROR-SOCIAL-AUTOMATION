"""
T01 Template Engine Renderer — MIROR 3-Slide Text Carousel
Visual Correction Edition — Strictly Token-Driven via layout.json
"""

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont

class T01Renderer:
    def __init__(self, project_root="d:/MIROR-SOCIAL-AUTOMATION"):
        self.project_root = os.path.abspath(project_root)

        # Load machine-readable layout config
        self.layout_config_path = os.path.join(
            self.project_root, "template-engine", "templates", "T01-bold-typographic", "layout.json"
        )
        with open(self.layout_config_path, "r", encoding="utf-8") as f:
            self.cfg = json.load(f)

        self.canvas_width = self.cfg["canvas"]["width"]
        self.canvas_height = self.cfg["canvas"]["height"]
        self.bg_color = self.cfg["canvas"]["background_color"]

        # Asset paths
        self.logo_path = os.path.join(self.project_root, self.cfg["logo"]["path"])
        self.font_bold_path = os.path.join(self.project_root, "assets", "fonts", "Montserrat-Bold.ttf")
        self.font_semibold_path = os.path.join(self.project_root, "assets", "fonts", "Montserrat-SemiBold.ttf")
        self.font_medium_path = os.path.join(self.project_root, "assets", "fonts", "Montserrat-Medium.ttf")
        self.font_regular_path = os.path.join(self.project_root, "assets", "fonts", "Montserrat-Regular.ttf")

        self._verify_assets()

    def _verify_assets(self):
        """Verify production assets exist."""
        assets = [
            ("Logo", self.logo_path),
            ("Font Bold", self.font_bold_path),
            ("Font SemiBold", self.font_semibold_path),
            ("Font Medium", self.font_medium_path),
            ("Font Regular", self.font_regular_path),
        ]
        for name, path in assets:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing required production asset: {name} at {path}")

    def load_font(self, font_weight_name, size):
        """Load local Montserrat font by weight name."""
        mapping = {
            "bold": self.font_bold_path,
            "semibold": self.font_semibold_path,
            "medium": self.font_medium_path,
            "regular": self.font_regular_path,
        }
        path = mapping.get(font_weight_name.lower(), self.font_regular_path)
        return ImageFont.truetype(path, size=size)

    def calculate_text_block(self, text, font, max_width, line_height_mult=1.15):
        """Wrap text and return lines, total height, and line height in px."""
        lines = []
        raw_lines = text.split("\n")
        for raw in raw_lines:
            if not raw.strip():
                lines.append("")
                continue
            words = raw.split(" ")
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip() if current_line else word
                bbox = font.getbbox(test_line)
                w = bbox[2] - bbox[0]
                if w <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)

        sample_bbox = font.getbbox("AygJPj19")
        single_line_h = sample_bbox[3] - sample_bbox[1]
        line_height_px = int(single_line_h * line_height_mult)
        total_height = len(lines) * line_height_px

        return lines, total_height, line_height_px

    def render_slide(self, slide_data, post_meta, output_path, total_slides=3):
        """Render a single slide deterministically."""
        # 1. Create clean flat background canvas
        image = Image.new("RGBA", (self.canvas_width, self.canvas_height), self.bg_color)
        draw = ImageDraw.Draw(image)

        slide_num = slide_data.get("slide_number", 1)
        slide_type = slide_data.get("type", "hook")

        # 2. Render Top-Left Logo (Logo X=50, Y=50 across all 3 slides)
        logo = Image.open(self.logo_path).convert("RGBA")
        logo_w = self.cfg["logo"]["width"]
        logo_aspect = logo.height / logo.width
        logo_h = int(logo_w * logo_aspect)
        logo_resized = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        
        logo_x = self.cfg["logo"]["x"]
        logo_y = self.cfg["logo"]["y"]
        image.paste(logo_resized, (logo_x, logo_y), logo_resized)

        # Content grid bounds
        margin_left = self.cfg["grid"]["margin_left"]
        margin_right = self.cfg["grid"]["margin_right"]
        max_text_w = self.cfg["grid"]["max_width"]
        x_left = margin_left
        x_right = self.canvas_width - margin_right

        # 3. Slide 1: HOOK (Center Aligned Headline)
        if slide_type == "hook" or slide_num == 1:
            cfg_s1 = self.cfg["typography"]["slide_1_hook"]
            headline_text = slide_data.get("headline", "")

            font_headline = self.load_font(cfg_s1["font_weight"], cfg_s1["font_size"])
            lines, total_h, line_h = self.calculate_text_block(
                headline_text, font_headline, max_text_w, cfg_s1["line_height_multiplier"]
            )

            # Center visually in vertical content area
            top_bound = self.cfg["grid"]["content_top"] + 40
            bottom_bound = self.cfg["grid"]["content_bottom"] - 40
            avail_h = bottom_bound - top_bound
            start_y = top_bound + max(0, (avail_h - total_h) / 2)

            curr_y = start_y
            for line in lines:
                if line:
                    bbox = font_headline.getbbox(line)
                    w = bbox[2] - bbox[0]
                    start_x = (self.canvas_width - w) / 2
                    draw.text((start_x, curr_y), line, font=font_headline, fill=cfg_s1["color"])
                curr_y += line_h

        # 4. Slide 2: FOLLOW-THROUGH (Left Aligned Headline & Body)
        elif slide_type == "follow-through" or slide_num == 2:
            cfg_s2 = self.cfg["typography"]["slide_2_follow_through"]
            headline_text = slide_data.get("headline", "")
            body_text = slide_data.get("supporting_text", "")

            # Headline
            font_h = self.load_font(cfg_s2["headline"]["font_weight"], cfg_s2["headline"]["font_size"])
            h_lines, h_total_h, h_line_h = self.calculate_text_block(
                headline_text, font_h, max_text_w, cfg_s2["headline"]["line_height_multiplier"]
            )

            # Body
            font_b = self.load_font(cfg_s2["body"]["font_weight"], cfg_s2["body"]["font_size"])
            b_lines, b_total_h, b_line_h = self.calculate_text_block(
                body_text, font_b, max_text_w, cfg_s2["body"]["line_height_multiplier"]
            )

            start_y = 260

            # Render Left-Aligned Headline
            curr_y = start_y
            for line in h_lines:
                if line:
                    draw.text((x_left, curr_y), line, font=font_h, fill=cfg_s2["headline"]["color"])
                curr_y += h_line_h

            curr_y += cfg_s2["gap_headline_body"]

            # Render Left-Aligned Body
            for line in b_lines:
                if line:
                    draw.text((x_left, curr_y), line, font=font_b, fill=cfg_s2["body"]["color"])
                curr_y += b_line_h

        # 5. Slide 3: CTA (Left Aligned Headline & Body + Pill CTA Button)
        elif slide_type == "cta" or slide_num == 3:
            cfg_s3 = self.cfg["typography"]["slide_3_cta"]
            headline_text = slide_data.get("headline", "")
            body_text = slide_data.get("supporting_text", "")
            cta_text = slide_data.get("cta", "")

            # Headline
            font_h = self.load_font(cfg_s3["headline"]["font_weight"], cfg_s3["headline"]["font_size"])
            h_lines, h_total_h, h_line_h = self.calculate_text_block(
                headline_text, font_h, max_text_w, cfg_s3["headline"]["line_height_multiplier"]
            )

            # Body
            font_b = self.load_font(cfg_s3["body"]["font_weight"], cfg_s3["body"]["font_size"])
            b_lines, b_total_h, b_line_h = self.calculate_text_block(
                body_text, font_b, max_text_w, cfg_s3["body"]["line_height_multiplier"]
            )

            start_y = 260

            # Render Left-Aligned Headline
            curr_y = start_y
            for line in h_lines:
                if line:
                    draw.text((x_left, curr_y), line, font=font_h, fill=cfg_s3["headline"]["color"])
                curr_y += h_line_h

            curr_y += cfg_s3["gap_headline_body"]

            # Render Left-Aligned Body
            for line in b_lines:
                if line:
                    draw.text((x_left, curr_y), line, font=font_b, fill=cfg_s3["body"]["color"])
                curr_y += b_line_h

            # Substantial vertical breathing room between body and CTA (140px gap)
            curr_y += cfg_s3["gap_body_cta"]

            # Render CTA Pill Button
            if cta_text:
                cfg_btn = cfg_s3["cta_button"]
                font_cta = self.load_font(cfg_btn["font_weight"], cfg_btn["font_size"])
                cta_lines, cta_total_h, cta_line_h = self.calculate_text_block(
                    cta_text, font_cta, max_text_w - (cfg_btn["padding_x"] * 2), 1.2
                )

                # Compute maximum line width inside CTA
                max_line_w = 0
                for line in cta_lines:
                    bbox = font_cta.getbbox(line)
                    w = bbox[2] - bbox[0]
                    if w > max_line_w:
                        max_line_w = w

                btn_w = max_line_w + (cfg_btn["padding_x"] * 2)
                btn_h = cta_total_h + (cfg_btn["padding_y"] * 2)

                btn_x1 = x_left
                btn_y1 = curr_y
                btn_x2 = btn_x1 + btn_w
                btn_y2 = btn_y1 + btn_h

                # Ensure CTA button stays within right margin
                if btn_x2 > x_right:
                    btn_x2 = x_right
                    btn_w = btn_x2 - btn_x1

                # Draw Pill Button
                draw.rounded_rectangle(
                    [btn_x1, btn_y1, btn_x2, btn_y2],
                    radius=cfg_btn["border_radius"],
                    fill=cfg_btn["bg_color"]
                )

                # Render CTA text centered inside button
                text_start_y = btn_y1 + cfg_btn["padding_y"]
                for line in cta_lines:
                    if line:
                        bbox = font_cta.getbbox(line)
                        lw = bbox[2] - bbox[0]
                        line_x = btn_x1 + (btn_w - lw) / 2
                        draw.text((line_x, text_start_y), line, font=font_cta, fill=cfg_btn["text_color"])
                    text_start_y += cta_line_h

        # 6. Render Bottom-Center Slide Counter (SLIDE X OF Y)
        counter_cfg = self.cfg.get("slide_counter", {})
        if counter_cfg.get("enabled", True):
            font_counter = self.load_font(counter_cfg.get("font_weight", "bold"), counter_cfg.get("font_size", 16))
            template_str = counter_cfg.get("text_template", "SLIDE {slide_number} OF {total_slides}")
            counter_text = template_str.format(slide_number=slide_num, total_slides=total_slides)
            
            c_bbox = font_counter.getbbox(counter_text)
            c_w = c_bbox[2] - c_bbox[0]
            c_x = (self.canvas_width - c_w) / 2
            c_y = counter_cfg.get("y", 1270)
            
            draw.text((c_x, c_y), counter_text, font=font_counter, fill=counter_cfg.get("color", "#3E3353"))

        # Save output PNG
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        rgb_image = Image.new("RGB", image.size, self.bg_color)
        rgb_image.paste(image, mask=image.split()[3])
        rgb_image.save(output_path, "PNG")

        return output_path

    def render_post(self, content_json_path, output_dir="output/previews"):
        """Render all slides for a post payload in exact semantic order: S01 hook, S02 follow-through, S03 cta."""
        with open(content_json_path, "r", encoding="utf-8") as f:
            post_data = json.load(f)

        content_id = post_data.get("content_id", "MIROR-001")
        template_id = post_data.get("template_id", "T01")
        slides = post_data.get("slides", [])

        # Enforce exact slide semantic ordering
        slide_type_order = ["hook", "follow-through", "cta"]
        ordered_slides = []
        for target_type in slide_type_order:
            found = next((s for s in slides if s.get("type") == target_type), None)
            if found:
                ordered_slides.append(found)

        if len(ordered_slides) != 3:
            ordered_slides = slides[:3]

        total_slides = len(ordered_slides)
        rendered_files = []
        for i, slide in enumerate(ordered_slides, start=1):
            filename = f"{content_id}_{template_id}_S{i:02d}.png"
            out_path = os.path.join(self.project_root, output_dir, filename)
            self.render_slide(slide, post_data.get("meta", {}), out_path, total_slides=total_slides)
            rendered_files.append(out_path)
            print(f"Rendered: {out_path}")

        return rendered_files


if __name__ == "__main__":
    renderer = T01Renderer()
    test_content = os.path.join(renderer.project_root, "template-engine", "tests", "test_content_MIROR-001.json")
    renderer.render_post(test_content)
