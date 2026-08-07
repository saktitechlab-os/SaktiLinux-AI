"""SaktiAI — Developer Context Detector (Phase 4A).

Probes a workspace and identifies:

- project type        (node / python / php / unknown)
- language
- framework           (react, next, django, flask, laravel, ...)
- package manager     (npm, yarn, pnpm, pip, poetry, uv, composer, ...)

Detection is filesystem-based (manifest sniffing), deterministic, and
runs offline. It supports Node.js, Python, and PHP projects.

    detector = DevContextDetector()
    ctx = detector.detect("/path/to/project")
    ctx.project_type      -> "node"
    ctx.language          -> "python"
    ctx.framework         -> "fastapi"
    ctx.package_manager   -> "uv"
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    import tomllib  # py3.11+
except ImportError:  # pragma: no cover
    tomllib = None

_MANIFESTS = (
    ("node", "package.json"),
    ("python", "pyproject.toml"),
    ("python", "requirements.txt"),
    ("python", "setup.py"),
    ("python", "Pipfile"),
    ("php", "composer.json"),
)

_LOCKFILES = {
    "pnpm": "pnpm-lock.yaml",
    "yarn": "yarn.lock",
    "bun": "bun.lockb",
    "npm": "package-lock.json",
    "poetry": "poetry.lock",
    "uv": "uv.lock",
    "composer": "composer.lock",
}

_FRAMEWORKS = {
    "node": [
        ("nestjs", "nestjs"), ("nextjs", "next"), ("nuxt", "nuxt"),
        ("vite", "vite"), ("react", "react"), ("vue", "vue"),
        ("angular", "angular"), ("svelte", "svelte"), ("express", "express"),
        ("fastify", "fastify"), ("koa", "koa"),
    ],
    "python": [
        ("django", "django"), ("fastapi", "fastapi"), ("flask", "flask"),
        ("bottle", "bottle"), ("streamlit", "streamlit"),
        ("tornado", "tornado"), ("aiohttp", "aiohttp"), ("click", "click"),
    ],
    "php": [
        ("laravel", "laravel/framework"), ("symfony", "symfony/*"),
        ("codeigniter", "codeigniter4/framework"), ("cakephp", "cakephp/*"),
        ("slim", "slim/slim"), ("yii", "yiisoft/*"),
    ],
}

_LANGUAGE = {
    "node": "javascript",
    "python": "python",
    "php": "php",
}


@dataclass
class DevContext:
    """Everything the detector found about a workspace."""

    root: str
    project_type: str = "unknown"
    language: str = "unknown"
    framework: str = "unknown"
    package_manager: str = "unknown"
    manifest: str = ""
    name: str = ""
    dependencies: List[str] = field(default_factory=list)
    scripts: Dict[str, str] = field(default_factory=dict)

    @property
    def detected(self) -> bool:
        return self.project_type != "unknown"

    def to_dict(self) -> Dict[str, object]:
        return {
            "root": self.root,
            "project_type": self.project_type,
            "language": self.language,
            "framework": self.framework,
            "package_manager": self.package_manager,
            "name": self.name,
            "manifest": self.manifest,
            "dependencies": self.dependencies,
            "scripts": self.scripts,
        }


class DevContextDetector:
    """Sniffs a directory to build a DevContext. Pure file probing."""

    def __init__(self, root: Optional[str] = None) -> None:
        self.root = os.path.abspath(root or os.getcwd())

    # ------------------------------------------------------------ api
    def detect(self, path: Optional[str] = None) -> DevContext:
        root = os.path.abspath(path or self.root)
        if not os.path.isdir(root):
            return DevContext(root=root)
        for project_type, manifest in _MANIFESTS:
            full = os.path.join(root, manifest)
            if os.path.isfile(full):
                ctx = self._detect_by_type(project_type, root, full)
                ctx.project_type = project_type
                ctx.language = _LANGUAGE.get(project_type, "unknown")
                return ctx
        return DevContext(root=root)

    # --------------------------------------------------------- detect
    def _detect_by_type(self, project_type: str, root: str,
                        manifest_path: str) -> DevContext:
        if project_type == "node":
            return self._probe_node(root, manifest_path)
        if project_type == "python":
            return self._probe_python(root, manifest_path)
        if project_type == "php":
            return self._probe_php(root, manifest_path)
        return DevContext(root=root)

    def _probe_node(self, root: str, manifest_path: str) -> DevContext:
        ctx = DevContext(root=root, manifest=manifest_path)
        data = _read_json(manifest_path) or {}
        ctx.name = str(data.get("name") or "")
        deps = dict(data.get("dependencies") or {})
        deps.update(data.get("devDependencies") or {})
        ctx.dependencies = sorted(str(k) for k in deps.keys() if k)
        ctx.scripts = {str(k): str(v) for k, v in
                       (data.get("scripts") or {}).items()}
        ctx.framework = _detect_framework("node", ctx.dependencies)
        ctx.package_manager = _detect_manager(root, "node")
        return ctx

    def _probe_python(self, root: str, manifest_path: str) -> DevContext:
        ctx = DevContext(root=root, manifest=manifest_path)
        if os.path.basename(manifest_path) == "pyproject.toml":
            data = _read_toml(manifest_path) or {}
            project = data.get("project") or {}
            ctx.name = str(project.get("name") or "")
            ctx.dependencies = sorted(
                _norm_dep(str(d)) for d in (project.get("dependencies") or []))
            tool = data.get("tool") or {}
            poetry = tool.get("poetry") or {}
            if poetry:
                ctx.name = ctx.name or str(poetry.get("name") or "")
                ctx.dependencies += sorted(
                    _norm_dep(str(k)) for k in
                    (poetry.get("dependencies") or {}).keys()
                    if k not in ("python",))
        else:
            ctx.dependencies = sorted(_requirements(root))
        ctx.framework = _detect_framework("python", ctx.dependencies)
        ctx.package_manager = _detect_manager(root, "python")
        return ctx

    def _probe_php(self, root: str, manifest_path: str) -> DevContext:
        ctx = DevContext(root=root, manifest=manifest_path)
        data = _read_json(manifest_path) or {}
        ctx.name = str(data.get("name") or "")
        require = dict(data.get("require") or {})
        require_dev = dict(data.get("require-dev") or {})
        require.update(require_dev)
        ctx.dependencies = sorted(str(k) for k in require.keys() if k)
        ctx.framework = _detect_framework("php", ctx.dependencies)
        ctx.package_manager = _detect_manager(root, "php")
        return ctx


def _read_json(path: str) -> Optional[Dict]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _read_toml(path: str) -> Optional[Dict]:
    if tomllib is None:
        return None
    try:
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    except (OSError, ValueError, tomllib.TOMLDecodeError):
        return None


def _norm_dep(dep: str) -> str:
    return re.split(r"[<>=!~;[]", dep, maxsplit=1)[0].strip()


def _requirements(root: str) -> List[str]:
    for name in ("requirements.txt", "requirements-dev.txt", "Pipfile"):
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return [_norm_dep(line) for line in fh
                        if line.strip() and not line.lstrip().startswith(("#", "-"))]
        except OSError:
            return []
    return []


def _detect_framework(project_type: str, deps: List[str]) -> str:
    for name, pattern in _FRAMEWORKS.get(project_type, []):
        if _has_dep(deps, pattern):
            return name
    return "unknown"


def _has_dep(deps: List[str], pattern: str) -> bool:
    if pattern.endswith("/*"):
        prefix = pattern[:-2]
        return any(d.startswith(prefix + "/") for d in deps)
    return pattern in deps


def _detect_manager(root: str, project_type: str) -> str:
    ordered = {
        "node": ["pnpm", "yarn", "bun", "npm"],
        "python": ["uv", "poetry", "npm"],
        "php": ["composer"],
    }[project_type]
    for name in ordered:
        lockfile = _LOCKFILES[name]
        if os.path.isfile(os.path.join(root, lockfile)):
            return name
    if project_type == "python":
        if any(os.path.isfile(os.path.join(root, p))
               for p in ("pyproject.toml", "setup.py", "requirements.txt")):
            return "pip"
    if project_type == "node":
        return "npm"
    if project_type == "php":
        return "composer"
    return "unknown"


if __name__ == "__main__":
    detector = DevContextDetector()
    ctx = detector.detect()
    print(json.dumps(ctx.to_dict(), indent=2))