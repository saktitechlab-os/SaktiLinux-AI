"""SaktiAI — Git adapter.

Detection (is this directory inside a git repository?) and construction
of real git commands: status (staged/unstaged), safe commit flow
(stage-all + commit, or commit with explicit message), and push.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple


def _git_bin() -> str:
    return shutil.which("git") or "git"


def find_repo_root(path: Optional[str] = None) -> Optional[str]:
    """Walk up from `path` (default cwd) to the nearest `.git` dir."""
    start = Path(path or os.getcwd()).resolve()
    if not start.is_dir():
        return None
    for directory in (start, *start.parents):
        if (directory / ".git").exists():
            return str(directory)
    return None


class GitAdapter:
    """Plans real git commands for the dev engine."""

    # -------------------------------------------------- detection
    def repo_root(self, path: Optional[str] = None) -> Optional[str]:
        return find_repo_root(path)

    def is_repo(self, path: Optional[str] = None) -> bool:
        return find_repo_root(path) is not None

    # ------------------------------------------------ command plans
    def plan_status(self, path: Optional[str] = None) -> Tuple[str, str]:
        """(command, root) for `git status --short` in the repo."""
        root = find_repo_root(path)
        if root is None:
            raise NotARepository(path)
        return f"{_git_bin()} status --short", root

    def plan_add_commit(self, message: str,
                        path: Optional[str] = None,
                        add_all: bool = True,
                        ) -> Tuple[str, str]:
        """(command, root) that stages and commits — no push."""
        root = find_repo_root(path)
        if root is None:
            raise NotARepository(path)
        if not message or not message.strip():
            raise CommitError("commit message is required (-m)")
        stage = f"{_git_bin()} add {'-A' if add_all else '.'}"
        commit = f'{_git_bin()} commit -m "{message.strip()}"'
        return f"{stage} && {commit}", root

    def plan_push(self, path: Optional[str] = None,
                  remote: Optional[str] = None,
                  branch: Optional[str] = None) -> Tuple[str, str]:
        root = find_repo_root(path)
        if root is None:
            raise NotARepository(path)
        cmd = _git_bin()
        if remote:
            cmd += f" push {remote}"
            return f"{cmd} {branch}" if branch else cmd, root
        return f"{cmd} push", root

    def plan_log(self, path: Optional[str] = None,
                 limit: int = 10) -> Tuple[str, str]:
        root = find_repo_root(path)
        if root is None:
            raise NotARepository(path)
        return f"{_git_bin()} log --oneline --max-count={max(1, limit)}", root


class NotARepository(Exception):
    """Raised when planning a git command outside a repository."""

    def __init__(self, path: Optional[str] = None) -> None:
        super().__init__(
            f"not a git repository (or any parent): "
            f"{path or os.getcwd()}")


class CommitError(Exception):
    """Raised when a commit cannot be planned (missing message)."""


# Re-export the list helper signature for type checkers.
__all__: List[str] = ["GitAdapter", "find_repo_root", "NotARepository",
                      "CommitError"]