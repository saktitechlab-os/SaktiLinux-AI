"""SaktiAI — integration test suite.

Wires the full brain pipeline with real (non-mocked) collaborator
modules and verifies end-to-end behaviour in dry-run mode. Never touches
the real user memory file (uses temp dirs).
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)