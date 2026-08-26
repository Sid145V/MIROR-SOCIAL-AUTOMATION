# MIROR Production Template Engine Specifications

This document defines the technical specifications, HTML/CSS layout rules, design token schemas, rendering adapters, and QA criteria for production templates in the MIROR Social Automation system.

---

## Template T01: MIROR Text Carousel (3-Slide System)

### 1. Template Identity & Status
- **Template ID:** `T01`
- **Template Name:** MIROR Text Carousel — 3-Slide System (S01, S02, S03)
- **Version:** `1.2.0`
- **Directory:** `template-engine/templates/T01-miror-text-carousel/`
- **Status:** `DEVELOPMENT — S03 VISUAL REVIEW REQUIRED`
- **Scope:** **SLIDES 1, 2, and 3 FULLY IMPLEMENTED**. *(S01 and S02 approved and locked; S03 under visual review).*

---

### 2. Design Tokens (`design-spec.json`)

Source of truth for all layout, geometry, logo coordinates, and typography parameters across all 3 slides:

```json
{
  "canvas": {
    "width": 1080,
    "height": 1350,
    "background": "#FDF8F5"
  },
  "slides": {
    "S01": {
      "logo": { "asset": "assets/logos/LOGO-001.png", "left": 50, "top": 50, "width": 120 },
      "headline": { "left": 90, "top": 470, "width": 900, "fontSize": 64, "lineHeight": 1.12, "color": "#3E3353", "alignment": "center" }
    },
    "S02": {
      "logo": { "asset": "assets/logos/LOGO-001.png", "left": 50, "top": 50, "width": 120 },
      "headline": { "left": 90, "top": 360, "width": 900, "fontSize": 68, "lineHeight": 1.10, "color": "#3E3353", "alignment": "left" },
      "body": { "left": 90, "gapFromHeadline": 55, "width": 900, "fontSize": 38, "lineHeight": 1.35, "color": "#625972", "alignment": "left", "paragraphSpacing": 35 }
    },
    "S03": {
      "logo": { "asset": "assets/logos/LOGO-001.png", "left": 50, "top": 50, "width": 120 },
      "headline": { "left": 90, "top": 360, "width": 900, "fontSize": 68, "lineHeight": 1.10, "color": "#3E3353", "alignment": "left" },
      "body": { "left": 90, "gapFromHeadline": 55, "width": 900, "fontSize": 38, "lineHeight": 1.35, "color": "#625972", "alignment": "left", "paragraphSpacing": 12 },
      "cta": { "left": 90, "gapFromBody": 140, "fontSize": 32, "lineHeight": 1.2, "bgColor": "#FD6794", "textColor": "#FFFFFF", "borderRadius": 32, "paddingX": 48, "paddingY": 24, "alignment": "center" }
    }
  }
}
```

---

### 3. Visual Architecture (HTML + CSS)

- **Canvas:** `1080 × 1350 px` (4:5 Portrait)
- **Background:** Flat `#FDF8F5` (Soft Blush). No gradients, noise, textures, cards, borders, or shadows.
- **Logo:** `LOGO-001.png` binary asset positioned absolutely at `left: 50px; top: 50px; width: 120px;`. Identical position across all 3 slides.
- **Slide 1 (Hook):** Headline centered horizontally and vertically (`top: 470px`, `font-size: 64px`, `Montserrat-Bold 700`, `#3E3353`).
- **Slide 2 (Follow-Through):** Headline left-aligned (`top: 360px`, `font-size: 68px`, `Montserrat-Bold 700`, `#3E3353`). Body copy left-aligned (`margin-top: 55px`, `font-size: 38px`, `Montserrat-Medium 500`, `#625972`). Paragraph spacing `35px`.
- **Slide 3 (CTA):** Headline left-aligned (`top: 360px`, `68px`). Body copy left-aligned (`margin-top: 55px`, `38px`). CTA pill button card left-aligned with content system (`margin-top: 140px`, `Montserrat-SemiBold 600`, `32px`, `#FFFFFF` text, `#FD6794` background, `border-radius: 32px`, `padding: 24px 48px`).

---

### 4. Renderer Adapter (`renderer.py`)

Deterministic browser-based rendering engine using system Headless Chromium:

```bash
python template-engine/templates/T01-miror-text-carousel/renderer.py
```

Outputs saved to:
- [output/previews/MIROR-T01-S01.png](file:///d:/MIROR-SOCIAL-AUTOMATION/output/previews/MIROR-T01-S01.png) *(Locked & Preserved)*
- [output/previews/MIROR-T01-S02.png](file:///d:/MIROR-SOCIAL-AUTOMATION/output/previews/MIROR-T01-S02.png) *(Locked & Preserved)*
- [output/previews/MIROR-T01-S03.png](file:///d:/MIROR-SOCIAL-AUTOMATION/output/previews/MIROR-T01-S03.png) *(Newly Rendered)*

---

### 5. Automated QA Checks (`validate_t01_slide3.py`)

Run 20-point QA verification for Slide 3:

```bash
python template-engine/tests/validate_t01_slide3.py
```
