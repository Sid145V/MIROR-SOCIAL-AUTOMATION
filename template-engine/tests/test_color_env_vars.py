"""
Automated Test Suite — MIROR T01 Environment Variable Color Configuration & Fallback Safety
"""

import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
core_dir = REPO_ROOT / "template-engine" / "core"
template_dir = REPO_ROOT / "template-engine" / "templates" / "T01-miror-text-carousel"

if str(core_dir) not in sys.path:
    sys.path.insert(0, str(core_dir))
if str(template_dir) not in sys.path:
    sys.path.insert(0, str(template_dir))

from text_lock import TextLockSystem
from renderer import T01HtmlRenderer

class TestColorEnvVars(unittest.TestCase):
    def setUp(self):
        self.renderer = T01HtmlRenderer(REPO_ROOT)
        # Clear color env vars before each test
        for k in ["MIROR_COLOR_01_HEX", "MIROR_COLOR_01_NAME",
                  "MIROR_COLOR_02_HEX", "MIROR_COLOR_02_NAME",
                  "MIROR_COLOR_03_HEX", "MIROR_COLOR_03_NAME"]:
            if k in os.environ:
                del os.environ[k]

    def tearDown(self):
        # Clear env vars after each test
        for k in ["MIROR_COLOR_01_HEX", "MIROR_COLOR_01_NAME",
                  "MIROR_COLOR_02_HEX", "MIROR_COLOR_02_NAME",
                  "MIROR_COLOR_03_HEX", "MIROR_COLOR_03_NAME"]:
            if k in os.environ:
                del os.environ[k]

    def test_1_no_env_vars_fallback(self):
        """TEST 1: No env vars -> existing spec colors are used."""
        spec_01 = self.renderer.get_variant_spec("01")
        spec_02 = self.renderer.get_variant_spec("02")
        spec_03 = self.renderer.get_variant_spec("03")

        self.assertEqual(spec_01["hex"].upper(), "#F8E3E7")
        self.assertEqual(spec_02["hex"].upper(), "#E7DDF2")
        self.assertEqual(spec_03["hex"].upper(), "#F6F0D8")

    def test_2_set_color_01_override(self):
        """TEST 2: Set MIROR_COLOR_01_HEX -> Variant 01 uses supplied HEX."""
        os.environ["MIROR_COLOR_01_HEX"] = "#FFC0CB"
        os.environ["MIROR_COLOR_01_NAME"] = "Custom Pink"
        spec_01 = self.renderer.get_variant_spec("01")

        self.assertEqual(spec_01["hex"], "#FFC0CB")
        self.assertEqual(spec_01["name"], "Custom Pink")

    def test_3_set_color_02_override(self):
        """TEST 3: Set MIROR_COLOR_02_HEX -> Variant 02 uses supplied HEX."""
        os.environ["MIROR_COLOR_02_HEX"] = "#D8BFD8"
        os.environ["MIROR_COLOR_02_NAME"] = "Thistle Purple"
        spec_02 = self.renderer.get_variant_spec("02")

        self.assertEqual(spec_02["hex"], "#D8BFD8")
        self.assertEqual(spec_02["name"], "Thistle Purple")

    def test_4_set_color_03_override(self):
        """TEST 4: Set MIROR_COLOR_03_HEX -> Variant 03 uses supplied HEX."""
        os.environ["MIROR_COLOR_03_HEX"] = "#FFF8DC"
        os.environ["MIROR_COLOR_03_NAME"] = "Cornsilk Cream"
        spec_03 = self.renderer.get_variant_spec("03")

        self.assertEqual(spec_03["hex"], "#FFF8DC")
        self.assertEqual(spec_03["name"], "Cornsilk Cream")

    def test_5_invalid_hex_fallback(self):
        """TEST 5: Invalid HEX strings fall back safely to default spec hex."""
        invalid_hexes = ["pink", "123456", "#FFF", "#GGGGGG", "", "   ", "#1234567"]
        for bad_hex in invalid_hexes:
            os.environ["MIROR_COLOR_01_HEX"] = bad_hex
            spec_01 = self.renderer.get_variant_spec("01")
            self.assertEqual(spec_01["hex"].upper(), "#F8E3E7", f"Failed to fall back for bad hex: '{bad_hex}'")

    def test_6_variants_04_05_unchanged(self):
        """TEST 6: Variants 04 and 05 remain completely unchanged."""
        spec_04 = self.renderer.get_variant_spec("04")
        spec_05 = self.renderer.get_variant_spec("05")

        self.assertEqual(spec_04["hex"].upper(), "#3E3353")
        self.assertEqual(spec_05["hex"].upper(), "#FD6794")

if __name__ == "__main__":
    unittest.main()
