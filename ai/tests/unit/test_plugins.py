"""Tests for the plugin system (loader + base contract)."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.core import ActionResult, Intent, IntentKind
from ai.plugins import PluginLoader, SaktiPlugin

PLUGIN_SRC = '''\
from ai.plugins import SaktiPlugin
from ai.core import ActionResult, Intent

class Plugin(SaktiPlugin):
    name = "greeter"
    version = "1.0.0"
    description = "says hello"
    intents = ("general",)

    def handle(self, intent, **kwargs):
        return ActionResult.ok("hello from greeter")
'''


class TestPluginBase(unittest.TestCase):
    def test_abstract_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            SaktiPlugin()

    def test_supports(self):
        class P(SaktiPlugin):
            intents = ("install",)
            def handle(self, intent, **kwargs):
                return None
        p = P(brain=None)
        self.assertTrue(p.supports(Intent(kind=IntentKind.INSTALL, raw="x")))
        self.assertFalse(p.supports(Intent(kind=IntentKind.SYSTEM, raw="x")))


class TestPluginLoader(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="sakti_plg_")

    def test_discovers_and_loads(self):
        path = os.path.join(self._tmp, "greeter.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(PLUGIN_SRC)
        loader = PluginLoader(directory=self._tmp)
        plugins = loader.load()
        self.assertIn("greeter", plugins)
        result = plugins["greeter"].handle(
            Intent(kind=IntentKind.GENERAL, raw="hi"))
        self.assertIn("hello", result.stdout)

    def test_empty_dir_no_plugins(self):
        loader = PluginLoader(directory=self._tmp)
        self.assertEqual(loader.load(), {})

    def test_bad_plugin_ignored(self):
        path = os.path.join(self._tmp, "bad.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("raise RuntimeError('boom')\n")
        loader = PluginLoader(directory=self._tmp)
        self.assertEqual(loader.load(), {})


if __name__ == "__main__":
    unittest.main()