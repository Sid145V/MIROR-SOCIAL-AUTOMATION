# MIROR Social Automation

[![MIROR CI Pipeline](https://github.com/Sid145V/MIROR-SOCIAL-AUTOMATION/actions/workflows/ci.yml/badge.svg)](https://github.com/Sid145V/MIROR-SOCIAL-AUTOMATION/actions/workflows/ci.yml)

## Project
**MIROR Social Automation**

## Purpose
Production-grade automated Instagram content creation and publishing system for MIROR.

## Current Phase
**PRODUCTION TEMPLATE ENGINE & CI/CD VALIDATION**

## System Overview & Features
- **Master Template Engine:** `T01 MIROR 3-Slide Text-Only Carousel` (Hook, Follow-Through, CTA).
- **Exact Text Lock System:** Immutable text preservation & SHA-256 string fingerprinting.
- **Background Color Variants:** 5 approved variants (`#FDF8F5`, `#FFFFFF`, `#E9E2F2`, `#3E3353`, `#FD6794`) with deterministic 5-day cycle rotation & WCAG contrast enforcement.
- **Automated CI/CD Validation:** GitHub Actions continuous integration pipeline for 100% automated visual & text regression protection.

---

## Important Principles
1. **MIROR brand rules are authoritative.**
2. **Approved assets must be used** instead of AI recreations.
3. **The MIROR logo must never be regenerated.**
4. **Templates must be deterministic** and reusable.
5. **AI should provide intelligence and creative decisions** within approved rules.
6. **Final typography and logo rendering must be deterministic.**
7. **Every creative must pass QA** before publication.
8. **Missing required information must cause an explicit failure/escalation** rather than invention.
9. **Website references and Instagram references must remain separate.**
10. **Website typography measurements must NOT automatically be treated as Instagram measurements.**

---

## Confirmed Brand References
- **Primary Purple:** `#3E3353`
- **White:** `#FFFFFF`
- **Primary Pink:** `#FD6794`
- **Primary Typeface:** Montserrat
  - Major Headline: Montserrat 700 Bold
  - Secondary/Emphasis: Montserrat 600 SemiBold
  - Body/Supporting: Montserrat 500 Medium
  - CTA: Montserrat 600 SemiBold

> **Note:** These typography weights are confirmed brand references. Font sizes, line heights, margins, logo dimensions, spacing, and layout values are driven deterministically via machine-readable design specifications.
