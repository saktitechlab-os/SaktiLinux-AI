#!/usr/bin/env python3
"""SaktiLinux AI — package manifest validation.

Each manifest:
- one package per line
- '#' starts a comment
- no empty entries, no duplicates
- package names match Arch package naming rules

Usage: python3 tests/unit/test_packages.py packages/lists
"""

import os
import re
import sys
import unittest

ARCH_PKG_RE = re.compile(r"^[a-z0-9@._+-]+$")

# Manifests dir: first arg if provided and exists (direct invocation),
# otherwise the repository default. Survives `unittest discover` argv.
_MANIFESTS_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "packages", "lists",
)
MANIFESTS_DIR = (
    sys.argv[1]
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1])
    else _MANIFESTS_DEFAULT
)


def load_manifest(path):
    packages = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if line:
                packages.append(line)
    return packages


class TestManifests(unittest.TestCase):
    def test_all_manifests(self):
        for name in sorted(os.listdir(MANIFESTS_DIR)):
            if not name.endswith(".txt"):
                continue
            path = os.path.join(MANIFESTS_DIR, name)
            packages = load_manifest(path)
            self.assertTrue(packages, f"{name}: manifest is empty")

            seen = set()
            for pkg in packages:
                self.assertRegex(pkg, ARCH_PKG_RE,
                                 f"{name}: invalid package name '{pkg}'")
                self.assertNotIn(pkg, seen, f"{name}: duplicate package '{pkg}'")
                seen.add(pkg)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]], verbosity=2)
