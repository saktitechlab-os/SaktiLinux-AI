"""SaktiOS UI — Theme bridge.

Loads the brand palette (branding/colors.json) and exposes it both as a
plain dict for the JS client and as a flat `--var: value` CSS template
so the shell's live theme and the generated stylesheet stay in sync.
"""

from __future__ import annotations

import json
import os
from typing import Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLORS_FILE = os.path.join(ROOT, "branding", "colors.json")


class ThemeError(Exception):
    """Branding palette could not be loaded."""


def load_palette(path: str = COLORS_FILE) -> Dict[str, object]:
    if not os.path.exists(path):
        raise ThemeError(f"branding palette not found: {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def css_variables(palette: Dict[str, object]) -> str:
    """Flatten the palette into `:root { --sakti-*: ...; }`.

    Palette keys map onto the names the shell CSS actually uses
    (primary, secondary, accent, bg, bg-alt, surface, text, ...);
    everything else is emitted with its literal key.
    """
    rename = {
        "background": "bg", "background_alt": "bg-alt",
        "text_primary": "text", "text_secondary": "text-dim",
        "text_disabled": "text-disabled", "success": "ok",
    }

    def value(entry) -> str:
        if isinstance(entry, dict):
            return str(entry.get("hex") or entry.get("value") or "")
        return str(entry)

    lines = [":root {"]
    for group, section in palette.items():
        if not isinstance(section, dict):
            continue
        for key, entry in section.items():
            if not isinstance(entry, dict):
                continue
            css_name = (f"--sakti-{rename.get(key, key)}"
                        if group == "palette"
                        else f"--sakti-{group}-{key}")
            css_value = value(entry)
            if css_value:
                lines.append(f"  {css_name}: {css_value};")
    lines.append("}")
    return "\n".join(lines)


def theme_payload(palette: Dict[str, object]) -> Dict[str, object]:
    """JSON payload for GET /api/theme (keep it small on the wire)."""
    return {
        "palette": palette.get("palette", {}),
        "glass": palette.get("glass", {}),
        "typography": palette.get("typography", {}),
        "spacing": palette.get("spacing", {}),
    }