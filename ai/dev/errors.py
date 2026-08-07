"""SaktiAI — Developer error diagnosis (human-readable failures).

Turn gnarly npm/pip/composer error output into one line a user can act
on. `diagnose()` inspects a failed ActionResult and returns a friendly
hint, or "" when nothing known matches.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

# Each rule: (regex, hint). First match wins.
NPM_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bE404\b|404 Not Found", re.I),
     "package was not found in the registry — check the name (npm search "
     "<name>, or `npm view <name>`)."),
    (re.compile(r"\bEACCES\b|permission denied", re.I),
     "permission error — you need write access to node_modules (try sudo, "
     "or fix ownership)."),
    (re.compile(r"\bENOT.*\b|ETIMEDOUT|Could not resolve|Network"),
     "network problem — the registry is unreachable. Check your connection "
     "or the registry (npm config get registry)."),
    (re.compile(r"\bERESOLVE\b|conflicting peer dependency", re.I),
     "dependency conflict — run `npm install --legacy-peer-deps` or update "
     "the conflicting package."),
    (re.compile(r"\bEPEERINVALID\b", re.I),
     "peer dependency mismatch — remove the conflict with "
     "`npm install --legacy-peer-deps`."),
]

PIP_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"no matching distribution|could not find a version", re.I),
     "package is not on PyPI under that name — check the spelling and the "
     "installed Python version."),
    (re.compile(r"permission denied|operation not permitted", re.I),
     "permission error — install into a virtualenv (`python -m venv .venv`, "
     "or pip install --user)."),
    (re.compile(r"network is unreachable|certificate verify failed|ssl|proxy")
     ,
     "network/TLS issue — check your connection, proxy, or mirror index."),
    (re.compile(r"could not find a version that satisfies", re.I),
     "no version available — the package or your pinned version does not "
     "exist."),
    (re.compile(r"externally-managed-environment|PEP 668", re.I),
     "PEP 668 externally-managed environment — use a virtualenv "
     "(`python -m venv .venv`) so Python lets you install."),
]

COMPOSER_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"could not find package", re.I),
     "package not found on Packagist — check the name and that you set "
     "`minimum-stability` if it is a dev package."),
    (re.compile(r"network|curl|ssl|could not resolve", re.I),
     "network problem reaching Packagist — check connectivity or your "
     "composer proxy."),
]

_GENERIC_HINTS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"is not recognized as an internal|not an internal or "
                r"external command|command not found", re.I),
     "the tool is not installed or not on PATH — install it or fix your "
     "environment."),
    (re.compile(r"\bENOSPC\b|no space left", re.I),
     "disk full — free up space and retry."),
    (re.compile(r"timed? ?out|timeout after", re.I),
     "command timed out — long-running tool or network hang."),
]


def _tool(kind: str) -> List[Tuple[re.Pattern, str]]:
    if kind == "npm":
        return NPM_HINTS
    if kind == "pip":
        return PIP_HINTS
    if kind == "composer":
        return COMPOSER_HINTS
    return []


def diagnose(command: str, exit_code: int, stdout: str,
             stderr: str) -> Optional[str]:
    """Return a friendly explanation for a failed command, or None."""
    if exit_code == 0:
        return None
    blob = f"{stdout}\n{stderr}".strip()
    if not blob:
        return None
    kind = _infer_kind(command)

    for pattern, hint in _tool(kind) + _GENERIC_HINTS:
        if pattern.search(blob):
            return hint
    return None


def _infer_kind(command: str) -> str:
    if "npm" in command or "yarn" in command or "pnpm" in command:
        return "npm"
    if "pip" in command:
        return "pip"
    if "composer" in command:
        return "composer"
    return ""


def hint_for(kind: str, blob: str) -> Optional[str]:
    """Match a hint against a raw error blob for a given toolkind."""
    for pattern, hint in _tool(kind) + _GENERIC_HINTS:
        if pattern.search(blob):
            return hint
    return None