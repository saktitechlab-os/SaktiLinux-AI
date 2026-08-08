"""Integration tests for Phase 6 SaktiOS Custom UI Shell.

A REAL UIServer on an ephemeral port, wired to the REAL offline brain
(rule-based) and the REAL automation engine with an isolated dev
history — everything over raw HTTP. Wallpaper/logo endpoints prove
asset fallbacks (SVG gradient / repo SVG) on a machine with no
~/wallpapers set up.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest

import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.automation import AutomationEngine
from ai.core import SaktiBrain
from ai.dev import DevHistory
from ui.server import serve


def _get(url: str) -> tuple[int, bytes, str]:
    with urllib.request.urlopen(url, timeout=15) as res:
        return res.status, res.read(), res.headers.get("Content-Type", "")


def _post(url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.status, json.loads(res.read().decode("utf-8"))


def _brain() -> SaktiBrain:
    from ai.actions import ActionPipeline
    from ai.command import CommandTranslator
    from ai.context import ContextEngine
    from ai.memory import MemoryStore
    from ai.planner import TaskPlanner
    from ai.providers import ProviderManager
    return SaktiBrain(context_engine=ContextEngine(),
                      planner=TaskPlanner(),
                      command_engine=CommandTranslator(),
                      action_pipeline=ActionPipeline(continue_on_error=True),
                      memory_store=MemoryStore(),
                      provider_manager=ProviderManager())


class RealUIEndToEnd(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_ui_int_")
        self.hist = DevHistory(os.path.join(self.dir, "hist.json"))
        self.server = serve(
            host="127.0.0.1", port=0, quiet=True,
            brain=_brain(),
            automation_factory=lambda: AutomationEngine(
                history=self.hist, confirm=None),
            history_factory=lambda: self.hist,
        )
        self._thread = threading.Thread(target=self.server.serve_forever,
                                        daemon=True)
        self._thread.start()
        self.base = self.server.server_url()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_index_is_the_custom_shell(self):
        status, body, ctype = _get(self.base + "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", ctype)
        for marker in ("SaktiOS", "Initializing AI Core", "chat-log",
                       "log-view", "dock-input"):
            self.assertIn(marker, body.decode("utf-8", errors="replace"))

    def test_real_chat_via_http(self):
        status, data = _post(self.base + "/api/chat",
                             {"message": "install docker", "dry": True})
        self.assertEqual(status, 200)
        self.assertTrue(data["reply"],
                        "expected a non-empty reply from the brain")
        self.assertIsInstance(data["intent"], str)

    def test_automation_dry_run_via_http(self):
        status, data = _post(self.base + "/api/do",
                             {"task": "run the project", "dry": True})
        self.assertEqual(status, 200)
        self.assertTrue(data["success"])
        self.assertTrue(data["steps"])

    def test_live_logs_endpoint(self):
        self.hist.add(command="sakti-ai dev run", action="run",
                      cwd=self.dir, status="success", exit_code=0)
        import urllib.request as urlreq
        with urlreq.urlopen(self.base + "/api/logs?limit=3",
                            timeout=15) as res:
            logs = json.loads(res.read().decode("utf-8"))
        self.assertEqual(res.status, 200)
        self.assertGreaterEqual(len(logs["entries"]), 1)
        self.assertEqual(logs["entries"][0]["action"], "run")

    def test_wallpaper_fallback_svg(self):
        status, body, ctype = _get(self.base + "/wallpaper")
        self.assertEqual(status, 200)
        self.assertIn("svg", ctype)
        self.assertIn(b"<svg", body)

    def test_logo_served_from_repo(self):
        status, body, ctype = _get(self.base + "/branding/logo")
        self.assertEqual(status, 200)
        self.assertTrue(ctype.startswith("image/"))
        self.assertTrue(len(body) > 100)


class UiCliTests(unittest.TestCase):
    """`sakti-ai ui status|install` end-to-end via the real CLI."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="sakti_ui_cli_")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _cli(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, "-m", "ai.cli", "ui", *args],
            capture_output=True, text=True, cwd=self.dir, env=env)

    def test_status_shows_shell_state(self):
        proc = self._cli("status")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("wm:", proc.stdout)
        self.assertIn("wallpaper", proc.stdout)

    def test_install_writes_wm_autostart_configs(self):
        out = os.path.join(self.dir, "cfg")
        proc = self._cli("install", "--config-dir", out, "--wm", "hyprland")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        conf = os.path.join(out, "hyprland", "hyprland.conf")
        self.assertTrue(os.path.isfile(conf))
        with open(conf, encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn("exec-once = sakti-ai ui serve", content)

    def test_ui_serve_cli_boots_and_answers_http(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = ROOT + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.Popen(
            [sys.executable, "-m", "ai.cli", "ui", "serve", "--port",
             "8766"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            cwd=os.path.dirname(__file__) or ".", env=env)
        try:
            url = "http://127.0.0.1:8766/api/status"
            data = None
            for _ in range(60):
                try:
                    with urllib.request.urlopen(url, timeout=10) as res:
                        data = json.loads(res.read().decode("utf-8"))
                    break
                except Exception:
                    import time
                    time.sleep(0.5)
            if data is None:
                proc.terminate()
                proc.wait(timeout=5)
                out, err = proc.communicate(timeout=5)
                self.fail("ui serve did not come up in time:\n"
                          + (out or "") + "\n" + (err or ""))
            self.assertEqual(data["ui"], "sakti-ui")
        finally:
            proc.terminate()
            proc.wait(timeout=10)
            try:
                proc.stdout.close()
                proc.stderr.close()
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()