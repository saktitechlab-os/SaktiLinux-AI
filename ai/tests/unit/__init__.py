"""SaktiAI — unit test suite for the AI modules.

Dev runner:  python.exe -m unittest discover -s ai/tests/unit -v
Root runner: python.exe -m unittest discover -s tests/unit
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)