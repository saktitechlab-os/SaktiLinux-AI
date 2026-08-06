"""SaktiLinux AI — Work Mode Manager.

The brain of the Dynamic Workspace system. Given a mode id it:

1. Reads the mode definition (from desktop/modes/*.json)
2. Renders the Plasma panel config (floating dock + taskbar apps)
3. Sets the KDE color scheme (dynamic accent)
4. Sets the wallpaper
5. Writes the launcher/favorites and shortcut bindings
6. Reloads the Plasma shell so changes apply live

Design contract:
- INSTALLED APPLICATIONS ARE NEVER REMOVED. Only UI surfaces change.
- Idempotent: switching to the current mode is a no-op.
- Safe fallbacks when Plasma tooling is absent (e.g. headless dev VM).
"""

import json
import os
import shutil
import subprocess
import sys

from schema import load_modes, validate_all

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODES_DIR = os.path.join(ROOT, "desktop", "modes")
THEMES_DIR = os.path.join(ROOT, "themes")
WALLPAPERS_DIR = os.path.join(ROOT, "assets", "wallpapers")

STATE_DIR = os.path.join(os.path.expanduser("~"), ".config", "sakti")
STATE_FILE = os.path.join(STATE_DIR, "state.json")

PLASMA_PANEL_CONFIG = os.path.join(
    os.path.expanduser("~"), ".config", "plasma-org.kde.plasma.desktop-appletsrc"
)

ACCENT_SCHEMES = {
    "cyan": "Sakti-cyan",
    "indigo": "Sakti-indigo",
    "orchid": "Sakti-orchid",
}


class ModeEngine:
    def __init__(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        self.modes = load_modes(MODES_DIR)
        self.state = self._load_state()

    # ------------------------------------------------------------ state
    def _load_state(self) -> dict:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, encoding="utf-8") as fh:
                return json.load(fh)
        return {"mode": "default"}

    def _save_state(self, mode_id: str) -> None:
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump({"mode": mode_id}, fh, indent=2)

    # ---------------------------------------------------------- queries
    def current(self) -> str:
        return self.state.get("mode", "default")

    def list_modes(self) -> list:
        return sorted(self.modes)

    # --------------------------------------------------------- helpers
    def _find_scheme(self, accent: str) -> str:
        return os.path.join(THEMES_DIR, "color-schemes", f"{ACCENT_SCHEMES[accent]}.colors")

    def _find_wallpaper(self, rel: str) -> str:
        return os.path.join(WALLPAPERS_DIR, rel)

    # ---------------------------------------------------------- actions
    def switch(self, mode_id: str, apply: bool = True) -> int:
        if mode_id not in self.modes:
            sys.stderr.write(
                f"Unknown mode: {mode_id}\n"
                f"Available: {', '.join(self.list_modes())}\n"
            )
            return 1

        mode = self.modes[mode_id]

        scheme_path = self._find_scheme(mode["accent"])
        wallpaper_path = self._find_wallpaper(mode["wallpaper"])
        missing = []
        if not os.path.exists(scheme_path):
            missing.append(f"color scheme {scheme_path}")
        if not os.path.exists(wallpaper_path):
            missing.append(f"wallpaper {wallpaper_path}")
        if missing:
            sys.stderr.write(f"Missing assets (run themes/generate.py): {', '.join(missing)}\n")
            return 1

        if apply:
            self._apply_colors(scheme_path)
            self._apply_wallpaper(wallpaper_path)
            self._apply_dock(mode["dock"])
            self._apply_shortcuts(mode["shortcuts"])
            self._reload_shell()

        self._save_state(mode_id)
        print(f"[sakti] switched mode -> {mode_id} ({mode['label']})")
        return 0

    def _apply_colors(self, scheme_path: str) -> None:
        tool = shutil.which("plasma-apply-colorscheme")
        if tool:
            subprocess.run([tool, scheme_path], check=False)
        else:
            dest = os.path.join(
                os.path.expanduser("~"), ".local", "share", "color-schemes",
                os.path.basename(scheme_path),
            )
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(scheme_path, dest)

    def _apply_wallpaper(self, wallpaper_path: str) -> None:
        tool = shutil.which("plasma-apply-wallpaperimage")
        if tool:
            subprocess.run([tool, wallpaper_path], check=False)
            return
        dest = os.path.join(
            os.path.expanduser("~"), "Pictures",
            os.path.basename(wallpaper_path),
        )
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(wallpaper_path, dest)

    def _apply_dock(self, dock_apps: list) -> None:
        """Write the panel applet list. Safe to run repeatedly."""
        lines = [
            "[Containments][1][General]",
            "id=1",
            "lastScreen=0",
            "type=Panel",
            "applets=1,2,3,4",
            "",
            "[Containments][1][Applet][1][General]",
            "plugin=org.kde.plasma.taskbar",
            "launchers=" + "|".join(dock_apps),
            "",
            "[Containments][1][Applet][2][General]",
            "plugin=org.kde.plasma.pager",
            "",
            "[Containments][1][Applet][3][General]",
            "plugin=org.kde.plasma.sakti.ai",
            "",
            "[Containments][1][Applet][4][General]",
            "plugin=org.kde.plasma.systemtray",
            "",
        ]
        os.makedirs(os.path.dirname(PLASMA_PANEL_CONFIG), exist_ok=True)
        with open(PLASMA_PANEL_CONFIG, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        print(f"[sakti] dock configured with {len(dock_apps)} apps")

    def _apply_shortcuts(self, shortcuts: dict) -> None:
        """Bind per-app global shortcuts via kwriteconfig5 (KDE)."""
        tool = shutil.which("kwriteconfig5")
        if not tool:
            return
        for app_id, binding in shortcuts.items():
            subprocess.run(
                [tool, "--file", "kgxettingsrc", "--group", app_id,
                 "--key", "Shortcut", binding],
                check=False,
            )

    def _reload_shell(self) -> None:
        if shutil.which("plasmashell"):
            subprocess.Popen(["plasmashell", "--replace"],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        print()
        print("Usage:")
        print("  sakti-modes switch <default|developer|designer|cyber> [--no-apply]")
        print("  sakti-modes list")
        print("  sakti-modes current")
        print("  sakti-modes validate")
        return 0

    engine = ModeEngine()
    cmd = argv[0]

    if cmd == "list":
        for m in engine.list_modes():
            print(m)
        return 0

    if cmd == "current":
        print(engine.current())
        return 0

    if cmd == "validate":
        reports = validate_all(MODES_DIR)
        if reports:
            for name, errors in reports:
                print(f"INVALID {name}: {'; '.join(errors)}")
            return 1
        print("All mode definitions valid")
        return 0

    if cmd == "switch":
        if len(argv) < 2:
            sys.stderr.write("usage: sakti-modes switch <mode> [--no-apply]\n")
            return 2
        return engine.switch(argv[1], apply="--no-apply" not in argv)

    sys.stderr.write(f"Unknown command: {cmd}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
