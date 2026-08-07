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


if __name__ == "__main__":
    unittest.main()