#!/usr/bin/env python3
"""SaktiLinux AI — repository structure validation.

Verifies the Phase-1 mandated directory tree and key files exist.
Runs in CI and locally: python3 tests/unit/test_structure.py
"""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REQUIRED_DIRS = [
    "docs", "branding", "desktop", "ai", "kernel", "installer", "sdk",
    "packages", "runtime", "settings", "store", "terminal", "voice",
    "security", "plugins", "scripts", "themes", "tests", "assets", ".github",
]

REQUIRED_FILES = [
    "README.md",
    "CHANGELOG.md",
    "ROADMAP.md",
    "LICENSE",
    ".gitignore",
    "branding/logo.svg",
    "branding/colors.json",
    "branding/brand-guide.md",
    "docs/architecture/overview.md",
    "docs/architecture/ai-brain.md",
    "docs/architecture/runtime.md",
    "docs/architecture/security.md",
    "docs/architecture/desktop.md",
    "docs/guides/development.md",
    "docs/guides/contribution.md",
    "scripts/common/lib.sh",
    "scripts/bootstrap-base.sh",
    "scripts/build-iso.sh",
    "scripts/install-desktop.sh",
    "scripts/apply-user-shell.sh",
    "scripts/install-fonts.sh",
    "scripts/install-icons.sh",
    "desktop/mode_engine.py",
    "desktop/schema.py",
    "desktop/modes/default.json",
    "desktop/modes/developer.json",
    "desktop/modes/designer.json",
    "desktop/modes/cyber.json",
    "themes/generate.py",
    "themes/color-schemes/Sakti-cyan.colors",
    "themes/color-schemes/Sakti-indigo.colors",
    "themes/color-schemes/Sakti-orchid.colors",
    "themes/sddm/sakti-login/ui/main.qml",
    "assets/wallpapers/sakti-default.svg",
    "assets/icons/README.md",
    "assets/fonts/README.md",
    "tests/run-tests.sh",
    "tests/unit/test_structure.py",
    "tests/unit/test_packages.py",
    "tests/unit/test_desktop.py",
    ".github/workflows/ci.yml",
]

REQUIRED_PACKAGE_LISTS = ["base.txt", "dev.txt", "designer.txt", "cyber.txt"]


class TestStructure(unittest.TestCase):
    def test_required_directories(self):
        for d in REQUIRED_DIRS:
            self.assertTrue(
                os.path.isdir(os.path.join(ROOT, d)),
                f"missing directory: {d}/",
            )

    def test_required_files(self):
        for f in REQUIRED_FILES:
            self.assertTrue(
                os.path.isfile(os.path.join(ROOT, f)),
                f"missing file: {f}",
            )

    def test_package_manifests(self):
        lists_dir = os.path.join(ROOT, "packages", "lists")
        for name in REQUIRED_PACKAGE_LISTS:
            self.assertTrue(
                os.path.isfile(os.path.join(lists_dir, name)),
                f"missing package manifest: packages/lists/{name}",
            )

    def test_scripts_executable(self):
        for script in ["bootstrap-base.sh", "build-iso.sh"]:
            path = os.path.join(ROOT, "scripts", script)
            self.assertTrue(os.access(path, os.X_OK) or os.name == "nt",
                            f"script not executable: scripts/{script}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
