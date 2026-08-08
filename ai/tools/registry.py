"""SaktiAI — Tool Registry.

Knows the developer toolset (git, docker, opencode, node, npm, pip,
composer, editors, package managers), detects which are actually
installed on the host, and maps natural command words onto tools.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Tool:
    """A known developer tool."""

    name: str                 # canonical name, e.g. "git"
    description: str
    bin: List[str] = field(default_factory=list)   # candidate executables
    kind: str = "tool"        # git / docker / editor / opencode / runtime
    pacman: Optional[str] = None    # package name on Arch (None = built-in)
    apt: Optional[str] = None       # package name on Debian/Ubuntu

    def is_missing(self) -> bool:
        return self.pacman is None and self.apt is None


KNOWN_TOOLS: List[Tool] = [
    Tool("git", "version control", ["git"], "vcs", "git", "git"),
    Tool("docker", "container engine", ["docker"], "container",
         "docker", "docker.io"),
    Tool("opencode", "AI coding agent (terminal)", ["opencode", "oc"],
         "agent", "opencode", "opencode"),
    Tool("node", "JavaScript runtime", ["node"], "runtime",
         "nodejs", "nodejs"),
    Tool("npm", "Node package manager", ["npm"], "package",
         "npm", "npm"),
    Tool("python", "Python interpreter", ["python3", "python"], "runtime",
         "python", "python3"),
    Tool("pip", "Python package installer", ["pip3", "pip"], "package",
         "python-pip", "python3-pip"),
    Tool("composer", "PHP dependency manager", ["composer"], "package",
         "composer", "composer"),
    Tool("code", "VS Code / Cursor editor", ["code", "cursor"], "editor",
         "code", "code"),
    Tool("php", "PHP runtime", ["php"], "runtime", "php", "php"),
]


class ToolRegistry:
    """Detects installed tools and maps names/binaries to tools."""

    def __init__(self, tools: Optional[List[Tool]] = None) -> None:
        self._tools: Dict[str, Tool] = {}
        for tool in tools or KNOWN_TOOLS:
            self.register(tool)

    def register(self, tool: Tool) -> None:
        """Register a tool (dynamic addition is supported)."""
        self._tools[tool.name] = tool

    def all(self) -> List[Tool]:
        return list(self._tools.values())

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def find_by_binary(self, binary: str) -> Optional[Tool]:
        for tool in self._tools.values():
            if binary in tool.bin:
                return tool
        return None

    def is_installed(self, name: str) -> bool:
        tool = self._tools.get(name)
        if tool is None:
            return False
        return any(shutil.which(b) is not None for b in tool.bin)

    def installed(self) -> List[Tool]:
        return [t for t in self._tools.values() if self.is_installed(t.name)]

    def installed_names(self) -> List[str]:
        return [t.name for t in self.installed()]

    def detect(self) -> Dict[str, bool]:
        return {t.name: self.is_installed(t.name) for t in self._tools.values()}