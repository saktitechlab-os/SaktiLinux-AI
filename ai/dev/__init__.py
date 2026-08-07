"""SaktiAI — Developer Core subpackage (Phase 4A).

Projects, languages, frameworks, package managers are detected from the
filesystem; developer commands (run / install / build) execute for real,
with live streaming, dry-run, install confirmation, and human-readable
error hints.
"""

from .detector import DevContext, DevContextDetector
from .engine import DevCommandEngine

__all__ = ["DevContext", "DevContextDetector", "DevCommandEngine"]