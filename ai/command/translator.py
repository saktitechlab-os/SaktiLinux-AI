"""SaktiAI — CommandTranslator.

Turns planner steps into concrete shell/PowerShell commands, honouring
the host platform (Windows vs POSIX) and refusing commands that are not
on the allow-list unless the "auto_exit" policy flag is set.

Interface
---------
    commands = translator.translate(plan, snapshot) -> {step.order: cmd}
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..core.types import ContextSnapshot, Plan

# Commands we trust even in strict mode.
_SAFE_COMMANDS: Dict[str, List[str]] = {
    "windows": ["dir", "echo", "where", "ver", "tasklist", "systeminfo"],
    "posix": ["ls", "echo", "uname", "cat", "ss", "ip", "df", "free",
              "top", "find", "grep", "sort", "awk", "wc", "nproc"],
}


def _is_windows() -> bool:
    import platform
    return platform.system() == "Windows"


class CommandTranslator:
    """Maps Step.command templates onto a concrete shell line."""

    def __init__(self, os_name: str | None = None,
                 strict: bool = True) -> None:
        self.os_name = os_name or ("windows" if _is_windows() else "posix")
        self.strict = strict

    # ------------------------------------------------------------ api
    def translate(self, plan: Plan,
                  context: ContextSnapshot) -> Dict[int, str]:
        """Return {step.order: shell command} for each step."""
        out: Dict[int, str] = {}
        for step in plan.steps:
            cmd = self._resolve(step.command, context)
            if self.strict and cmd and not self._allowed(cmd):
                cmd = self._annotation(step.validator, cmd)
            out[step.order] = cmd
        return out

    def _resolve(self, template: str, context: ContextSnapshot) -> str:
        if not template:
            return ""
        # Simple $var / {var} substitution from the snapshot.
        for name in ("cwd", "username", "active_project", "os_name"):
            value = str(getattr(context, name, "") or "")
            template = (template.replace(f"${{{name}}}", value)
                        .replace(f"${name}", value))
        return template

    def _allowed(self, cmd: str) -> bool:
        head = (cmd.split() or [""])[0].lower()
        head = head.replace("\\", "/").split("/")[-1]
        return head in _SAFE_COMMANDS.get(self.os_name, [])

    def _annotation(self, validator: Optional[str], cmd: str) -> str:
        """Annotate the attempt; in strict mode we refuse without policy."""
        if validator == "allow_check" and not self.strict:
            return cmd
        return ""

    def allows(self, command: str) -> bool:
        return self._allowed(command)

    def strict_mode(self, enabled: bool) -> None:
        self.strict = enabled