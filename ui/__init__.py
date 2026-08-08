"""SaktiOS — Custom UI Shell (Phase 6).

The fullscreen "Jarvis-style" interface: splash boot, AI chat center,
live-log side panel, command dock, hidden launcher, and an in-UI custom
browser placeholder — dark futuristic theme, zero heavy animation, no
host OS visuals.

    ui.theme     branding palette -> CSS variables
    ui.server    UIServer: stdlib HTTP server + API + static shell web
    ui.shell     ShellSetup: wallpaper / WM config / autologin / purge
    ui/web/*     the actual interface (static, served by UIServer)

Standalone per process; the shell is launched fullscreen by the WM
config generated via `sakti-ai ui install` and bootstrapped by the
`sakti-ui-shell.sh` launcher.
"""

from __future__ import annotations

import os

from .server import UIServer, serve
from .shell import ShellSetup

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")

__all__ = ["UIServer", "serve", "ShellSetup", "WEB_DIR"]