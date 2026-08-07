"""SaktiAI — Developer Core subpackage (Phase 4A).

Projects, languages, frameworks, package managers are detected from the
filesystem; developer commands (run / install / build) execute for real.
"""

from .detector import DevContext, DevContextDetector
from .engine import DevCommandEngine

__all__ = ["DevContext", "DevContextDetector", "DevCommandEngine"]