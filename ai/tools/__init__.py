"""SaktiAI — Tool Ecosystem (Phase 4B).

A registry of developer tools (git, docker, opencode, package managers)
with real detection, dynamic registration, command → tool mapping, and a
package-manager-backed install flow (pacman today, apt ready).

Modules:
    registry    known tools + installed-tool detection
    manager     install flow + command -> tool mapping
    adapters    per-tool command planners (git, docker, opencode)
"""

from .registry import Tool, ToolRegistry
from .manager import ToolManager

__all__ = ["Tool", "ToolRegistry", "ToolManager"]