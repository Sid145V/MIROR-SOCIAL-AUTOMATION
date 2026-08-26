# MIROR T01 Background Color Variant & Contrast System Specification

## 1. System Architecture
The **T01 Background Color Variant & Contrast System** introduces a controlled, deterministic 5-background color palette to the T01 template engine without altering any layout geometry, typography sizes, margins, logo coordinates `(50, 50)`, or text lock specifications.

---

## 2. Approved 5-Background Color Palette

| Variant Key | Color Name | HEX Code | Text Theme | Primary Text | Secondary Text | CTA Background | CTA Text |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`01`** | **Soft Blush** | `#FDF8F5` | `dark` | `#3E3353` | `#625972` | `#FD6794` | `#FFFFFF` |
| **`02`** | **White** | `#FFFFFF` | `dark` | `#3E3353` | `#625972` | `#FD6794` | `#FFFFFF` |
| **`03`** | **Light Purple** | `#E9E2F2` | `dark` | `#3E3353` | `#625972` | `#FD6794` | `#FFFFFF` |
| **`04`** | **MIROR Purple** | `#3E3353` | `light` | `#FFFFFF` | `#FFFFFF` | `#FD6794` | `#FFFFFF` |
| **`05`** | **MIROR Pink** | `#FD6794` | `light` | `#FFFFFF` | `#FFFFFF` | `#3E3353` | `#FFFFFF` |

---

## 3. Deterministic 5-Day Rotation Formula

The system supports automatic 5-day cyclic rotation based on publishing day number:

$$\text{variant\_index} = ((\text{dayNumber} - 1) \bmod 5) + 1$$

- **Day 1:** Variant `01` (`#FDF8F5` Soft Blush)
- **Day 2:** Variant `02` (`#FFFFFF` White)
- **Day 3:** Variant `03` (`#E9E2F2` Light Purple)
- **Day 4:** Variant `04` (`#3E3353` MIROR Purple)
- **Day 5:** Variant `05` (`#FD6794` MIROR Pink)
- **Day 6:** Variant `01` (`#FDF8F5` Soft Blush) ...

> **Precedence Rule:** An explicit `"backgroundVariant": "03"` attribute in the payload overrides `dayNumber` when both are supplied.

---

## 4. Rendered Variant Outputs Directory

All 15 preview variations (5 variants × 3 slides) are generated at exact `1080 × 1350 px` resolution in:
- `output/previews/variants/MIROR-T01-V{01-05}-S{01-03}.png`

---

## 5. QA Verification Suite
Run the 25-point background variant QA test suite:

```bash
python template-engine/tests/validate_t01_background_variants.py
```
Result: `25/25 CHECKS PASSED` (including 17/17 Exact Text Lock regression checks).
