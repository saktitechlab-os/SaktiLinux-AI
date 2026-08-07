"""Tests for ai/core intent classification."""

import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ai.core import IntentClassifier, IntentKind


class TestIntentClassifier(unittest.TestCase):
    def setUp(self):
        self.classifier = IntentClassifier()

    def test_install_detected(self):
        intent = self.classifier.classify("please install docker")
        self.assertEqual(intent.kind, IntentKind.INSTALL)
        self.assertEqual(intent.parameters.get("target"), "docker")

    def test_create_detected(self):
        intent = self.classifier.classify("create a react portfolio")
        self.assertEqual(intent.kind, IntentKind.CREATE)
        self.assertEqual(intent.parameters.get("stack"), "react")

    def test_deploy_detected(self):
        intent = self.classifier.classify("deploy the site")
        self.assertEqual(intent.kind, IntentKind.DEPLOY)

    def test_scan_network_detected(self):
        intent = self.classifier.classify("scan network for devices")
        self.assertEqual(intent.kind, IntentKind.SCAN_NETWORK)

    def test_system_detected(self):
        intent = self.classifier.classify("show system info")
        self.assertEqual(intent.kind, IntentKind.SYSTEM)

    def test_run_detected(self):
        intent = self.classifier.classify("run firefox")
        self.assertEqual(intent.kind, IntentKind.RUN)

    def test_unknown_general(self):
        intent = self.classifier.classify("what time is it")
        self.assertEqual(intent.kind, IntentKind.GENERAL)
        self.assertLess(intent.confidence, 0.5)

    def test_confidence_default_range(self):
        intent = self.classifier.classify("install git")
        self.assertGreaterEqual(intent.confidence, 0.5)

    def test_supported_kinds(self):
        kinds = self.classifier.supported_kinds()
        self.assertIn("install", kinds)
        self.assertIn("general", kinds)
        self.assertIn("install_dependency", kinds)
        self.assertIn("run_project", kinds)
        self.assertIn("fix_error", kinds)
        self.assertIn("git_commit", kinds)

    # ------------------------------------------------------------ dev intents
    def test_install_dependency_npm(self):
        intent = self.classifier.classify("install axios using npm")
        self.assertEqual(intent.kind, IntentKind.INSTALL_DEPENDENCY)
        self.assertEqual(intent.parameters.get("dependency"), "axios")
        self.assertEqual(intent.parameters.get("manager"), "npm")

    def test_install_dependency_explicit(self):
        intent = self.classifier.classify("add react dependency")
        self.assertEqual(intent.kind, IntentKind.INSTALL_DEPENDENCY)
        self.assertIn("dependency", intent.parameters)

    def test_install_dependency_manager_prefix(self):
        intent = self.classifier.classify("pip install requests")
        self.assertEqual(intent.kind, IntentKind.INSTALL_DEPENDENCY)
        self.assertEqual(intent.parameters.get("dependency"), "requests")
        self.assertEqual(intent.parameters.get("manager"), "pip")

    def test_install_app_still_install(self):
        intent = self.classifier.classify("install docker")
        self.assertEqual(intent.kind, IntentKind.INSTALL)
        self.assertEqual(intent.parameters.get("target"), "docker")

    def test_run_project_detected(self):
        intent = self.classifier.classify("run the project")
        self.assertEqual(intent.kind, IntentKind.RUN_PROJECT)
        self.assertEqual(intent.parameters.get("project"), "project")

    def test_run_dev_server(self):
        intent = self.classifier.classify("start the dev server")
        self.assertEqual(intent.kind, IntentKind.RUN_PROJECT)

    def test_run_app_still_run(self):
        intent = self.classifier.classify("run firefox")
        self.assertEqual(intent.kind, IntentKind.RUN)
        self.assertEqual(intent.parameters.get("target"), "firefox")

    def test_fix_error_detected(self):
        intent = self.classifier.classify("fix the error")
        self.assertEqual(intent.kind, IntentKind.FIX_ERROR)
        self.assertIn("issue", intent.parameters)

    def test_fix_error_why(self):
        intent = self.classifier.classify("why is my build failing")
        self.assertEqual(intent.kind, IntentKind.FIX_ERROR)

    def test_git_commit_detected(self):
        intent = self.classifier.classify("git commit my changes")
        self.assertEqual(intent.kind, IntentKind.GIT_COMMIT)

    def test_git_commit_with_message(self):
        intent = self.classifier.classify("commit with message 'fix login bug'")
        self.assertEqual(intent.kind, IntentKind.GIT_COMMIT)
        self.assertIn("message", intent.parameters)

    def test_dev_intents_high_confidence(self):
        for text in ("run the project", "fix the error",
                     "git commit my changes", "install axios using npm",
                     "start the dev server", "add react dependency"):
            self.assertGreater(
                self.classifier.classify(text).confidence, 0.7)

    # ------------------------------------------------------------ accuracy
    def test_candidates_respect_top(self):
        intents = self.classifier.candidates("run the project")
        self.assertLessEqual(len(intents), 3)
        self.assertEqual(intents[0].kind, IntentKind.RUN_PROJECT)

    def test_general_stays_low_confidence(self):
        intent = self.classifier.classify("what time is it")
        self.assertEqual(intent.kind, IntentKind.GENERAL)
        self.assertLess(intent.confidence, 0.5)


if __name__ == "__main__":
    unittest.main()