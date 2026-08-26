# MIROR Exact Text Lock & Text Integrity System Specification

## 1. System Philosophy & Objectives
The **MIROR Exact Text Lock & Text Integrity System** enforces a strict architectural guarantee: **The supplied content payload is sacred and immutable.**

The renderer is purely a **DESIGN ENGINE**, not a copywriting engine.
- **NO AI/LLM text rewriting**, summarizing, or paraphrasing.
- **NO string normalization:** `.strip()`, `.lower()`, `.upper()`, auto-capitalization, smart quote replacement, or punctuation removal are strictly forbidden.
- **EXACT STRING IMMUTABILITY:** Preserves exact capitalization, exact punctuation, exact spaces, and exact `\n` line breaks as supplied.
- **LOUDSPEAKER FAILURE:** If a text field is missing, empty, modified, or exceeds template bounds, rendering fails immediately with an explicit `TextLockError` or `TextFitError`.

---

## 2. Decoupled Architecture Layers

```
  +-------------------------------------------------------------+
  | 1. CONTENT LAYER (Excel / Google Sheets / Approved JSON)     |
  |    Supplies immutable text strings with `"lock": "EXACT"`.  |
  +-------------------------------------------------------------+
                               |
                               v
  +-------------------------------------------------------------+
  | 2. TEXT INTEGRITY LAYER (SHA-256 Fingerprint Validation)    |
  |    Validates presence, non-emptiness & SHA-256 hash match.    |
  +-------------------------------------------------------------+
                               |
                               v
  +-------------------------------------------------------------+
  | 3. DESIGN & ASSET LAYER (design-spec.json + Local TTF Fonts)|
  |    Provides machine-readable tokens and LOGO-001.png asset. |
  +-------------------------------------------------------------+
                               |
                               v
  +-------------------------------------------------------------+
  | 4. RENDER LAYER (Headless Chromium HTML/CSS Engine)         |
  |    Renders exact text to 1080x1350 PNG with 0 pixel loss.   |
  +-------------------------------------------------------------+
                               |
                               v
  +-------------------------------------------------------------+
  | 5. QA LAYER (Positive & Negative Mutation Test Suites)      |
  |    Verifies exact string matching & 100% mutation rejection.|
  +-------------------------------------------------------------+
```

---

## 3. Schema & Lock Attribute (`test_content_MIROR-T01-MASTER.json`)

```json
{
  "content_id": "MIROR-001",
  "template_id": "T01",
  "text_integrity": {
    "S01.headline": "063396046dd3d7c071578b82355938457d64033ddb054a9c1aedeb443eb9b829",
    "S02.headline": "a5e404e6ba6fbeb5b1463699a32a8a15a1022b19ca89ef75f68bd25d2641f36c",
    "S02.body.0": "49b3b0edbf75523c49a8879226fdf36036a89f32ad2905e7d11830126ff7ce62",
    "S02.body.1": "f77b2ffbd5d2acb300fe21820da9fb9641daf04607acb26de86bca801b09ad04",
    "S02.body.2": "cf3aa9184b88ad5e41220dec57888814c9ade1395efe2c9bdd8d2bd0d8aa2b69",
    "S03.headline": "cea00e0eea613159cbee70fc47741ec34166e362040146235c1ea73581f01912",
    "S03.body.0": "af7a74d9b9716b73643d709677de4458abff46d1c1054e1c66de340c3cd3c1f9",
    "S03.body.1": "5411f5332ff9d14314377077845a7b41910da3d4456b5a1854241573d5c8b0b0",
    "S03.body.2": "c3129a84799a4bc36a69c6494f037e6a838ae8847670649b78e81ec06d0917df",
    "S03.cta": "6f10515c8d2c2128de50f5cf6737d419d13facf1be12c0c55352b7bb0e0d0540"
  },
  "slides": [
    {
      "id": "S01",
      "headline": { "text": "YOU'RE TIRED.\nYOU CAN'T SLEEP.\nYOU'RE IRRITABLE.\n\nYOUR BODY IS TRYING\nTO TELL YOU SOMETHING.", "lock": "EXACT" }
    },
    {
      "id": "S02",
      "headline": { "text": "HERE'S WHAT MAY BE\nHAPPENING.", "lock": "EXACT" },
      "body": [
        { "text": "During perimenopause, your hormones can fluctuate significantly.", "lock": "EXACT" },
        { "text": "That can affect your periods, sleep, mood, energy, concentration and more.", "lock": "EXACT" },
        { "text": "The symptoms may not be separate.\nThey may be connected.", "lock": "EXACT" }
      ]
    },
    {
      "id": "S03",
      "headline": { "text": "START CONNECTING\nTHE DOTS.", "lock": "EXACT" },
      "body": [
        { "text": "Understand your symptoms.", "lock": "EXACT" },
        { "text": "Get expert guidance.", "lock": "EXACT" },
        { "text": "Talk to women going through it too.", "lock": "EXACT" }
      ],
      "cta": { "text": "JOIN THE MIROR COMMUNITY →\nLink in bio", "lock": "EXACT" }
    }
  ]
}
```

---

## 4. Automated Test Verification
Run the 17-point test suite:

```bash
python template-engine/tests/validate_t01_text_integrity.py
```

Result: `17/17 TESTS PASSED` (9 positive integrity checks + 8 negative mutation checks).
