"""Tests for ai/memory store and event bus (temp file isolation)."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.memory import MemoryBus, MemoryStore


class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="sakti_mem_")
        self.store = MemoryStore(path=os.path.join(self._tmp, "memory.json"))

    def tearDown(self):
        self.store.wipe()

    def test_write_read(self):
        self.store.write("preferences", "accent", "blue")
        self.assertEqual(self.store.read("preferences", "accent"), "blue")

    def test_update_merges_overwrite(self):
        self.store.write("projects", "web", {"stack": "react"})
        self.store.update("projects", "web", {"status": "active"})
        self.assertEqual(self.store.read("projects", "web")["status"], "active")

    def test_delete(self):
        self.store.write("preferences", "theme", "dark")
        self.assertTrue(self.store.delete("preferences", "theme"))
        self.assertIsNone(self.store.read("preferences", "theme"))

    def test_list(self):
        self.store.write("preferences", "a", 1)
        self.store.write("preferences", "b", 2)
        self.assertEqual(set(self.store.list("preferences").keys()),
                         {"a", "b"})

    def test_namespace_validation(self):
        with self.assertRaises(KeyError):
            self.store.update("nope", "k", "v")

    def test_persistence_across_reload(self):
        self.store.write("preferences", "accent", "green")
        reloaded = MemoryStore(path=self.store._path)
        self.assertEqual(reloaded.read("preferences", "accent"), "green")

    def test_history_add_and_recent(self):
        self.store.add_history("hello")
        self.store.add_history("install docker")
        self.assertEqual(self.store.recent_history(limit=10)[-1], "install docker")

    def test_recent_commands(self):
        self.store.add_recent_command("ls -la")
        self.assertEqual(self.store.recent_commands(limit=5), ["ls -la"])

    def test_remember_project(self):
        self.store.remember_project("sakti", {"ok": True})
        meta = self.store.read("projects", "sakti")
        self.assertTrue(meta["ok"])
        self.assertIn("updated_at", meta)


class TestMemoryBus(unittest.TestCase):
    def test_publish_calls_handler(self):
        bus = MemoryBus()
        seen = []
        bus.subscribe("projects", lambda ns, k, v: seen.append((ns, k, v)))
        bus.publish("projects", "sakti", {"ok": True})
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], "projects")

    def test_unsubscribe(self):
        bus = MemoryBus()
        seen = []
        handler = lambda ns, k, v: seen.append(k)
        bus.subscribe("history", handler)
        bus.unsubscribe("history", handler)
        bus.publish("history", "x", None)
        self.assertEqual(seen, [])

    def test_scope_is_per_namespace(self):
        bus = MemoryBus()
        seen = []
        bus.subscribe("history", lambda ns, k, v: seen.append(k))
        bus.publish("recent_commands", "x", None)
        self.assertEqual(seen, [])

    def test_subscribers_count(self):
        bus = MemoryBus()
        bus.subscribe("history", lambda ns, k, v: None)
        bus.subscribe("history", lambda ns, k, v: None)
        self.assertEqual(bus.subscribers("history"), 2)


if __name__ == "__main__":
    unittest.main()