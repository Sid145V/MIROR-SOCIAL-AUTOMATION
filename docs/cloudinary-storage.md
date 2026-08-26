# MIROR Cloudinary Persistent Image Storage Specification

## 1. Overview & Purpose
In production container environments (Docker, Render, Hostinger), local container storage is ephemeral and reset upon restarts or container scaling. **Cloudinary** is integrated as the persistent CDN image-storage layer for the MIROR T01 Renderer API.

> **Status & Integration Notice:**  
> - **MAKE.COM IS NOT CONNECTED YET.**  
> - **INSTAGRAM IS NOT CONNECTED YET.**  
> - **HOSTINGER DEPLOYMENT IS NOT COMPLETED YET.**  
>  
> Cloudinary is added solely as the persistent storage layer for rendered T01 images.

---

## 2. Storage Architecture

The storage system uses an extensible factory pattern defined in `api/storage.py`:

```
                           StorageAdapter (Interface)
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
       LocalStorageAdapter                       CloudinaryStorageAdapter
    (Local File Workspace)                      (Production CDN Delivery)
                │                                             │
                ▼                                             ▼
  output/renders/{post_id}/                     Cloudinary CDN HTTPS URLs
  {post_id}_T01_{slide_id}.png                 https://res.cloudinary.com/...
```

The renderer engine (`T01HtmlRenderer`) produces the 1080×1350 PNG images locally, and the selected storage adapter handles persistence and URL resolution.

---

## 3. Environment Variables & Backend Selection

| Variable Name | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `STORAGE_BACKEND` | No | `local` | Storage adapter mode (`local` or `cloudinary`). |
| `CLOUDINARY_CLOUD_NAME` | If `cloudinary` | *None* | Cloudinary account cloud name. |
| `CLOUDINARY_API_KEY` | If `cloudinary` | *None* | Cloudinary API Key. |
| `CLOUDINARY_API_SECRET` | If `cloudinary` | *None* | Cloudinary API Secret Key. |

---

## 4. Deterministic Asset Structure

When uploading to Cloudinary, assets are organized deterministically:

- **Folder Path:** `MIROR/social-automation/{post_id}/`
- **Public ID:** `{post_id}_T01_{slide_id}`
- **Format:** `PNG` (Raw 1080×1350 resolution without cropping, resizing, or lossy transformations)
- **Overwrite Policy:** `overwrite=True` (Deterministic asset identification without random UUID duplicates)

---

## 5. API Response Schema

### 5.1 Local Storage Mode (`STORAGE_BACKEND=local`)
```json
{
  "success": true,
  "post_id": "MIROR-001",
  "template": "T01",
  "backgroundVariant": "01",
  "slides": [
    {
      "slide": "S01",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S01.png",
      "url": null
    }
  ]
}
```

### 5.2 Cloudinary Mode (`STORAGE_BACKEND=cloudinary`)
```json
{
  "success": true,
  "post_id": "MIROR-001",
  "template": "T01",
  "backgroundVariant": "01",
  "slides": [
    {
      "slide": "S01",
      "file": "output/renders/MIROR-001/MIROR-001_T01_S01.png",
      "url": "https://res.cloudinary.com/your-cloud/image/upload/v12345/MIROR/social-automation/MIROR-001/MIROR-001_T01_S01.png"
    }
  ]
}
```

---

## 6. Structured Error Handling & Security

If Cloudinary credentials are missing or an upload fails, the API returns a structured HTTP 400 JSON error:

```json
{
  "success": false,
  "error": {
    "code": "STORAGE_UPLOAD_FAILURE",
    "message": "Unable to persist rendered asset to Cloudinary CDN storage."
  }
}
```

**Security Rules:**
1. Zero hardcoded credentials in source code.
2. Credentials loaded strictly from environment variables.
3. No API secret keys printed in application logs or exposed in API error responses.
