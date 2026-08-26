# MIROR T01 Renderer API Production Deployment Guide

## 1. Overview & System Status
This guide describes how to build, configure, run, and test the production Docker container for the **MIROR T01 Renderer API**.

> **Important Integration Status Notices:**  
> - **MAKE.COM IS NOT CONNECTED YET.**  
> - **INSTAGRAM IS NOT CONNECTED YET.**  
> - **HOSTINGER DEPLOYMENT IS NOT COMPLETED YET.**  
>  
> Cloudinary is integrated as the persistent CDN image storage layer for containerized environments.

---

## 2. Docker Container Configuration

- **Base Image:** `python:3.10-slim`
- **Exposed Port:** `${PORT:-8000}` (Default: `8000`, listening on `0.0.0.0`)
- **Browser Runtime:** Playwright Headless Chromium binary installed via `python -m playwright install --with-deps chromium`
- **Production Assets:** Pre-packaged `LOGO-001.png` logo binary & local Montserrat font family (`Montserrat-Bold.ttf`, `Montserrat-Medium.ttf`, `Montserrat-SemiBold.ttf`)

---

## 3. Environment Variables & Storage Selection

| Variable Name | Default | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | HTTP listening port for Uvicorn. |
| `STORAGE_BACKEND` | `local` | Storage adapter backend (`local` or `cloudinary`). |
| `CLOUDINARY_CLOUD_NAME` | *None* | Required when `STORAGE_BACKEND=cloudinary`. |
| `CLOUDINARY_API_KEY` | *None* | Required when `STORAGE_BACKEND=cloudinary`. |
| `CLOUDINARY_API_SECRET` | *None* | Required when `STORAGE_BACKEND=cloudinary`. |

---

## 4. Docker Build & Run Instructions

### 4.1 Build Docker Image
```bash
docker build -t miror-renderer-api:latest .
```

### 4.2 Run Container with Cloudinary Storage
```bash
docker run -d \
  -p 8000:8000 \
  -e PORT=8000 \
  -e STORAGE_BACKEND=cloudinary \
  -e CLOUDINARY_CLOUD_NAME=your_cloud_name \
  -e CLOUDINARY_API_KEY=your_api_key \
  -e CLOUDINARY_API_SECRET=your_api_secret \
  --name miror-renderer \
  miror-renderer-api:latest
```

---

## 5. Storage Architecture & Ephemeral Storage Protection

Container-local filesystem storage (`output/renders/`) is **ephemeral**. By configuring `STORAGE_BACKEND=cloudinary`, rendered PNG images are automatically uploaded to Cloudinary CDN and returned as persistent HTTPS URLs (`https://res.cloudinary.com/...`).

Detailed storage documentation is available in [docs/cloudinary-storage.md](file:///d:/MIROR-SOCIAL-AUTOMATION/docs/cloudinary-storage.md).
