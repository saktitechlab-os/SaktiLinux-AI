"""SaktiOS UI — web server (stdlib only).

Serves the fullscreen shell UI plus the small JSON API the interface
talks to:

    GET  /                    -> index.html (the shell)
    GET  /static/<file>       -> ui/web assets
    GET  /branding/logo       -> logo image (user asset, else repo SVG)
    GET  /favicon.ico         -> same logo
    GET  /wallpaper           -> ~/wallpapers/w1.png (SVG fallback)
    GET  /api/status          -> engine health + fallbacks state
    GET  /api/theme           -> branding palette for live theming
    GET  /api/apps            -> launcher catalog
    GET  /api/logs?limit=N    -> latest dev-history entries (live logs)
    POST /api/chat            -> {"message", "dry"} -> brain reply
    POST /api/do              -> {"task", "dry"} -> automation report

Threaded so chat and the log panel never block each other. Every
fallback is graceful: missing wallpaper -> generated SVG, missing logo
-> repo SVG.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable, Dict, List, Optional, Tuple

from .theme import COLORS_FILE, load_palette, theme_payload

LOG = logging.getLogger("sakti.ui")


class UIServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, address: tuple = ("127.0.0.1", 0),
                 brain: Optional[object] = None,
                 automation_factory: Optional[Callable] = None,
                 history_factory: Optional[Callable] = None,
                 apps: Optional[List[dict]] = None,
                 web_dir: Optional[str] = None,
                 assets_dir: Optional[str] = None,
                 branding_dir: Optional[str] = None) -> None:
        super().__init__(address, _UIHandler)
        self.brain = brain
        self.automation_factory = automation_factory
        self.history_factory = history_factory
        self.apps = list(apps) if apps is not None else _DEFAULT_APPS
        here = os.path.dirname(os.path.abspath(__file__))
        self.web_dir = os.path.abspath(web_dir or os.path.join(here, "web"))
        self.assets_dir = os.path.abspath(
            assets_dir or os.path.join(os.path.expanduser("~"),
                                       "wallpapers"))
        self.branding_dir = os.path.abspath(
            branding_dir or os.path.join(
                os.path.dirname(here), "branding"))

    # ---------------------------------------------------------- api
    def server_url(self) -> str:
        host, port = self.server_address
        return f"http://{host}:{port}"

    def api_status(self) -> Dict[str, object]:
        import ai
        out: Dict[str, object] = {}
        if self.brain is not None and hasattr(self.brain, "status"):
            st = self.brain.status()
            if isinstance(st, dict):
                out = dict(st)
        out.update({
            "ui": "sakti-ui",
            "version": getattr(ai, "__version__", "0.0.0"),
            "ready": bool(self.brain) and bool(out.get("ready", True)),
            "apps": len(self.apps),
            "wallpaper": os.path.isfile(
                os.path.join(self.assets_dir, "w1.png")),
        })
        return out

    def api_logs(self, limit: int = 30) -> List[dict]:
        if self.history_factory is None:
            return []
        try:
            return self.history_factory().list(limit=max(1, min(limit, 100)))
        except Exception as exc:
            LOG.warning("logs unavailable: %s", exc)
            return []

    def api_chat(self, message: str, dry: bool = False) -> Dict[str, object]:
        if self.brain is None:
            return {"ok": False, "reply": "AI core is offline"}
        out = {"ok": False, "reply": "", "intent": ""}
        try:
            report = self.brain.process(message, dry_run=dry)
        except Exception as exc:
            LOG.warning("brain chat failed: %s", exc)
            out["reply"] = f"AI core error: {exc}"
            return out
        intent = getattr(report, "intent", None)
        out["reply"] = (getattr(report, "message", None) or "").strip()
        out["intent"] = intent.kind.value if intent is not None else ""
        out["ok"] = bool(out["reply"]) and not (
            out["reply"].startswith("ERROR") or out["reply"].startswith(
                "no response"))
        return out

    def api_do(self, task: str, dry: bool = False) -> Dict[str, object]:
        if self.automation_factory is None:
            return {"ok": False, "error": "automation engine offline"}
        try:
            report = self.automation_factory().run(task, dry_run=dry)
        except Exception as exc:
            LOG.warning("automation run failed: %s", exc)
            return {"ok": False, "error": str(exc)}
        if hasattr(report, "to_dict"):
            return report.to_dict()
        return {"ok": bool(getattr(report, "success", False)), "task": task}

    def api_theme(self) -> Dict[str, object]:
        try:
            return theme_payload(load_palette(COLORS_FILE))
        except Exception:
            return {}

    def api_apps(self) -> List[dict]:
        return list(self.apps)

    def branding_logo(self) -> Tuple[bytes, str]:
        """User asset first (assets/logo.png), repo SVG as fallback."""
        user = self._first_existing(
            os.path.join(self.branding_dir, "logo.png"),
            os.path.join(self.branding_dir, "logo.jpg"))
        if user:
            with open(user, "rb") as fh:
                return fh.read(), "image/png" if user.endswith(
                    ".png") else "image/jpeg"
        svg = os.path.join(self.branding_dir, "logo.svg")
        if os.path.exists(svg):
            with open(svg, "rb") as fh:
                return fh.read(), "image/svg+xml"
        return b"", "image/svg+xml"

    def wallpaper(self) -> Tuple[bytes, str]:
        w1 = os.path.join(self.assets_dir, "w1.png")
        if os.path.isfile(w1):
            with open(w1, "rb") as fh:
                return fh.read(), "image/png"
        return _FALLBACK_WALLPAPER_SVG, "image/svg+xml"

    @staticmethod
    def _first_existing(*paths: str) -> Optional[str]:
        for p in paths:
            if os.path.isfile(p):
                return p
        return None


_FALLBACK_WALLPAPER_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080">'
    b'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    b'<stop offset="0" stop-color="#0f172a"/><stop offset="0.5" '
    b'stop-color="#0b1240"/><stop offset="1" stop-color="#1e1b4b"/>'
    b'</linearGradient></defs>'
    b'<rect width="1920" height="1080" fill="url(#g)"/>'
    b'<circle cx="960" cy="540" r="420" fill="none" stroke="#22d3ee" '
    b'stroke-opacity="0.18" stroke-width="2" stroke-dasharray="8 20"/>'
    b'<circle cx="960" cy="540" r="260" fill="none" stroke="#c084fc" '
    b'stroke-opacity="0.25" stroke-width="1.5"/>'
    b'</svg>')

_DEFAULT_APPS: List[dict] = [
    {"id": "browser", "name": "SaktiOS Web",
     "desc": "minimal custom browser", "action": "browser"},
    {"id": "files", "name": "Files",
     "desc": "open the file manager", "action": "files",
     "command": "xdg-open ~/"},
    {"id": "terminal", "name": "Terminal",
     "desc": "launch the terminal", "action": "terminal",
     "command": "sakti-ai terminal"},
    {"id": "settings", "name": "Settings",
     "desc": "system settings", "action": "settings",
     "command": "sakti-ai settings"},
]


def serve(host: str = "127.0.0.1", port: int = 0, quiet: bool = False,
          brain: Optional[object] = None,
          automation_factory: Optional[Callable] = None,
          history_factory: Optional[Callable] = None,
          **kwargs) -> UIServer:
    """Build a bound UIServer; caller decides when to serve/shutdown."""
    if not quiet:
        LOG.info("sakti-ui: serving on http://%s:%s (Ctrl-C to stop)",
                 host, port or "?")
    return UIServer((host, port), brain=brain,
                    automation_factory=automation_factory,
                    history_factory=history_factory, **kwargs)


class _UIHandler(BaseHTTPRequestHandler):
    server: UIServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        LOG.debug(fmt, *args)

    def log_error(self, fmt: str, *args) -> None:
        LOG.warning(fmt, *args)

    # -------------------------------------------------------- GET
    def do_GET(self):  # noqa: C901 (routing is intentionally flat)
        path = self.path.split("?", 1)[0]
        try:
            if path in ("/", "/index.html", "/static/index.html"):
                self._static("index.html")
            elif path.startswith("/static/"):
                self._static(path[len("/static/"):])
            elif path in ("/branding/logo", "/favicon.ico"):
                self._raw(*self.server.branding_logo())
            elif path == "/wallpaper":
                self._raw(*self.server.wallpaper())
            elif path == "/api/status":
                self._json(self.server.api_status())
            elif path == "/api/theme":
                self._json(self.server.api_theme())
            elif path == "/api/apps":
                self._json({"apps": self.server.api_apps()})
            elif path == "/api/logs":
                self._json({"entries": self.server.api_logs(
                    limit=self._query_int("limit", 30))})
            elif path.startswith("/api/"):
                self._json({"ok": False, "error": f"unknown endpoint "
                                                   f"{path}"},
                           HTTPStatus.NOT_FOUND)
            else:
                self._json({"ok": False, "error": "not found"},
                           HTTPStatus.NOT_FOUND)
        except BrokenPipeError:
            pass

    # ------------------------------------------------------- POST
    def do_POST(self) -> None:  # noqa: N802 (http.server convention)
        path = self.path.split("?", 1)[0]
        if path not in ("/api/chat", "/api/do"):
            self._json({"ok": False, "error": "not found"},
                       HTTPStatus.NOT_FOUND)
            return
        body = self._read_json()
        if body is None:
            self._json({"ok": False, "error": "invalid JSON body"},
                       HTTPStatus.BAD_REQUEST)
            return
        try:
            if path == "/api/chat":
                message = str(body.get("message") or "").strip()
                if not message:
                    self._json({"ok": False, "error": "message required"},
                               HTTPStatus.BAD_REQUEST)
                    return
                payload = self.server.api_chat(
                    message, dry=bool(body.get("dry", False)))
            else:
                task = str(body.get("task") or "").strip()
                if not task:
                    self._json({"ok": False, "error": "task required"},
                               HTTPStatus.BAD_REQUEST)
                    return
                payload = self.server.api_do(
                    task, dry=bool(body.get("dry", False)))
            self._json(payload)
        except Exception as exc:
            LOG.exception("api %s failed", path)
            self._json({"ok": False, "error": str(exc)},
                       HTTPStatus.INTERNAL_SERVER_ERROR)

    # ----------------------------------------------------- helpers
    def _read_json(self) -> Optional[dict]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
            return data if isinstance(data, dict) else None
        except (ValueError, UnicodeDecodeError):
            return None

    def _query_int(self, name: str, default: int) -> int:
        from urllib.parse import parse_qs, urlparse
        qs = parse_qs(urlparse(self.path).query)
        try:
            return int(qs.get(name, [str(default)])[0])
        except ValueError:
            return default

    def _static(self, name: str) -> None:
        root = os.path.realpath(self.server.web_dir)
        full = os.path.realpath(os.path.join(root, name))
        if not full.startswith(root + os.sep):
            self._json({"ok": False, "error": "forbidden"},
                       HTTPStatus.FORBIDDEN)
            return
        if not os.path.isfile(full):
            self._json({"ok": False, "error": "not found"},
                       HTTPStatus.NOT_FOUND)
            return
        mime = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as fh:
            data = fh.read()
        self._raw(data, mime)

    def _json(self, payload: object,
              status: int = HTTPStatus.OK) -> None:
        self._raw(json.dumps(payload).encode("utf-8"), "application/json",
                  status=status)

    def _raw(self, data: bytes, mime: str,
             status: int = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass