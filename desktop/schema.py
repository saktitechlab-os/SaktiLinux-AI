"""SaktiLinux AI — Desktop schema.

Defines the JSON schema for work-mode definitions under `desktop/modes/`.
A mode only *describes* UI (dock apps, shortcuts, widgets, accent) — it
never removes installed applications, only tunes what the shell shows.
"""

import json
import os

VALID_MODES = {"default", "developer", "designer", "cyber"}

VALID_SECTIONS = {
    "id": str,
    "label": str,
    "accent": str,          # cyan | indigo | orchid
    "wallpaper": str,       # relative path under assets/wallpapers/
    "dock": list,           # app IDs shown in the floating dock
    "launcher": list,       # app IDs in the start-menu grid
    "favorites": list,      # app IDs pinned to the launcher
    "widgets": list,        # widget IDs to place on the workspace
    "shortcuts": dict,      # { app:id -> keybinding }
    "setup": dict,          # optional setup extras
}

VALID_ACCENTS = {"cyan", "indigo", "orchid"}


def load_modes(package_dir: str) -> dict:
    """Load all mode JSON files into a {id: data} map."""
    modes = {}
    for name in sorted(os.listdir(package_dir)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(package_dir, name), encoding="utf-8") as fh:
            data = json.load(fh)
        modes[data["id"]] = data
    return modes


def validate_mode(data: dict) -> list:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    if "id" not in data:
        errors.append("missing 'id'")
        return errors
    if data["id"] not in VALID_MODES:
        errors.append(f"invalid mode id: {data['id']}")

    for field, _expected in VALID_SECTIONS.items():
        if field not in data:
            errors.append(f"missing '{field}'")
    if data.get("accent") not in VALID_ACCENTS:
        errors.append(f"invalid accent: {data.get('accent')}")
    return errors


def validate_all(modes_dir: str) -> list:
    """Validate every mode file, return list of (file, errors)."""
    reports = []
    for name in sorted(os.listdir(modes_dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(modes_dir, name)
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        errors = validate_mode(data)
        if errors:
            reports.append((name, errors))
    return reports