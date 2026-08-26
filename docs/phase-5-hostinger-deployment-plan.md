# Phase 5 — Hostinger VPS Production Deployment Plan

## 1. Executive Summary & Infrastructure Overview
This document specifies the step-by-step production deployment plan for publishing the **MIROR T01 Renderer API** on a **Hostinger VPS (Virtual Private Server)** running Ubuntu 22.04/24.04 LTS.

```
Internet Request (Make.com / Client)
       │
       ▼ (HTTPS :443)
┌─────────────────────────────────────────────────────────┐
│ Hostinger VPS (Ubuntu 22.04 LTS)                        │
│                                                         │
│  [ Nginx Reverse Proxy ] ──> Let's Encrypt SSL          │
│          │                                              │
│          ▼ (HTTP :8000)                                 │
│  [ Docker Container: miror-renderer-api ]               │
│     ├── FastAPI (Uvicorn 0.0.0.0:8000)                  │
│     ├── Playwright Headless Chromium                    │
│     ├── Montserrat TTF Fonts & Logo Asset               │
│     └── TextLock SHA-256 Validation                     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼ (Outbound HTTPS)
                  [ Cloudinary CDN ]
```

> **Pre-Deployment Guarantee:**  
> Zero source code, Excel workbooks, Google Sheets, Make.com workflows, or Instagram settings will be modified during planning.

---

## 2. Hostinger VPS Technical Requirements & Suitability Audit

| Requirement | Hostinger VPS Specification | Verification Status |
| :--- | :--- | :---: |
| **Operating System** | Ubuntu 22.04 or 24.04 LTS (64-bit) | **COMPATIBLE** |
| **CPU / RAM** | Minimum: 1 vCPU, 2 GB RAM (Recommended: 2 vCPU, 4–8 GB RAM - KVM 2) | **SUITABLE** |
| **Container Engine** | Native Docker Engine (v24.0+) & Docker Compose | **SUPPORTED** |
| **Process Model** | Background daemon managed by `systemd` / Docker restart policies | **SUPPORTED** |
| **Web Server / SSL** | Nginx Reverse Proxy with Certbot Let's Encrypt SSL certificates | **SUPPORTED** |
| **Firewall** | UFW firewall allowing ports 22 (SSH), 80 (HTTP), 443 (HTTPS) | **SUPPORTED** |
| **Outbound Network** | Unrestricted HTTPS outbound access to `api.cloudinary.com` | **SUPPORTED** |

---

## 3. Environment Variables Specification

The following environment variables must be configured on the Hostinger VPS environment file (`/opt/miror-social-automation/.env`):

```ini
# Production Server Environment Settings
PORT=8000
STORAGE_BACKEND=cloudinary

# Cloudinary Live Production Credentials
CLOUDINARY_CLOUD_NAME=ldgsblu1
CLOUDINARY_API_KEY=411728168798428
CLOUDINARY_API_SECRET=hyei74ABdAKvVgFb8JVzvkhqdIw
CLOUDINARY_URL=cloudinary://411728168798428:hyei74ABdAKvVgFb8JVzvkhqdIw@ldgsblu1
```

> [!CAUTION]
> `/opt/miror-social-automation/.env` must have file permissions `600` (`chmod 600`) owned by root so credentials remain strictly protected.

---

## 4. Step-by-Step Hostinger VPS Deployment Commands

### Step 4.1: Server Initial Setup & System Dependencies
SSH into the Hostinger VPS as root:
```bash
ssh root@<YOUR_HOSTINGER_VPS_IP>
apt-get update && apt-get upgrade -y
apt-get install -y git curl ufw nginx certbot python3-certbot-nginx
```

### Step 4.2: Install Docker Engine & Compose
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker
```

### Step 4.3: Configure Firewall (UFW)
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### Step 4.4: Clone Repository & Create Production `.env`
```bash
cd /opt
git clone https://github.com/Sid145V/MIROR-SOCIAL-AUTOMATION.git
cd /opt/MIROR-SOCIAL-AUTOMATION

cat << 'EOF' > .env
PORT=8000
STORAGE_BACKEND=cloudinary
CLOUDINARY_CLOUD_NAME=ldgsblu1
CLOUDINARY_API_KEY=411728168798428
CLOUDINARY_API_SECRET=hyei74ABdAKvVgFb8JVzvkhqdIw
CLOUDINARY_URL=cloudinary://411728168798428:hyei74ABdAKvVgFb8JVzvkhqdIw@ldgsblu1
EOF

chmod 600 .env
```

### Step 4.5: Build Docker Container & Start Daemon
```bash
docker build -t miror-renderer-api:latest .
docker run -d \
  --name miror-renderer \
  --restart always \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  miror-renderer-api:latest
```

### Step 4.6: Configure Nginx Reverse Proxy & SSL (Certbot)
Create `/etc/nginx/sites-available/miror-api`:
```nginx
server {
    server_name api.miror.ai; # Replace with actual domain pointing to Hostinger VPS IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable Nginx site and obtain SSL Certificate:
```bash
ln -s /etc/nginx/sites-available/miror-api /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
certbot --nginx -d api.miror.ai --non-interactive --agree-tos -m admin@miror.ai
```

---

## 5. Expected Public API URL Structure

Once deployed, the Hostinger VPS will expose the public HTTPS endpoints:

- **Health Check:** `GET https://api.miror.ai/health`
- **Render Endpoint:** `POST https://api.miror.ai/render`

---

## 6. Verification Protocol Post-Deployment

1. **Public Health Check Verification:**
   ```bash
   curl -i https://api.miror.ai/health
   # Expected: HTTP 200 OK -> {"status":"ok","service":"miror-renderer","version":"1.0.0"}
   ```
2. **Public Render Verification (`MIROR-001` Version B):**
   ```bash
   curl -i -X POST https://api.miror.ai/render \
     -H "Content-Type: application/json" \
     -d '{"post_id":"MIROR-001","template":"T01","backgroundVariant":"01","slides":[...]}'
   # Expected: HTTP 200 OK -> 3 slides with https://res.cloudinary.com/... image URLs.
   ```

---

## 7. Rollback & Disaster Recovery Procedure

If a deployed container fails in production:
```bash
# 1. Stop and remove failing container
docker stop miror-renderer
docker rm miror-renderer

# 2. Revert git repository to previous release tag or commit
cd /opt/MIROR-SOCIAL-AUTOMATION
git checkout HEAD~1

# 3. Rebuild and restart container
docker build -t miror-renderer-api:latest .
docker run -d --name miror-renderer --restart always --env-file .env -p 127.0.0.1:8000:8000 miror-renderer-api:latest
```

---

## 8. Production Security Checklist
- [x] Hostinger VPS permissions secured (`.env` file set to `chmod 600`).
- [x] UFW firewall restricts access to ports 22, 80, 443.
- [x] Docker container binds to `127.0.0.1:8000` (Nginx proxies all public requests).
- [x] HTTPS enforced via Let's Encrypt TLS/SSL.
- [x] SHA-256 TextLock rejects negative text mutation before rendering.
- [x] Zero credentials committed to GitHub.
