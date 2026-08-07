"""SaktiAI — Developer Core subpackage (Phase 4A).

Projects, languages, frameworks, package managers are detected from the
filesystem; developer commands (run / install / build) execute for real,
with live streaming, dry-run, install confirmation, human-readable error
hints, and a command history you can replay.
"""

from .detector import DevContext, DevContextDetector
from .engine import DevCommandEngine
from .history import DevHistory

__all__ = ["DevContext", "DevContextDetector", "DevCommandEngine", "DevHistory"]