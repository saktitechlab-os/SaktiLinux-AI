"""Tests for the command translator (strict-mode allow-list)."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.command import CommandTranslator
from ai.core import ContextSnapshot, Intent, IntentKind, Plan


class TestCommandTranslator(unittest.TestCase):
    def setUp(self):
        self.strict = CommandTranslator(os_name="posix", strict=True)
        self.loose = CommandTranslator(os_name="posix", strict=False)
        self.ctx = ContextSnapshot()
        self.plan = Plan(intent="test", summary="t")
        self.plan.add_step("list", command="ls -la")
        self.plan.add_step("install", command="pacman -S docker",
                           validator=None)

    def test_allowed_command_passthrough(self):
        commands = self.strict.translate(self.plan, self.ctx)
        self.assertEqual(commands[1], "ls -la")

    def test_disallowed_command_blocked(self):
        commands = self.strict.translate(self.plan, self.ctx)
        self.assertEqual(commands[2], "")

    def test_allows(self):
        self.assertTrue(self.strict.allows("ls"))
        self.assertFalse(self.strict.allows("rm -rf /"))

    def test_loose_mode_keeps_command(self):
        commands = self.loose.translate(self.plan, self.ctx)
        self.assertNotEqual(commands[2], "")

    def test_var_substitution(self):
        plan = Plan(intent="run", summary="run")
        plan.add_step("run", command="echo $cwd")
        commands = self.strict.translate(plan, self.ctx)
        self.assertIn(self.ctx.cwd, commands[1])


if __name__ == "__main__":
    unittest.main()