#!/usr/bin/env python3
"""SaktiLinux AI — Phase 2 tests.

Validates:
  - work-mode definitions (desktop/modes/*.json) against the schema
  - the theme generator produces valid KDE color schemes per accent
  - every mode references an existing wallpaper
  - plasmoid metadata is well-formed JSON with required fields
"""

import json
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "desktop"))

from schema import validate_all, VALID_ACCENTS  # noqa: E402

MODES_DIR = os.path.join(ROOT, "desktop", "modes")
WALLPAPERS_DIR = os.path.join(ROOT, "assets", "wallpapers")
PLASMOIDS_DIR = os.path.join(ROOT, "desktop", "plasmoids")

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


class TestModeDefinitions(unittest.TestCase):
    def test_all_modes_valid(self):
        reports = validate_all(MODES_DIR)
        self.assertEqual(reports, [], f"invalid mode definitions: {reports}")

    def test_required_modes_present(self):
        files = {name for name in os.listdir(MODES_DIR) if name.endswith(".json")}
        self.assertEqual(
            files,
            {"default.json", "developer.json", "designer.json", "cyber.json"},
        )

    def test_wallpapers_exist(self):
        for name in sorted(os.listdir(MODES_DIR)):
            if not name.endswith(".json"):
                continue
            data = load_json(os.path.join(MODES_DIR, name))
            wallpaper = os.path.join(WALLPAPERS_DIR, data["wallpaper"])
            self.assertTrue(
                os.path.isfile(wallpaper),
                f"{name}: missing wallpaper {data['wallpaper']}",
            )

    def test_accent_values_valid(self):
        for name in sorted(os.listdir(MODES_DIR)):
            if not name.endswith(".json"):
                continue
            data = load_json(os.path.join(MODES_DIR, name))
            self.assertIn(data["accent"], VALID_ACCENTS)

    def test_dock_never_empty(self):
        for name in sorted(os.listdir(MODES_DIR)):
            if not name.endswith(".json"):
                continue
            data = load_json(os.path.join(MODES_DIR, name))
            self.assertTrue(data["dock"], f"{name}: dock must not be empty")


class TestThemeSchemes(unittest.TestCase):
    def test_all_accents_have_schemes(self):
        scheme_dir = os.path.join(ROOT, "themes", "color-schemes")
        for accent in VALID_ACCENTS:
            path = os.path.join(scheme_dir, f"Sakti-{accent}.colors")
            self.assertTrue(os.path.isfile(path), f"missing scheme for {accent}")

    def test_scheme_format(self):
        scheme_dir = os.path.join(ROOT, "themes", "color-schemes")
        for name in os.listdir(scheme_dir):
            if not name.endswith(".colors"):
                continue
            with open(os.path.join(scheme_dir, name), encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("[General]", content)
            self.assertIn("[Colors:Window]", content)
            for line in content.splitlines():
                if "=" in line and line.split("=", 1)[1].strip():
                    value = line.split("=", 1)[1].strip()
                    if "," in value:
                        parts = value.split(",")
                        self.assertEqual(len(parts), 3)
                        for p in parts:
                            self.assertTrue(p.isdigit(), f"bad RGB value: {value}")


class TestPlasmoids(unittest.TestCase):
    def test_metadata_valid(self):
        for plasmoid in os.listdir(PLASMOIDS_DIR):
            meta = os.path.join(PLASMOIDS_DIR, plasmoid, "metadata.json")
            self.assertTrue(os.path.isfile(meta), f"missing metadata for {plasmoid}")
            data = load_json(meta)
            self.assertIn("KPlugin", data)
            self.assertEqual(data["KPlugin"]["Id"], plasmoid)
            self.assertEqual(data["KPackageStructure"], "Plasma/Applet")
            main_script = data.get("X-Plasma-MainScript", "ui/main.qml")
            main = os.path.join(PLASMOIDS_DIR, plasmoid, "contents", main_script)
            self.assertTrue(os.path.isfile(main), f"missing main.qml for {plasmoid}")


class TestWallpapers(unittest.TestCase):
    def test_wallpapers_valid_svg(self):
        for name in os.listdir(WALLPAPERS_DIR):
            if not name.endswith(".svg"):
                continue
            with open(os.path.join(WALLPAPERS_DIR, name), encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("<svg", content)
            self.assertIn("</svg>", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
