# MIROR T01 Renderer API Production Deployment Guide

## 1. System Architecture Overview
The **MIROR T01 Renderer API** is a containerized FastAPI application executing Playwright Headless Chromium to produce deterministic 1080×1350 Instagram carousel PNG slides.

```
                           GitHub (main branch)
                                    │
                                    ▼
                      Managed Container Platform
                     (Render / Railway / Cloud Run)
                                    │
                                    ▼
                  FastAPI Renderer API (0.0.0.0:${PORT})
                                    │
                      ┌─────────────┴─────────────┐
                      ▼                           ▼
               TextLock System             Cloudinary CDN
            (SHA-256 Validation)          (Persistent Images)
                      │
                      ▼
               Public HTTPS Response
```

---

## 2. Platform Requirements & Provider Selection

### Minimum Container Resource Specifications
- **Base Image:** `python:3.10-slim` (Linux x86_64)
- **Memory (RAM):** 1 GB minimum (2 GB recommended for Playwright Chromium execution)
- **CPU:** 1 vCPU
- **Outbound Network:** Public HTTPS access to `api.cloudinary.com` and `res.cloudinary.com`
- **Environment Support:** Dockerfile container deployment with custom environment variable injection and dynamic `PORT` binding.

### Platform Evaluation Matrix
- **Hostinger Shared Web Hosting:** **INCOMPATIBLE.** Does not support Docker containers, background Playwright Chromium headless processes, or persistent Uvicorn daemon execution.
- **Hostinger VPS:** **COMPATIBLE.** Requires manual Docker installation, systemd service management, and Nginx reverse proxy setup.
- **Render.com / Railway.app / Google Cloud Run (Recommended):** **OPTIMAL.** Native Dockerfile support, automatic HTTPS SSL certificates, dynamic port binding, zero infrastructure management, and automatic deployment on `git push origin main`.

---

## 3. Required Environment Variables Configuration

Configure the following variables in your provider's Web Dashboard:

| Variable Name | Required Value / Description | Sensitive? |
| :--- | :--- | :---: |
| `PORT` | Set automatically by platform (defaults to `8000`). | No |
| `STORAGE_BACKEND` | Set to `"cloudinary"` for production persistent image storage. | No |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud account name (e.g. `ldgsblu1`). | No |
| `CLOUDINARY_API_KEY` | Cloudinary API Key (e.g. `411728168798428`). | No |
| `CLOUDINARY_API_SECRET` | Cloudinary API Secret. | **YES (Keep Secret)** |
| `CLOUDINARY_URL` | `cloudinary://API_KEY:API_SECRET@CLOUD_NAME` | **YES (Keep Secret)** |

> [!CAUTION]
> NEVER commit `.env` or hardcode credentials into source code. Always use provider environment variable settings.

---

## 4. Container Build & Start Command
- **Build Command:** Built automatically via root [`Dockerfile`](file:///d:/MIROR-SOCIAL-AUTOMATION/Dockerfile).
- **Start Command:**
  ```bash
  sh -c "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"
  ```

---

## 5. Public API Endpoints

### 5.1 Health Check Endpoint
- **URL:** `GET https://<your-deployment-domain>/health`
- **Response Format (HTTP 200):**
  ```json
  {
    "status": "ok",
    "service": "miror-renderer",
    "version": "1.0.0"
  }
  ```

### 5.2 Render Carousel Endpoint
- **URL:** `POST https://<your-deployment-domain>/render`
- **Headers:** `Content-Type: application/json`
- **Request Body Payload Example (`MIROR-001` Version B):**
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
      ...
    ]
  }
  ```
- **Response Format (HTTP 200):**
  ```json
  {
    "success": true,
    "post_id": "MIROR-001",
    "template": "T01",
    "backgroundVariant": "01",
    "canvas": { "width": 1080, "height": 1350 },
    "slides": [
      { "slide": "S01", "file": "output/renders/MIROR-001/MIROR-001_T01_S01.png", "url": "https://res.cloudinary.com/..." },
      { "slide": "S02", "file": "output/renders/MIROR-001/MIROR-001_T01_S02.png", "url": "https://res.cloudinary.com/..." },
      { "slide": "S03", "file": "output/renders/MIROR-001/MIROR-001_T01_S03.png", "url": "https://res.cloudinary.com/..." }
    ]
  }
  ```

---

## 6. Maintenance & Operational Procedures

### How to Redeploy from GitHub
Any push to the `main` branch of `https://github.com/Sid145V/MIROR-SOCIAL-AUTOMATION.git` will automatically trigger a production build and zero-downtime deployment.

### How to Inspect Container Logs
Use your provider dashboard logs or CLI (e.g. `render logs`, `railway logs`, `gcloud logging`).

### How to Restart the Service
Trigger a manual deployment or service restart from the provider management console.

### Rollback Procedure
If a production issue occurs, revert the GitHub commit on `main` (`git revert HEAD && git push origin main`) to trigger an immediate automatic redeploy of the previous working state.
