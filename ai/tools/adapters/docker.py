"""SaktiAI — Docker adapter.

Detects Dockerfiles in a project and plans real `docker build` /
`docker run` commands. The dev engine executes them.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Tuple


def _docker_bin() -> str:
    return shutil.which("docker") or "docker"


def docker_installed() -> bool:
    return shutil.which("docker") is not None


def find_dockerfile(path: Optional[str] = None) -> Optional[str]:
    """Return the Dockerfile path in `path` (default cwd), or None."""
    start = Path(path or ".").resolve()
    if not start.is_dir():
        return None
    if (start / "Dockerfile").is_file():
        return str(start / "Dockerfile")
    return None


class DockerAdapter:
    """Plans real docker build/run commands."""

    def has_dockerfile(self, path: Optional[str] = None) -> bool:
        return find_dockerfile(path) is not None

    def docker_installed(self) -> bool:
        return docker_installed()

    def plan_build(self, path: Optional[str] = None,
                   tag: Optional[str] = None,
                   build_args: Optional[str] = None,
                   ) -> Tuple[str, str]:
        """(command, root) for `docker build -t <tag> .`."""
        root = Path(path or ".").resolve()
        if find_dockerfile(str(root)) is None:
            raise DockerfileMissing(str(root))
        image_tag = tag or f"{root.name.lower()}:latest"
        extra = f" {build_args}" if build_args else ""
        return (f"{_docker_bin()} build -t {image_tag}{extra} .", str(root))

    def plan_run(self, path: Optional[str] = None,
                 image: Optional[str] = None,
                 tag: Optional[str] = None,
                 ports: Optional[str] = None,
                 detach: bool = False,
                 ) -> Tuple[str, str]:
        """(command, root) for `docker run` of the built image."""
        root = Path(path or ".").resolve()
        image_name = image or tag or f"{root.name.lower()}:latest"
        flags = ["--rm"]
        if ports:
            flags.append(f"-p {ports}")
        if detach:
            flags.append("-d")
        return (f"{_docker_bin()} run {' '.join(flags)} {image_name}",
                str(root))


class DockerfileMissing(Exception):
    """Raised when planning a build without a Dockerfile."""

    def __init__(self, path: Optional[str] = None) -> None:
        super().__init__(
            f"no Dockerfile found in {path or '.'} — add one or pass "
            f"another --path")


__all__ = ["DockerAdapter", "find_dockerfile", "docker_installed",
           "DockerfileMissing"]