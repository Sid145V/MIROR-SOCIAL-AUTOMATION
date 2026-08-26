# Automated Test Suite

## Overview
This directory will contain the automated test suites for verifying template rendering and visual QA rules.

## Test Scope & Validation Areas
Automated tests implemented in future phases will validate:
- **Dimensions:** Verification that outputs match exact target aspect ratios (e.g. 1080x1080, 1080x1350, 1080x1920).
- **Template Structure:** Conformance to structural rules for each template layout (T01 through T06).
- **Text Overflow:** Detection of unclipped copy, overflow bounds, or unintended wrapping.
- **Logo Presence:** Verification that the official MIROR logo is correctly placed, unobstructed, and untampered.
- **Asset Availability:** Ensuring all referenced brand images, fonts, and graphics resolve prior to rendering.
- **Typography:** Verification of approved font family (Montserrat) and correct weight assignments (Bold 700, SemiBold 600, Medium 500).
- **Color Rules:** Verification that rendering uses approved palette colors (`#3E3353`, `#FFFFFF`, `#FD6794`).
- **Output Format:** Validating output image encoding (PNG/JPEG), metadata, and resolution.
- **Template Integrity:** Ensuring no missing elements, broken links, or unauthorized modifications occur during processing.
