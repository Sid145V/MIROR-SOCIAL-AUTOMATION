# MIROR T01 Production Renderer API Dockerfile
FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr & set UTF-8
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install Linux system dependencies required by Playwright Chromium and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright Headless Chromium binary
RUN python -m playwright install --with-deps chromium

# Copy application source code and production assets
COPY api/ ./api/
COPY template-engine/ ./template-engine/
COPY assets/ ./assets/
COPY config/ ./config/
COPY docs/ ./docs/
COPY output/ ./output/

# Expose default port
EXPOSE 8000

# Healthcheck endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start FastAPI server listening on 0.0.0.0
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
