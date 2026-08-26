# MIROR T01 Renderer API Production Deployment Guide

## 1. Overview & System Status
This guide describes how to build, configure, run, and test the production Docker container for the **MIROR T01 Renderer API**.

> **Important Integration Status Notices:**  
> - **MAKE.COM IS NOT CONNECTED YET.**  
> - **INSTAGRAM IS NOT CONNECTED YET.**  
> - **EXTERNAL STORAGE (S3/CLOUD STORAGE) IS NOT CONNECTED YET.**  
>  
> The current milestone achieves **containerized deployment readiness** for the deterministic T01 rendering engine.

---

## 2. Docker Container Configuration

- **Base Image:** `python:3.10-slim`
- **Exposed Port:** `${PORT:-8000}` (Default: `8000`, listening on `0.0.0.0`)
- **Browser Runtime:** Playwright Headless Chromium binary installed via `python -m playwright install --with-deps chromium`
- **Production Assets:** Pre-packaged `LOGO-001.png` logo binary & local Montserrat font family (`Montserrat-Bold.ttf`, `Montserrat-Medium.ttf`, `Montserrat-SemiBold.ttf`)

---

## 3. Docker Build & Run Instructions

### 3.1 Build Docker Image
```bash
docker build -t miror-renderer-api:latest .
```

### 3.2 Run Docker Container
```bash
docker run -d \
  -p 8000:8000 \
  -e PORT=8000 \
  --name miror-renderer \
  miror-renderer-api:latest
```

---

## 4. In-Container Endpoint Verification

### 4.1 Health Check (`GET /health`)
```bash
curl -X GET http://localhost:8000/health
```
**Expected Output (HTTP 200):**
```json
{
  "status": "ok",
  "service": "miror-renderer",
  "version": "1.0.0"
}
```

### 4.2 Render Carousel (`POST /render`)
```bash
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d @template-engine/tests/test_content_MIROR-T01-MASTER.json
```
**Expected Output (HTTP 200):**
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
      "file": "output/renders/MIROR-001/MIROR-001_T01_S01.png",
      "url": "output/renders/MIROR-001/MIROR-001_T01_S01.png"
    },
    {
      "slide": "S02",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S02.png",
      "url": "output/renders/MIROR-001/MIROR-001_T01_S02.png"
    },
    {
      "slide": "S03",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S03.png",
      "url": "output/renders/MIROR-001/MIROR-001_T01_S03.png"
    }
  ]
}
```

---

## 5. Storage Architecture & Ephemeral Storage Warning

> **CRITICAL PRODUCTION NOTICE — FILE PERSISTENCE:**  
> Container-local filesystem storage (`output/renders/`) is **ephemeral**. Files stored inside a container do **NOT** survive container restarts or server scaling events.

### Storage Abstraction Design (`api/storage.py`)
The application defines an abstract `StorageAdapter` interface:

- `LocalStorageAdapter`: Used during local development and internal container workspace.
- `S3StorageAdapter` / `CloudStorageAdapter` *(Future Extension)*: Will upload rendered PNG images directly to AWS S3, Google Cloud Storage, or Cloudflare R2 and return HTTPS public URLs in the API response.

---

## 6. Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | HTTP port on which Uvicorn listens. |
| `MIROR_STORAGE_TYPE` | `local` | Storage backend adapter type (`local` or `s3`). |
| `PYTHONUNBUFFERED` | `1` | Ensures immediate log flushing to stdout/stderr. |
