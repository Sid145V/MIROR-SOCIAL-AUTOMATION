# Excel to MIROR T01 Renderer Data Contract Specification

## 1. Overview & Data Architecture
This document defines the formal data contract mapping operational rows in `MIROR_Content_Library.xlsx` (Sheet: `Content_Library`) to the structured JSON payloads expected by the **MIROR T01 Production Renderer API** (`POST /render`).

```
  [ MIROR_Content_Library.xlsx ] (Sheet: Content_Library)
               │
               ▼
   import_excel_content.py (Ingestion & Decomposition)
               │
               ├── 1. Schema Validation (Content ID, Status, Template ID)
               ├── 2. Structural Slide Parsing (Headline, Body Paragraphs, CTA)
               ├── 3. Text Lock SHA-256 Fingerprint Resolution
               │
               ▼
   FastAPI Renderer Input Payload (t01.schema.json)
               │
               ▼
    [ POST /render -> 3 PNG Slides + Storage ]
```

---

## 2. Comprehensive Field-by-Field Data Mapping Table

| Excel Column Name | Internal Field Name | Target Renderer JSON Field | Data Type | Validation & Formatting Rules | Visually Rendered? | Classification |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| `Content ID` | `content_id` | `post_id` / `content_id` | `String` | Pattern: `^MIROR-[0-9]{3,}$`. Must be non-empty and unique. | **NO** (Used for directory naming & asset IDs) | Input / ID |
| `Content Title` | `content_title` | `meta.title` | `String` | Descriptive topic title. Preserved for metadata. | **NO** | Metadata |
| `Objective` | `objective` | `meta.objective` | `String` | Campaign objective. Nullable. | **NO** | Metadata |
| `Type` | `type` | `meta.type` | `String` | Content category / pillar (e.g. `Symptom Recognition`). Nullable. | **NO** | Metadata |
| `SLIDE 1 — HOOK` | `slide1_raw` | `slides[0].headline.text` | `String` | Slide 1 Hook text block. Must be locked to `"lock": "EXACT"`. Newlines (`\n`) preserved. | **YES** (Slide 1 Headline) | Content Input |
| `SLIDE 2 — FOLLOW-THROUGH` | `slide2_raw` | `slides[1].headline.text` & `slides[1].body[].text` | `String / Array` | Parsed into transition headline (Block 1) and body paragraph list (Blocks 2+). All elements locked to `"lock": "EXACT"`. | **YES** (Slide 2 Headline & Body) | Content Input |
| `SLIDE 3 — CTA` | `slide3_raw` | `slides[2].headline.text`, `slides[2].body[].text` & `slides[2].cta.text` | `String / Array` | Parsed into closing headline (Block 1), body points, and final CTA button block (`JOIN THE MIROR COMMUNITY →\nLink in bio`). All elements locked to `"lock": "EXACT"`. | **YES** (Slide 3 Headline, Body & CTA) | Content Input |
| `Key Message` | `key_message` | `meta.key_message` | `String` | Core takeaways summary. Nullable. | **NO** | Metadata |
| `Supporting Context` | `supporting_context` | `meta.supporting_context` | `String` | Strategy advice. Nullable. | **NO** | Metadata |
| `Source` | `source` | `meta.source` | `String` | Content origin reference. Nullable. | **NO** | Metadata |
| `Priority` | `priority` | `meta.priority` | `String` | e.g., `High`, `Medium`. Nullable. | **NO** | Metadata |
| `Status` | `status` | `meta.status` | `String` | Must equal `"READY"` for active ingestion. Rows marked `"DRAFT"` or `"ARCHIVED"` are skipped. | **NO** | Control / Workflow |

---

## 3. Structural Decomposition Rules for Monolithic Excel Cells

Excel stores content as monolithic text strings in columns 5, 6, and 7. The ingestion tool decomposes these text blocks into the structured array format required by `t01.schema.json`:

### 3.1 Slide 1 (`SLIDE 1 — HOOK`)
- **Headline Text:** Entire cell string value with trailing whitespace trimmed.
- **Lock Attribute:** `"lock": "EXACT"`.

### 3.2 Slide 2 (`SLIDE 2 — FOLLOW-THROUGH`)
- **Headline (`headline.text`):** First paragraph block (text preceding the first double newline `\n\n`).
- **Body Paragraphs (`body[].text`):** Remaining paragraph blocks separated by double newlines `\n\n`. Each paragraph becomes an object `{"text": "...", "lock": "EXACT"}`.

### 3.3 Slide 3 (`SLIDE 3 — CTA`)
- **Headline (`headline.text`):** First paragraph block preceding double newline `\n\n`.
- **CTA Button (`cta.text`):** Final paragraph block containing `"JOIN THE MIROR"` or `"Link in bio"` or `"→"`. Formatted as `{"text": "JOIN THE MIROR COMMUNITY →\nLink in bio", "lock": "EXACT"}`.
- **Body Points (`body[].text`):** Intermediate paragraph blocks (if any), split by line breaks into individual bullet objects `{"text": "...", "lock": "EXACT"}`.

---

## 4. Optional Visual Controls & Defaults

| Parameter | Source in Excel | Default Value if Absent | Description |
| :--- | :--- | :--- | :--- |
| `template_id` | Implicit or Metadata | `"T01"` | Template identifier (restricted to `"T01"`). |
| `backgroundVariant` | Metadata / Strategy | `"01"` (or `dayNumber` cycle) | Approved color variant (`"01"` to `"05"`). |
| `canvas.width` | System Contract | `1080` | Canvas width in pixels. |
| `canvas.height` | System Contract | `1350` | Canvas height in pixels. |
