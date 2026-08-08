"""SaktiAI — OpenCode adapter.

Turns a natural-language prompt into a real `opencode run` invocation,
capturing the generated code so the dev engine can save it into the
project files (`opencode generate`).
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple


def _opencode_bin() -> str:
    return shutil.which("opencode") or "opencode"


def opencode_installed() -> bool:
    return shutil.which("opencode") is not None


def opencode_detect() -> Optional[str]:
    return shutil.which("opencode")


class OpenCodeAdapter:
    """Plans real `opencode` invocations."""

    def installed(self) -> bool:
        return opencode_installed()

    def binary(self) -> str:
        return opencode_detect() or "opencode"

    def plan_run(self, prompt: str, path: Optional[str] = None,
                 ) -> Tuple[str, str]:
        """(command, root) for `opencode run "<prompt>"`."""
        root = Path(path or ".").resolve()
        if not root.is_dir():
            raise OpenCodePathMissing(str(root))
        return (f'{opencode_detect()} run "{prompt.strip()}"', str(root))

    def plan_generate(self, prompt: str, path: Optional[str] = None,
                      output_file: Optional[str] = None,
                      ) -> Tuple[str, str]:
        """(command, root) that generates code and writes it to a file.

        Uses `opencode run` with an explicit "write this file" prompt
        and redirects stdout to the target project file.
        """
        root = Path(path or ".").resolve()
        if not root.is_dir():
            raise OpenCodePathMissing(str(root))
        target = (root / output_file) if output_file else None
        if target is not None:
            target.parent.mkdir(parents=True, exist_ok=True)
            task = (f'Generate the complete content of the file '
                    f'"{output_file}" for the following task. '
                    f'Output raw file content only, no markdown fences.')
            cmd = (f'{opencode_detect()} run '
                   f'"{task} {prompt.strip()}" > "{target}"')
            return cmd, str(root)
        return self.plan_run(prompt, str(root))


class OpenCodePathMissing(Exception):
    """Raised when the target project directory does not exist."""


__all__ = ["OpenCodeAdapter", "opencode_installed", "opencode_detect",
           "OpenCodePathMissing"]