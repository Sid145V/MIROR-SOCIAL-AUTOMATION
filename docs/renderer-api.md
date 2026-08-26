# MIROR T01 Production Renderer API Documentation

## 1. Purpose & Overview
The **MIROR T01 Production Renderer API** exposes the approved, deterministic HTML/CSS browser-based rendering engine as a lightweight, production-ready FastAPI service.

> **Status Notice:**  
> **MAKE.COM IS NOT CONNECTED YET.**  
> The API layer is currently prepared and fully testable locally as the standalone automation interface for MIROR content rendering.

---

## 2. Architecture Pipeline

```
[ External Request / JSON Payload ]
               │
               ▼
       FastAPI (/render)
               │
               ├── 1. Schema Validation (post_id, template="T01", slides)
               ├── 2. Exact Text Lock System (SHA-256 Fingerprint Matching)
               ├── 3. Background Variant Resolution ('01'-'05' or 5-day cycle)
               │
               ▼
   T01HtmlRenderer (Headless Chromium)
               │
               ▼
   Generated 1080 × 1350 PNG Outputs
   output/renders/{post_id}/{post_id}_T01_S01.png
   output/renders/{post_id}/{post_id}_T01_S02.png
   output/renders/{post_id}/{post_id}_T01_S03.png
               │
               ▼
    [ Structured JSON Response ]
```

---

## 3. Endpoints

### 3.1 `GET /health`
Verifies service health without executing browser rendering.

**Response (HTTP 200):**
```json
{
  "status": "ok",
  "service": "miror-renderer",
  "version": "1.0.0"
}
```

---

### 3.2 `POST /render`
Accepts a JSON payload representing a MIROR T01 carousel, enforces text integrity and background rules, renders all 3 slides (`S01`, `S02`, `S03`), and returns file paths.

#### Request Schema Example:
```json
{
  "post_id": "MIROR-001",
  "template": "T01",
  "backgroundVariant": "01",
  "slides": [
    {
      "id": "S01",
      "type": "hook",
      "headline": {
        "text": "YOU'RE TIRED.\nYOU CAN'T SLEEP.\nYOU'RE IRRITABLE.\n\nYOUR BODY IS TRYING\nTO TELL YOU SOMETHING.",
        "lock": "EXACT"
      }
    },
    {
      "id": "S02",
      "type": "follow-through",
      "headline": {
        "text": "HERE'S WHAT MAY BE\nHAPPENING.",
        "lock": "EXACT"
      },
      "body": [
        {
          "text": "During perimenopause, your hormones can fluctuate significantly.",
          "lock": "EXACT"
        },
        {
          "text": "That can affect your periods, sleep, mood, energy, concentration and more.",
          "lock": "EXACT"
        },
        {
          "text": "The symptoms may not be separate.\nThey may be connected.",
          "lock": "EXACT"
        }
      ]
    },
    {
      "id": "S03",
      "type": "cta",
      "headline": {
        "text": "START CONNECTING\nTHE DOTS.",
        "lock": "EXACT"
      },
      "body": [
        {
          "text": "Understand your symptoms.",
          "lock": "EXACT"
        },
        {
          "text": "Get expert guidance.",
          "lock": "EXACT"
        },
        {
          "text": "Talk to women going through it too.",
          "lock": "EXACT"
        }
      ],
      "cta": {
        "text": "JOIN THE MIROR COMMUNITY →\nLink in bio",
        "lock": "EXACT"
      }
    }
  ]
}
```

#### Successful Response Schema (HTTP 200):
```json
{
  "success": true,
  "post_id": "MIROR-001",
  "template": "T01",
  "backgroundVariant": "01",
  "canvas": {
    "width": 1080,
    "height": 1350
  },
  "slides": [
    {
      "slide": "S01",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S01.png"
    },
    {
      "slide": "S02",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S02.png"
    },
    {
      "slide": "S03",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S03.png"
    }
  ]
}
```

---

## 4. Structured Error Responses

If any validation or rendering step fails, the API returns a structured HTTP 400 or HTTP 500 JSON error payload:

```json
{
  "success": false,
  "error": {
    "code": "TEXT_LOCK_FAILURE",
    "message": "T01 TEXT LOCK FAILURE: Field 'S01.headline' hash mismatch.",
    "field": "S01"
  }
}
```

### Error Code Reference Table

| Code | HTTP Status | Description |
| :--- | :--- | :--- |
| `VALIDATION_ERROR` | `400` | Missing required fields (`post_id`, `template`, `slides`). |
| `SCHEMA_VALIDATION_ERROR` | `400` | Malformed JSON payload or invalid object structure. |
| `UNSUPPORTED_TEMPLATE` | `400` | Template ID is not `"T01"`. |
| `TEXT_LOCK_FAILURE` | `400` | Exact text validation failed due to character/punctuation mutation. |
| `BACKGROUND_VARIANT_ERROR` | `400` | Invalid `backgroundVariant` (must be `"01"`, `"02"`, `"03"`, `"04"`, `"05"`). |
| `RENDER_FAILURE` | `500` | Browser rendering process error. |
| `OUTPUT_FAILURE` | `500` | PNG file generation failed on disk. |

---

## 5. Local Startup & Command Testing

### 5.1 Start FastAPI Local Server
```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### 5.2 Test `/health` via `curl`
```bash
curl -X GET http://127.0.0.1:8000/health
```

### 5.3 Test `/render` via `curl`
```bash
curl -X POST http://127.0.0.1:8000/render \
  -H "Content-Type: application/json" \
  -d @template-engine/tests/test_content_MIROR-T01-MASTER.json
```

### 5.4 Run Automated API Test Suite
```bash
python api/tests/test_api.py
```
Output: `=== API QA SUMMARY: 14/14 TESTS PASSED ===`
