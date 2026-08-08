"""Unit tests for Phase 6 SaktiOS Custom UI Shell.

Covers the theme bridge, the stdlib UI server API (with recording
fakes — no real subprocesses), and the shell config generator
(Hyprland/Openbox/autologin/purge) writing into temp dirs.
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace

import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.server import UIServer, serve
from ui.shell import ShellSetup
from ui.theme import COLORS_FILE, css_variables, load_palette, theme_payload


def _get(url: str) -> tuple[int, dict]:
    with urllib.request.urlopen(url, timeout=10) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


def _get_text(url: str) -> tuple[int, str, str]:
    with urllib.request.urlopen(url, timeout=10) as res:
        return res.status, res.headers.get("Content-Type", ""), \
            res.read().decode("utf-8", errors="replace")


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


class _FakeBrain:
    """Minimal offline brain stand-in for API tests."""

    def status(self):
        return {"engine": "fake", "ready": True}

    def process(self, message, dry_run=False):
        return SimpleNamespace(
            message=f"reply: {message}",
            intent=SimpleNamespace(kind=SimpleNamespace(value="run")))


class _FakeReport:
    def __init__(self, success=True):
        self.success = success
        self.steps = [{"order": 1, "description": "fake step"}]
        self.plan_error = None

    def to_dict(self):
        return {"success": self.success,
                "steps": self.steps, "plan_error": self.plan_error}


class BaseServerCase(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.mkdtemp(prefix="sakti_ui_data_")
        self.hist_path = os.path.join(self.data, "hist.json")
        self.server = serve(
            host="127.0.0.1", port=0, quiet=True,
            brain=_FakeBrain(),
            automation_factory=lambda: _FakeAutomation(),
            history_factory=lambda: _FakeHistory(self.hist_path),
        )
        self._thread = threading.Thread(target=self.server.serve_forever,
                                        daemon=True)
        self._thread.start()
        self.base = self.server.server_url()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.data, ignore_errors=True)


class _FakeAutomation:
    def run(self, task, dry_run=False):
        return _FakeReport(success=True)


class _FakeHistory:
    def __init__(self, path):
        self.path = path

    def list(self, limit=30):
        return [{"id": 1, "command": "sakti-ai dev run", "action": "run",
                 "status": "success", "exit_code": 0}]


class TestTheme(unittest.TestCase):
    def test_palette_loads_brand_values(self):
        palette = load_palette(COLORS_FILE)
        self.assertEqual(palette["palette"]["primary"]["hex"], "#22d3ee")
        self.assertEqual(palette["palette"]["background"]["hex"], "#0f172a")

    def test_css_variables_are_what_the_shell_uses(self):
        css = css_variables(load_palette(COLORS_FILE))
        self.assertIn("--sakti-primary: #22d3ee", css)
        self.assertIn("--sakti-bg: #0f172a", css)
        self.assertIn(":root {", css)

    def test_theme_payload_shape(self):
        payload = theme_payload(load_palette(COLORS_FILE))
        self.assertIn("palette", payload)
        self.assertIn("typography", payload)


class TestServerApi(BaseServerCase):
    def test_index_served(self):
        status, ctype, html = _get_text(self.base + "/")
        self.assertEqual(status, 200)
        self.assertIn("SaktiOS", html)

    def test_static_assets(self):
        for name in ("styles.css", "app.js"):
            status, ctype, body = _get_text(self.base + f"/static/{name}")
            self.assertEqual(status, 200, name)
            self.assertTrue(ctype)
            self.assertTrue(body)

    def test_static_path_traversal_blocked(self):
        try:
            _get_text(self.base + "/static/../server.py")
            self.fail("expected 403 forbidden")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 403)

    def test_api_status(self):
        status, data = _get(self.base + "/api/status")
        self.assertEqual(status, 200)
        self.assertEqual(data["ui"], "sakti-ui")
        self.assertEqual(data["ready"], True)
        self.assertIn("version", data)

    def test_api_theme(self):
        status, data = _get(self.base + "/api/theme")
        self.assertEqual(status, 200)
        self.assertEqual(data["palette"]["primary"]["hex"], "#22d3ee")

    def test_api_apps_browser_is_first(self):
        status, data = _get(self.base + "/api/apps")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(data["apps"]), 1)
        self.assertEqual(data["apps"][0]["id"], "browser")
        self.assertEqual(data["apps"][0]["name"], "SaktiOS Web")

    def test_api_logs_shape(self):
        status, data = _get(self.base + "/api/logs?limit=5")
        self.assertEqual(status, 200)
        self.assertIsInstance(data["entries"], list)

    def test_api_unknown_endpoints(self):
        try:
            _get(self.base + "/api/nope")
            self.fail("expected 404")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)
        try:
            _get(self.base + "/nowhere")
            self.fail("expected 404")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 404)

    def test_chat_requires_message(self):
        try:
            _post(self.base + "/api/chat", {})
            self.fail("expected 400")
        except urllib.error.HTTPError as exc:
            self.assertEqual(exc.code, 400)

    def test_chat_replies(self):
        status, data = _post(self.base + "/api/chat",
                             {"message": "hello", "dry": True})
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertIn("reply: hello", data["reply"])

    def test_do_runs_automation(self):
        status, data = _post(self.base + "/api/do",
                             {"task": "run the project", "dry": True})
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])

    def test_branding_logo_endpoint(self):
        status, ctype, body = _get_text(self.base + "/branding/logo")
        self.assertEqual(status, 200)
        self.assertTrue(ctype.startswith("image/"))

    def test_wallpaper_fallback_is_svg(self):
        status, ctype, body = _get_text(self.base + "/wallpaper")
        self.assertEqual(status, 200)
        self.assertIn("svg", ctype)
        self.assertIn("<svg", body)


def _post(url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


class TestShellSetup(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_shell_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_hyprland_config_is_bare_but_functional(self):
        setup = ShellSetup(home=self.dir, wm="hyprland")
        conf = setup.hyprland_config()
        self.assertIn("exec-once = sakti-ai ui serve", conf)
        self.assertIn("monitor = ,preferred,auto,1", conf)
        self.assertNotIn("waybar", conf)   # no bars/panels
        self.assertIn("disable_hyprland_logo", conf)
        self.assertIn(".png", conf)        # wallpaper wired in

    def test_hyprland_uses_swww_wallpaper(self):
        setup = ShellSetup(home=self.dir, wm="hyprland")
        cmd = setup.wallpaper_command() or ""
        self.assertIn("swww img", cmd)
        self.assertIn("w1.png", cmd)

    def test_openbox_autostart_uses_feh(self):
        setup = ShellSetup(home=self.dir, wm="openbox")
        auto = setup.openbox_autostart()
        self.assertIn("feh --bg-fill", auto)
        self.assertIn("sakti-ai ui serve &", auto)

    def test_generate_writes_expected_tree(self):
        setup = ShellSetup(home=self.dir, wm="hyprland", user="demo")
        written = setup.generate(self.dir + "/out")
        self.assertEqual(len(written), 3)
        expected = [
            "hyprland/hyprland.conf",
            "systemd/system/getty@tty1.service.d/override.conf",
            "sddm.conf.d/autologin.conf",
        ]
        for rel in expected:
            self.assertTrue(any(p.endswith(rel) for p in written), rel)

    def test_openbox_generate_writes_autostart(self):
        setup = ShellSetup(home=self.dir, wm="openbox")
        written = setup.generate(self.dir + "/out")
        self.assertTrue(any(p.endswith("openbox/autostart")
                            for p in written))

    def test_getty_autologin(self):
        setup = ShellSetup(user="sakti")
        unit = setup.getty_autologin()
        self.assertIn("--autologin sakti", unit)
        self.assertIn("tty1", unit)

    def test_purge_plan_removes_linux_traces(self):
        setup = ShellSetup(home=self.dir)
        plan = setup.purge_plan(with_packages=True)
        self.assertGreaterEqual(len(plan), 4)
        self.assertTrue(any("w1.png" in step for step in plan))
        self.assertTrue(any("firefox" in step for step in plan))

    def test_status_keys(self):
        setup = ShellSetup(home=self.dir, wm="hyprland")
        info = setup.status()
        self.assertEqual(info["wm"], "hyprland")
        self.assertFalse(info["wallpaper_present"])
        self.assertIn("w1.png", info["wallpaper"])


if __name__ == "__main__":
    unittest.main()