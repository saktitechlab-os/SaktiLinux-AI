"""SaktiAI — Tool Manager.

Orchestrates the ToolRegistry with the host package manager (pacman on
, apt on Debian/Ubuntu) to install tools for real, and maps natural
command words onto registered tools.
"""

from __future__ import annotations

import shutil
from typing import Callable, Optional

from ..actions.runner import CommandRunner
from ..core.types import ActionResult
from .registry import Tool, ToolRegistry

TOOL_WORDS = {
    "git": "git", "commit": "git", "push": "git", "pull": "git",
    "docker": "docker", "container": "docker",
    "opencode": "opencode", "open-code": "opencode",
    "npm": "npm", "node": "node", "python": "python", "pip": "pip",
    "composer": "composer", "code": "code", "vscode": "code",
}


def detect_package_manager() -> Optional[str]:
    """Return "pacman" / "apt" when the host package manager exists."""
    if shutil.which("pacman"):
        return "pacman"
    if shutil.which("apt-get"):
        return "apt"
    return None


class ToolManager:
    """Detects, maps, and installs tools (real package-manager commands)."""

    def __init__(self, registry: Optional[ToolRegistry] = None,
                 runner: Optional[CommandRunner] = None) -> None:
        self.registry = registry or ToolRegistry()
        self.runner = runner or CommandRunner()

    # ------------------------------------------------------ mapping
    def map_tool(self, command: str) -> Optional[Tool]:
        """Map the first word(s) of a command onto a tool, if known."""
        if not command:
            return None
        first = command.strip().split()[0].lower()
        name = TOOL_WORDS.get(first)
        if name is None:
            return None
        return self.registry.get(name)

    def install_command(self, tool: Tool) -> Optional[str]:
        """The real package-manager install command, or None."""
        pm = detect_package_manager()
        if pm == "pacman" and tool.pacman:
            return f"sudo pacman -S --needed --noconfirm {tool.pacman}"
        if pm == "apt" and tool.apt:
            return f"sudo apt-get install -y {tool.apt}"
        return None

    # ------------------------------------------------------ install
    def install_tool(self, tool: str, dry_run: bool = False,
                     live: bool = False,
                     confirm: Optional[Callable[[str, str], bool]] = None
                     ) -> ActionResult:
        """Install a registered tool for real (or plan it with --dry)."""
        tool_obj = self.registry.get(tool)
        if tool_obj is None:
            return ActionResult.fail(
                f"unknown tool '{tool}' — see `sakti-ai tools list`",
                exit_code=-1)
        if self.registry.is_installed(tool):
            return ActionResult.ok(
                f"tool '{tool}' is already installed")
        command = self.install_command(tool_obj)
        if command is None:
            pm = detect_package_manager()
            if pm is None:
                return ActionResult.fail(
                    "no package manager detected on this system "
                    "(expected pacman or apt-get)", exit_code=-1)
            return ActionResult.fail(
                f"no install recipe for tool '{tool}' via '{pm}'",
                exit_code=-1)
        if (confirm and not dry_run
                and not confirm(tool_obj.name, command)):
            return ActionResult.fail(
                f"aborted by user: not installing {tool}", exit_code=-4)
        if dry_run:
            return self.runner.run(command, dry_run=True)
        return (self.runner.run_live(command)
                if live else self.runner.run(command))