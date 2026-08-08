"""SaktiAI — Tool adapters (Phase 4B).

Each adapter turns a real developer tool (git, docker, opencode) into a
small command-facing API: detection (is the tool/repo/context present?)
plus "planned command" builders that the dev engine executes for real.
"""

from .git import GitAdapter
from .docker import DockerAdapter
from .opencode import OpenCodeAdapter

__all__ = ["GitAdapter", "DockerAdapter", "OpenCodeAdapter"]