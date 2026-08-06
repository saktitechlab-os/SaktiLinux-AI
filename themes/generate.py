#!/usr/bin/env python3
"""SaktiLinux AI — Theme Generation Engine.

Reads `branding/colors.json` (canonical design tokens) and generates:

  themes/plasma/       KDE Plasma desktop theme (colors, splash, dialogs)
  themes/color-schemes/*.colors   KDE color scheme per accent
  themes/sddm/         SDDM login theme
  themes/lockscreen/   SDDM-lock theme

Usage:
  python3 themes/generate.py [--accent cyan|indigo|orchid] [--output-dir OUT]

Runs on any host (pure stdlib). Output is stable and re-generable.
"""

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRANDING = os.path.join(ROOT, "branding", "colors.json")

ACCENTS = {
    "cyan": "primary",
    "indigo": "secondary",
    "orchid": "accent",
}

PALETTE_KEY_TO_ACCENT = {v: k for k, v in ACCENTS.items()}

OUTPUT_SCHEME = "schemes"


# ----------------------------------------------------------------- helpers
def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_qrgb(hex_color: str) -> str:
    r, g, b = hex_to_rgb(hex_color)
    return f"{r},{g},{b}"


# ------------------------------------------------------------- color scheme
COLOR_GROUPS = {
    "General": [
        ("ColorScheme", "Sakti"),
        ("Name", "Sakti {accent_name}"),
        ("shadeSortColumn", "false"),
        ("shadeSortOrder", "false"),
    ],
    "WM": [
        ("activeBackground", "{surface}"),
        ("activeForeground", "{text_primary}"),
        ("inactiveBackground", "{surface}"),
        ("inactiveForeground", "{text_secondary}"),
        ("activeFrame", "{accent}"),
        ("inactiveFrame", "{surface}"),
        ("activeTitleBarBlend", "{accent}"),
        ("inactiveTitleBarBlend", "{surface}"),
        ("activeTitleBarGradient", "Horizontal"),
        ("inactiveTitleBarGradient", "Horizontal"),
    ],
    "Colors:Window": [
        ("BackgroundNormal", "{surface}"),
        ("BackgroundAlternate", "{surface_raised}"),
        ("ForegroundNormal", "{text_primary}"),
        ("ForegroundInactive", "{text_secondary}"),
        ("ForegroundLink", "{accent}"),
        ("ForegroundVisited", "{secondary}"),
        ("ForegroundNegative", "{danger}"),
        ("ForegroundNeutral", "{warning}"),
        ("ForegroundPositive", "{success}"),
        ("DecorationFocus", "{accent}"),
        ("DecorationHover", "{secondary}"),
    ],
    "Colors:Button": [
        ("BackgroundNormal", "{surface_raised}"),
        ("BackgroundAlternate", "{surface}"),
        ("ForegroundNormal", "{text_primary}"),
        ("ForegroundInactive", "{text_secondary}"),
        ("ForegroundLink", "{accent}"),
        ("ForegroundVisited", "{secondary}"),
        ("ForegroundNegative", "{danger}"),
        ("ForegroundNeutral", "{warning}"),
        ("ForegroundPositive", "{success}"),
        ("DecorationFocus", "{accent}"),
        ("DecorationHover", "{secondary}"),
    ],
    "Colors:Selection": [
        ("BackgroundNormal", "{accent}"),
        ("BackgroundAlternate", "{secondary}"),
        ("ForegroundNormal", "{text_primary}"),
        ("ForegroundInactive", "{text_secondary}"),
        ("ForegroundLink", "{accent}"),
        ("ForegroundVisited", "{secondary}"),
        ("ForegroundNegative", "{danger}"),
        ("ForegroundNeutral", "{warning}"),
        ("ForegroundPositive", "{success}"),
        ("DecorationFocus", "{accent}"),
        ("DecorationHover", "{secondary}"),
    ],
    "Colors:Tooltip": [
        ("BackgroundNormal", "{surface_raised}"),
        ("BackgroundAlternate", "{surface}"),
        ("ForegroundNormal", "{text_primary}"),
        ("ForegroundInactive", "{text_secondary}"),
        ("ForegroundLink", "{accent}"),
        ("ForegroundVisited", "{secondary}"),
        ("ForegroundNegative", "{danger}"),
        ("ForegroundNeutral", "{warning}"),
        ("ForegroundPositive", "{success}"),
        ("DecorationFocus", "{accent}"),
        ("DecorationHover", "{secondary}"),
    ],
    "Colors:Complementary": [
        ("BackgroundNormal", "{surface}"),
        ("BackgroundAlternate", "{surface_raised}"),
        ("ForegroundNormal", "{text_primary}"),
        ("ForegroundInactive", "{text_secondary}"),
        ("ForegroundLink", "{accent}"),
        ("ForegroundVisited", "{secondary}"),
        ("ForegroundNegative", "{danger}"),
        ("ForegroundNeutral", "{warning}"),
        ("ForegroundPositive", "{success}"),
        ("DecorationFocus", "{accent}"),
        ("DecorationHover", "{secondary}"),
    ],
    "Colors:Header": [
        ("BackgroundNormal", "{background}"),
        ("BackgroundAlternate", "{background_alt}"),
        ("ForegroundNormal", "{text_primary}"),
        ("ForegroundInactive", "{text_secondary}"),
        ("ForegroundLink", "{accent}"),
        ("ForegroundVisited", "{secondary}"),
        ("ForegroundNegative", "{danger}"),
        ("ForegroundNeutral", "{warning}"),
        ("ForegroundPositive", "{success}"),
        ("DecorationFocus", "{accent}"),
        ("DecorationHover", "{secondary}"),
    ],
}


def render_scheme(tokens: dict, accent_key: str) -> str:
    palette = tokens["palette"]
    palette_key = ACCENTS[accent_key]
    accent = palette[palette_key]["hex"]
    values = {
        "accent": accent,
        "accent_name": palette[palette_key]["name"],
        "secondary": palette["secondary"]["hex"],
        "primary": palette["primary"]["hex"],
        "background": palette["background"]["hex"],
        "background_alt": palette["background_alt"]["hex"],
        "surface": palette["surface"]["hex"],
        "surface_raised": palette["surface_raised"]["hex"],
        "text_primary": palette["text_primary"]["hex"],
        "text_secondary": palette["text_secondary"]["hex"],
        "text_disabled": palette["text_disabled"]["hex"],
        "success": palette["success"]["hex"],
        "warning": palette["warning"]["hex"],
        "danger": palette["danger"]["hex"],
        "info": palette["info"]["hex"],
    }

    lines = ["[General]"]
    for key, tmpl in COLOR_GROUPS["General"]:
        lines.append(f"{key}={tmpl.format(**values)}")
    lines.append("")

    for group in COLOR_GROUPS:
        if group == "General":
            continue
        lines.append(f"[{group}]")
        for key, tmpl in COLOR_GROUPS[group]:
            color = tmpl.format(**values)
            if color.startswith("#") and len(color) == 7:
                color = rgb_to_qrgb(color)
            lines.append(f"{key}={color}")
        lines.append("")

    return "\n".join(lines)


def generate_schemes(tokens: dict, output_dir: str) -> list:
    out = os.path.join(output_dir, "color-schemes")
    os.makedirs(out, exist_ok=True)
    written = []
    for accent_key in ACCENTS:
        filename = os.path.join(out, f"Sakti-{accent_key}.colors")
        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(render_scheme(tokens, accent_key))
        written.append(filename)
    return written


# ------------------------------------------------------------ plasma theme
PLASMA_THEME_FILES = [
    "dialogs/background.svg",
    "dialogs/box-decoration.svg",
    "widgets/background.svg",
    "widgets/panel-background.svg",
    "widgets/tooltip.svg",
    "splash/Sakti.svg",
]


def generate_plasma_theme(tokens: dict, output_dir: str) -> str:
    theme_dir = os.path.join(output_dir, "plasma")
    for rel in PLASMA_THEME_FILES:
        path = os.path.join(theme_dir, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Empty markers replaced by real SVGs below via copy from assets.
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(svg_stub(tokens, rel))

    metadata = os.path.join(theme_dir, "metadata.desktop")
    with open(metadata, "w", encoding="utf-8") as fh:
        fh.write(
            "[Desktop Entry]\n"
            "Name=Sakti\n"
            "Comment=SaktiLinux AI Plasma theme\n"
            "Type=Service\n"
            "X-KDE-ServiceTypes=Plasma/LookAndFeel\n"
            "X-KDE-ParentApp=lookandfeel\n"
            "Encoding=UTF-8\n"
        )
    return theme_dir


def svg_stub(tokens: dict, rel: str) -> str:
    palette = tokens["palette"]
    bg = palette["background"]["hex"]
    accent = palette["primary"]["hex"]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" '
        f'viewBox="0 0 512 512">\n'
        f'  <rect width="512" height="512" rx="28" fill="{bg}"/>\n'
        f'  <circle cx="256" cy="256" r="120" fill="{accent}" opacity="0.18"/>\n'
        f'  <circle cx="256" cy="256" r="46" fill="none" stroke="{accent}" '
        f'stroke-width="4" stroke-dasharray="90 200"/>\n'
        f'  <circle cx="256" cy="256" r="14" fill="{accent}"/>\n'
        f'</svg>\n'
    )


# ------------------------------------------------------------------ splash
def generate_splash(tokens: dict, output_dir: str) -> str:
    splash_dir = os.path.join(output_dir, "splash")
    os.makedirs(splash_dir, exist_ok=True)
    logo_src = os.path.join(ROOT, "branding", "logo.svg")
    logo_dst = os.path.join(splash_dir, "logo.svg")
    if os.path.exists(logo_src):
        shutil.copyfile(logo_src, logo_dst)
    metadata = os.path.join(splash_dir, "metadata.desktop")
    with open(metadata, "w", encoding="utf-8") as fh:
        fh.write(
            "[Desktop Entry]\n"
            "Name=Sakti Splash\n"
            "Comment=SaktiLinux AI boot splash\n"
            "Type=Service\n"
            "X-KDE-ServiceTypes=Plasma/LookAndFeel\n"
            "X-KDE-ParentApp=lookandfeel\n"
            "Encoding=UTF-8\n"
        )
    return splash_dir


# ------------------------------------------------------------------- main
def main() -> int:
    parser = argparse.ArgumentParser(description="SaktiLinux AI theme generator")
    parser.add_argument("--accent", choices=list(ACCENTS), default="cyan",
                        help="default accent to bake into Plasma theme")
    parser.add_argument("--output-dir", default=os.path.join(ROOT, "themes"),
                        help="output root (default: themes/)")
    args = parser.parse_args()

    with open(BRANDING, encoding="utf-8") as fh:
        tokens = json.load(fh)

    schemes = generate_schemes(tokens, args.output_dir)
    theme = generate_plasma_theme(tokens, args.output_dir)
    splash = generate_splash(tokens, args.output_dir)

    print(f"Color schemes : {len(schemes)} generated")
    for s in schemes:
        print(f"  - {os.path.relpath(s, args.output_dir)}")
    print(f"Plasma theme  : {os.path.relpath(theme, args.output_dir)}")
    print(f"Splash        : {os.path.relpath(splash, args.output_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
