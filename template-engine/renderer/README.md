# MIROR Creative Renderer Engine

## Overview
This directory will contain the template rendering engine for generating Instagram visual assets.

## Architectural Requirements & Specifications
The future renderer will:
- Use deterministic HTML/CSS or another deterministic rendering method to guarantee visual consistency.
- Produce exact Instagram dimensions (e.g. 1080x1080 square, 1080x1350 portrait, 1080x1920 story/reel).
- Use approved MIROR fonts (Montserrat font family with designated weights).
- Use the original, unmodified MIROR logo (never AI-recreated or modified).
- Use approved brand colors (`#3E3353`, `#FFFFFF`, `#FD6794`).
- Render exact copy and text without formatting or truncation errors.
- **Never rely on AI image generation to render final text or logos.**

> **Note:** Rendering stack dependencies (e.g., Playwright / Canvas / Puppeteer) will be selected and installed during the renderer development phase.
