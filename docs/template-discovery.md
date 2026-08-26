# MIROR Template Discovery & Instagram Design System

This document synthesizes the empirical visual analysis of 40 Instagram reference assets into discovered visual families, design system parameters, carousel structures, and recommended production templates for the MIROR Social Automation system.

---

## 1. Evaluation of Existing Initial Placeholder Templates

The six initial project template directories were placeholders. Based on visual cluster analysis, here is how they map to actual empirical MIROR reference patterns:

| Placeholder Folder | Empirical Status | Discovery Recommendation |
| :--- | :--- | :--- |
| `T01-bold-typographic` | Strongly Confirmed | **RETAIN & REFINE** as **Family 1: Bold Typographic Pop-Block**. Captures high-energy pop-art text blocks (`REF-IG-001..004`, `009`, `011`, `013`, `024`). |
| `T02-photographic-editorial` | Confirmed | **RETAIN & RENAME** to **Family 3: Photographic Lifestyle & Grid**. Captures real-life photo overlays, 2-card grids (`REF-IG-018..022`), and editorial covers (`REF-IG-016`, `025`, `026`, `040`). |
| `T03-soft-editorial` | Confirmed | **RETAIN & RENAME** to **Family 2: Soft Editorial 3D Hero**. Captures soft pink pastel backgrounds with 3D hero assets (`REF-IG-005`, `008`, `031`, `032`, `034`). |
| `T04-medical-educational` | Confirmed | **RETAIN & RENAME** to **Family 4: Structured Data & Medical**. Captures 4-callout 3D organ diagrams (`REF-IG-036`, `038`, `039`), 2-column comparative tables (`REF-IG-029`), and 2x2 icon grids (`REF-IG-037`). |
| `T05-product-app` | Confirmed | **RETAIN & REFINE** as **Family 5: Product & Conversion CTA**. Captures app phone mockups (`REF-IG-004`, `033`) and text/pill button CTAs (`REF-IG-023`, `027`). |
| `T06-community-story` | Unconfirmed in Current Set | **MERGE / REPURPOSE** into Family 5 (App Community CTAs) or hold for future user story carousels. |

---

## 2. Visual Family Clustering Table

| Candidate Family | Represented References | Core Structure | Fixed Elements | Variable Elements | Reusability | Confidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Family 1: Bold Typographic Pop-Block** | `REF-IG-001`, `002`, `003`, `004`, `009`, `011`, `013`, `014`, `024` | Dark purple canvas (`#3E3353`), stacked angled color blocks containing bold white/dark copy, vector doodle accents, checkmark cards. | Logo top-left in pink square badge, dark background, bold stacked blocks, Montserrat 700 Bold copy. | Block colors (white/pink/orange/yellow), text strings, checkmark list items, accent doodle type. | HIGH | HIGH |
| **Family 2: Soft Editorial 3D Hero** | `REF-IG-005`, `008`, `031`, `032`, `034` | Soft blush pink background (`#FDF8F5`), giant bold headline, central 3D hero asset (calendar, hourglass, orchid-uterus) with falling petals. | Logo top-left in black square badge, blush pink background, editorial layout rhythm. | Headline text, 3D hero render asset, secondary text alignment (left vs center). | HIGH | HIGH |
| **Family 3: Photographic Lifestyle & Grid** | `REF-IG-016`, `018`, `019`, `020`, `021`, `022`, `025`, `026`, `040` | Soft warm beige background (`#FDF8F5`), lifestyle photography of women, 2-card rounded photo stack with glowing red pain highlights. | Logo top-left in black square badge, beige background color, card corner radius (~24px), Montserrat font hierarchy. | Photo image assets, pain highlight coordinates, card titles ("SHOULDERS", "KNEES"), headline copy. | HIGH | HIGH |
| **Family 4: Structured Data & Medical** | `REF-IG-012`, `015`, `029`, `036`, `037`, `038`, `039` | Soft blush or beige background, structured data container (4-callout 3D diagram, 2-column comparative table, 2x2 icon grid, 3-step vertical process). | Logo top-left badge, background canvas, card corner radii (~16-24px), typography rules. | Center 3D diagram asset or table rows, card label strings, icon SVGs. | HIGH | HIGH |
| **Family 5: Product & Conversion CTA** | `REF-IG-004`, `014`, `023`, `027`, `033`, `040` | High-contrast CTA slide, prominent app download messaging, 3D smartphone mockup or centered purple/pink CTA button box. | Action headline style, MIROR app branding, official logo badge. | Headline question, button copy ("Download the miror App" / "Fill a simple form"), mockup screen asset. | HIGH | HIGH |

---

## 3. Carousel Architecture Analysis

Out of 40 Instagram references, 100% belong to multi-slide educational/conversion carousels. The carousels exhibit a consistent 4-part structural rhythm:

```
[Slide 1: COVER]  ──►  [Slides 2-N: CONTENT/DIAGRAMS]  ──►  [Slide N+1: SUMMARY/CHECKLIST]  ──►  [Final Slide: CTA]
```

### Structural Components

1. **Cover Slide (Slide 1):**
   - **Purpose:** Hooks user attention with a bold symptom question or concept.
   - **Pattern:** Either giant stacked typographic blocks (`REF-IG-001`, `009`) OR high-impact 3D hero rendering (`REF-IG-005`, `032`) OR striking lifestyle photo (`REF-IG-016`, `025`, `035`).
   - **Fixed:** Top-left `LOGO-001` badge, prominent title.

2. **Internal Content Slides (Slides 2 to N-1):**
   - **Purpose:** Explains symptoms, medical causes, or anatomical comparisons.
   - **Pattern:** Uses structured components:
     - 2-Card Photo Grid (`REF-IG-018` through `022`)
     - 4-Callout 3D Organ Diagram (`REF-IG-036`, `038`, `039`)
     - 2-Column Comparative Table (`REF-IG-029`)
     - 3-Step Process Flowchart (`REF-IG-012`)
   - **Fixed:** Carousel navigation arrow at bottom-right, logo top-left.

3. **Summary / Checklist Slide (Slide N-1):**
   - **Purpose:** Summarizes warning signs or key takeaways.
   - **Pattern:** 4-Item Checkbox List (`REF-IG-015`) or 2x2 Medical Icon Grid (`REF-IG-037`).

4. **Final CTA Slide (Final Slide):**
   - **Purpose:** Drives user conversion to download the MIROR app or consult experts.
   - **Pattern:** 3D smartphone mockup display (`REF-IG-004`, `033`) or solid color CTA pill button (`REF-IG-023`) or prominent box banner (`REF-IG-027`).

---

## 4. MIROR Instagram Design System Discovery

Every design system rule identified from the reference analysis is explicitly categorized into **OBSERVED**, **INFERRED**, or **REQUIRES_CONFIRMATION**.

### A. Canvas & Outer Layout
- `OBSERVED`: Square (1:1 aspect ratio, 1080x1080) and portrait (4:5 aspect ratio, 1080x1350) post formats are present in Instagram feeds.
- `OBSERVED`: Top-left corner is strictly reserved for the official `LOGO-001` badge in all branded templates.
- `INFERRED`: Outer safe padding is approximately 6% to 8% of canvas width (~64px to 80px on a 1080px canvas).
- `REQUIRES_CONFIRMATION`: Standard production resolution export (whether 1080x1080 standard vs 1080x1350 portrait is the default for all future automated post renders).

### B. Logo Treatment
- `OBSERVED`: `LOGO-001` is rendered inside a square badge with rounded corners.
- `OBSERVED`: Badge background color alternates between Bright Pink (`#FD6794`) on dark purple posts and Black/Dark Purple (`#3E3353`) on light blush/beige posts.
- `OBSERVED`: The logo mark itself is never modified, rotated, or recolored.
- `INFERRED`: Logo badge width is approximately 7% to 8% of canvas width (~80px on 1080px canvas).
- `REQUIRES_CONFIRMATION`: Exact top-left pixel anchor offset (e.g. `top: 60px; left: 60px`).

### C. Typography Rules
- `OBSERVED`: Primary typeface across 100% of posts is **Montserrat**.
- `OBSERVED`: Hierarchy mapping:
  - **Major Headline:** Montserrat 700 Bold / Extra Bold.
  - **Secondary Emphasis / Italic Highlight:** Montserrat 600 SemiBold (often styled in pink italic).
  - **Body Text / Card Labels / List Items:** Montserrat 500 Medium.
  - **CTA Text:** Montserrat 500 Medium or 700 Bold.
- `INFERRED`: Headline text wrapping is tightly controlled (maximum 3-4 words per line).
- `REQUIRES_CONFIRMATION`: Exact Instagram-specific font size scaling table (e.g. Headline = 64px, Subhead = 36px, Body = 24px for 1080x1080 canvas). Website font sizes must NOT be reused directly.

### D. Color Palette Rules
- `OBSERVED`: Core Brand Colors:
  - **Primary Dark Purple:** `#3E3353`
  - **Primary Magenta Pink:** `#FD6794`
  - **Primary White:** `#FFFFFF`
  - **Soft Blush Pink Background:** `#FDF8F5` / `#F9ECE8`
  - **Soft Warm Beige Background:** `#FDF8F5`
  - **Accent Yellow:** `#FFB800`
  - **Accent Orange:** `#FF6B35`
  - **Muted Text Purple:** `#625972`
- `INFERRED`: Light background posts (blush pink or warm beige) represent ~70% of educational content, while dark purple background posts represent ~30% (high-impact pop-art or cover posts).
- `REQUIRES_CONFIRMATION`: Strict color pairing matrix allowed per template family.

### E. Cards & Components
- `OBSERVED`: Card containers feature rounded corners (`border-radius: 16px` to `24px`).
- `OBSERVED`: Photo grid cards (`REF-IG-018..022`) use a dark bottom linear gradient overlay (`rgba(0,0,0,0) to rgba(0,0,0,0.7)`) to ensure high contrast for white Montserrat typography.
- `OBSERVED`: Callout cards in 3D diagrams (`REF-IG-036`, `038`, `039`) are white rounded pill boxes with faint border outlines and subtle drop shadows.

---

## 5. Recommended Production Template Architecture

To maximize automation efficiency, deterministic HTML/CSS rendering, and brand consistency while reproducing 100% of the reference ecosystem, we recommend **5 Core Production Templates**:

```
                                  MIROR TEMPLATE ENGINE
                                            │
    ┌───────────────────┬───────────────────┼───────────────────┬───────────────────┐
    ▼                   ▼                   ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  TEMPLATE 1  │    │  TEMPLATE 2  │    │  TEMPLATE 3  │    │  TEMPLATE 4  │    │  TEMPLATE 5  │
│     Bold     │    │Soft Editorial│    │ Photographic │    │ Structured   │    │  Product &   │
│  Typographic │    │   3D Hero    │    │  Photo Grid  │    │ Data Diagram │    │Conversion CTA│
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

### Template 1: `T01-bold-typographic`
- **Template ID:** `T01-bold-typographic`
- **Template Name:** Bold Typographic Pop-Block
- **Represented References:** `REF-IG-001`, `REF-IG-002`, `REF-IG-003`, `REF-IG-009`, `REF-IG-011`, `REF-IG-013`, `REF-IG-024`
- **Core Layout:** Dark purple canvas (`#3E3353`). Stacked colored rectangular text block containers (`.block-card`) with slight offset rotation and drop shadows. Optional checkmark list cards below headline stack.
- **Content Fields:** `headline_lines` (array of string + color pairs), `subtext` (string), `list_items` (optional array of checkmark items), `accent_doodle` (starburst/arrow/circle).
- **Logo Behavior:** `LOGO-001` in pink square badge anchored top-left.
- **Typography Behavior:** Montserrat 700 Bold inside colored blocks; automatic text size adjustment based on string length.
- **Color Behavior:** Dark background `#3E3353`; blocks alternate White, Pink `#FD6794`, Orange `#FF6B35`, Yellow `#FFB800`.
- **Complexity:** LOW (Pure HTML/CSS flexbox + transform block stack).
- **Confidence:** HIGH

---

### Template 2: `T02-soft-editorial-hero`
- **Template ID:** `T02-soft-editorial-hero`
- **Template Name:** Soft Editorial 3D Hero
- **Represented References:** `REF-IG-005`, `REF-IG-008`, `REF-IG-031`, `REF-IG-032`, `REF-IG-034`
- **Core Layout:** Soft blush pink background (`#FDF8F5`). 2-column editorial split: left column bold Montserrat typography, right column 3D hero image render asset (calendar, hourglass, flowers).
- **Content Fields:** `headline` (string), `highlight_word` (pink italic string), `subtext` (string), `hero_image_url` (path to 3D asset).
- **Logo Behavior:** `LOGO-001` in dark purple square badge anchored top-left.
- **Typography Behavior:** Left-aligned Montserrat 700 Bold headline + 600 SemiBold pink accent.
- **Color Behavior:** Background `#FDF8F5`; copy `#3E3353` and `#FD6794`.
- **Complexity:** MEDIUM (Requires high quality 3D asset input).
- **Confidence:** HIGH

---

### Template 3: `T03-photo-lifestyle-grid`
- **Template ID:** `T03-photo-lifestyle-grid`
- **Template Name:** Photographic Lifestyle & 2-Card Grid
- **Represented References:** `REF-IG-016`, `REF-IG-018`, `REF-IG-019`, `REF-IG-020`, `REF-IG-021`, `REF-IG-022`, `REF-IG-025`, `REF-IG-026`, `REF-IG-040`
- **Core Layout:** Soft warm beige background (`#FDF8F5`). Supports 2 modes:
  1. *Cover Mode:* Top headline copy + bottom photographic figure cutout.
  2. *2-Card Mode:* Stacked vertical container holding 2 rounded photo cards (`border-radius: 20px`) with gradient dark bottom overlay for white text and red radial glow pain indicators.
- **Content Fields:** `layout_mode` ("cover" | "two_card"), `headline` (string), `card_1` (`{ image, title, subtitle, pain_x, pain_y }`), `card_2` (`{ image, title, subtitle, pain_x, pain_y }`).
- **Logo Behavior:** `LOGO-001` in dark purple square badge anchored top-left.
- **Typography Behavior:** Card titles in Montserrat 700 Bold all-caps white; subtext in Montserrat 500 Medium white.
- **Color Behavior:** Soft beige canvas `#FDF8F5`; dark gradient overlay `#000000` to `rgba(0,0,0,0.7)`.
- **Complexity:** MEDIUM (HTML/CSS card grid with dynamic CSS radial red glow overlays).
- **Confidence:** HIGH

---

### Template 4: `T04-structured-data-diagram`
- **Template ID:** `T04-structured-data-diagram`
- **Template Name:** Structured Data & Medical Diagram
- **Represented References:** `REF-IG-012`, `REF-IG-015`, `REF-IG-029`, `REF-IG-036`, `REF-IG-037`, `REF-IG-038`, `REF-IG-039`
- **Core Layout:** Soft blush background (`#FDF8F5`). Supports 3 structured sub-layouts:
  1. *4-Callout Diagram:* Central 3D anatomical render surrounded by 4 rounded white callout cards connected via red lines.
  2. *2-Column Table:* 2-column comparative table card ("Hormonal" vs "Injury") with header color bar and bullet list rows.
  3. *2x2 Icon Grid:* Symmetrical 2x2 grid of circular medical icon badges with text labels below.
- **Content Fields:** `diagram_type` ("4_callout" | "comparison_table" | "2x2_grid"), `title` (string), `center_asset_url` (image path), `items` (array of objects containing label, text, icon).
- **Logo Behavior:** `LOGO-001` in dark purple square badge anchored top-left.
- **Typography Behavior:** Title Montserrat 700 Bold `#3E3353`; card labels Montserrat 600 SemiBold.
- **Color Behavior:** Soft blush canvas `#FDF8F5`; white cards `#FFFFFF` with pink border accents `#FD6794`.
- **Complexity:** MEDIUM-HIGH (Requires SVG connecting lines or structured flexbox positioning).
- **Confidence:** HIGH

---

### Template 5: `T05-product-conversion-cta`
- **Template ID:** `T05-product-conversion-cta`
- **Template Name:** Product & Conversion CTA
- **Represented References:** `REF-IG-004`, `REF-IG-014`, `REF-IG-023`, `REF-IG-027`, `REF-IG-033`
- **Core Layout:** High-contrast carousel ending slide. Displays headline question, secondary value proposition, and prominent conversion element (either 3D smartphone app mockup displaying MIROR app screen OR solid dark purple/pink CTA pill button).
- **Content Fields:** `headline` (string), `subheadline` (string), `cta_type` ("app_mockup" | "pill_button" | "box_banner"), `button_text` (string), `app_screen_image` (optional string).
- **Logo Behavior:** `LOGO-001` top-left badge.
- **Typography Behavior:** Action headline Montserrat 700 Bold; CTA button text Montserrat 500 Medium / 700 Bold.
- **Color Behavior:** Flexible (Dark purple `#3E3353` or Soft blush `#FDF8F5`).
- **Complexity:** LOW-MEDIUM.
- **Confidence:** HIGH
