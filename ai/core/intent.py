"""SaktiAI — intent classification.

Rule-based natural-language classifier that maps user text onto
`IntentKind` with parameters and a calibrated confidence score. Kept
pluggable so a local LLM (Phase-3 llm/ and provider manager) can later
rank candidates.

Anatomy of a rule
-----------------
    (NAME, REGEX, KIND, CONFIDENCE, extractor)

Rules are matched in priority order: the most specific phrases come first,
so generic fallbacks (`install`, `run`) never steal a request that was
really about a dependency, a project, a git commit, or an error. Each rule
also carries an extractor that pulls structured parameters out of the
match (target, dependency, manager, project, error snippet, message).
"""

from __future__ import annotations

import re
from typing import Callable, Dict, List, Optional

from .types import Intent, IntentKind

_STRONG = 0.9    # unmistakable phrase (dev-specific intents)
_BASE = 0.7      # confident keyword hit

# Package managers → signals install_dependency.
_PKG_MANAGERS = (r"(?:npm|yarn|pnpm|pip|pip3|pipenv|poetry|cargo|gem|go|"
                 r"brew|apt|composer|maven|gradle)")
_WORKSPACE = (r"(?:project|repo|repository|codebase|app|application|"
              r"workspace|module|server|website|site)")


def _extract_target(match, text: str) -> Dict[str, object]:
    m = re.search(r"(?:install|uninstall|run|launch|open)\s+"
                  r"(?:the\s+|this\s+|my\s+)?([\w./\-]+)", text, re.I)
    return {"target": m.group(1).rstrip(".,!?") if m else ""}


def _extract_dep(match, text: str) -> Dict[str, object]:
    params: Dict[str, object] = {}
    mgr = re.search(rf"({_PKG_MANAGERS})", text.lower())
    if mgr:
        params["manager"] = mgr.group(1)
    # 1) "<install/add> X using|via|with|through <manager>"
    via = re.search(r"(?:install|add)\s+([\w@./\-]+)\s+(?:using|via|with|through)",
                    text.lower())
    if via and via.group(1) not in ("the", "a", "an"):
        params["dependency"] = via.group(1)
        return params
    # 2) "X dependency / package / module / library"
    word = re.search(r"(\S+)\s+(?:dependency|package|module|library)", text.lower())
    if word and word.group(1) not in ("add", "install"):
        params["dependency"] = word.group(1).rstrip(".,!?")
        return params
    # 3) "<manager> install|add <name>"  (pip install requests)
    if mgr:
        pkg = re.search(r"(?:install|add)\s+([\w@./\-]+)", text.lower())
        if pkg:
            params["dependency"] = pkg.group(1).rstrip(".,!?")
    # 4) bare "add <name>"
    elif (bare := re.search(r"\b add\s+([\w@./\-]+)", text.lower())):
        params["dependency"] = bare.group(1).rstrip(".,!?")
    return params


def _extract_commit(match, text: str) -> Dict[str, object]:
    m = re.search(r"(?:commit(?:['\"]?:|ed|ing)?|push)\s*(?:with message[: ]*|\s+—?\s*)?"
                  r"(['\"]?)(.*?)\1?$", text, re.IGNORECASE)
    msg = (m.group(2).strip() if m and m.group(2).strip()
           else _default_commit_message(text))
    return {"message": msg}


def _default_commit_message(text: str) -> str:
    m = re.search(r"(?:commit|push)\s+(.*)$", text, re.IGNORECASE)
    return m.group(1).strip().rstrip(".,!?") if m else "changes"


def _extract_fix(match, text: str) -> Dict[str, object]:
    m = re.search(r"(?:fix|debug|error|failing|troubleshoot)\s*[: -]*\s*"
                  r"([a-z0-9_./\- ]{2,80})", text, re.IGNORECASE)
    return {"issue": m.group(1).strip().rstrip(".,!?") if m else "error"}


def _extract_project(match, text: str) -> Dict[str, object]:
    m = re.search(rf"\b({_WORKSPACE})\b", text)
    return {"project": m.group(1).lower() if m else "current"}


def _extract_query(match, text: str) -> Dict[str, object]:
    m = re.search(r"(?:search(?:\s+for)?|find)\s+(.+)$", text, re.IGNORECASE)
    return {"query": m.group(1).strip().rstrip(".,!?") if m else text}


def _extract_create(match, text: str) -> Dict[str, object]:
    stacks = (r"\b(react|next|nextjs|vue|node|nodejs|flutter|rust|python|"
              r"android|express|typescript|go|portfolio)\b")
    stack = re.search(stacks, text, re.IGNORECASE)
    name = (stack.group(1).lower() if stack else "default")
    if name == "nextjs":
        name = "next"
    return {"stack": name}


def _extract_run(match, text: str) -> Dict[str, object]:
    m = re.search(r"(?:run|launch|open)\s+([^\s,.;]+)", text)
    return {"target": m.group(1).rstrip(".,!?") if m else ""}


def _extract_target_generic(match, text: str) -> Dict[str, object]:
    m = re.search(r"install\s+(?:the\s+)?([\w./@\-]+)", text, re.IGNORECASE)
    return {"target": m.group(1).rstrip(".,!?") if m else ""}


# ------------------------------------------------------------- rules ------
# Priority-ordered: most specific developer phrases first, so generic
# `install`/`run` can never swallow a dependency / project / commit / fix.
_RULES: List[tuple[str, "re.Pattern", IntentKind, float, "Callable[..., dict]"]] = [
    # ---- developer intents (highest specificity) ----
    ("git_commit",
     r"\b(?:git\s+commit|commit|(?:git\s+)?push(?:ed)?|save\s+(?:the\s+|my\s+)?"
     r"(?:changes|work|code))\b.*"
     r"(?:changes|work|code|fix|feat|message|now|\bto\b|\bon\b)?",
     IntentKind.GIT_COMMIT, _STRONG, _extract_commit),

    ("fix_error",
     r"\b(?:fix|debug|repair|troubleshoot|resolve)\s(?:the\s+|this\s+|that\s+)?"
     r"(?:error|bug|issue|crash|why|what)"
     r"|\berror\b.{0,40}(?:fix|debug|show|message|why)"
     r"|why\s+(?:is|does|isn't)\s+\w",
     IntentKind.FIX_ERROR, _STRONG, _extract_fix),

    ("install_dependency",
     rf"\b(?:install|add|get)\s+(?:a\s+|the\s+|this\s+)?"
     r"(?:dependency|package|lib(?:rary)?|module)\b"
     rf"|\b(?:install|add)\s+\S+\s+(?:using|via|with|through)\s+({_PKG_MANAGERS})\b"
     rf"|\b({_PKG_MANAGERS})\s+(?:install|add)\b"
     r"|\badd\s+\S+\b",
     IntentKind.INSTALL_DEPENDENCY, _STRONG, _extract_dep),

    ("run_project",
     rf"\b(?:run|start|launch|serve|rebuild)\s+(?:the\s+|this\s+|my\s+)?"
     rf"({_WORKSPACE})"
     rf"|\b(?:run|start|launch|serve)\b.{{0,30}}\b(?:dev|development|local)"
     r"\s*server\b"
     r"|\b(?:npm|yarn|pnpm)\s+run\b",
     IntentKind.RUN_PROJECT, _STRONG, _extract_project),

    # -- generic but still unambiguous ----
    ("build",
     r"\b(?:build|compile)\s+(?:the\s+|a\s+)?"
     r"(?:project|app|application|code|android|release|binary|from\s+source)"
     r"|\b(?:build|compile)\s+(?:the\s+)?\S+",
     IntentKind.BUILD, _BASE, _extract_target_generic),

    ("create_project",
     rf"\bcreate\b[\s\w,:;\"']*?\b({_WORKSPACE}|project|portfolio|starter|app)\b"
     rf"|\b(?:scaffold|new|init)\b[\s\w-]*\b({_WORKSPACE})\b",
     IntentKind.CREATE, _BASE, _extract_create),

    ("install",
     r"\binst[a-z]*all?\b",
     IntentKind.INSTALL, _BASE, _extract_target_generic),

    ("deploy_project",
     r"\b(?:deploy|publish|ship|upload)\s+(?:the\s+|this\s+|my\s+)?"
     r"(?:project|app|website|site|api|server|site)\b"
     r"|\b(?:deploy|publish|ship)\b",
     IntentKind.DEPLOY, _BASE, None),

    ("scan_network",
     r"\b(?:scan|recon|enumerate|map)\b.*\b(?:network|wifi|ports?\b|hosts?\b|subnet)",
     IntentKind.SCAN_NETWORK, _BASE, None),

    ("organize",
     r"\b(?:organi[sz]e|clean(?: up)?|sort)\s+(?:my\s+|the\s+|this\s+)?"
     r"downloads\b",
     IntentKind.ORGANIZE, _BASE, None),

    ("search",
     r"\bsearch(?:\s+for)?\b|\bfind\s+(?:the\s+)?",
     IntentKind.SEARCH, _BASE, _extract_query),

    ("run",
     r"\b(?:run|launch|open)\s+\S+",
     IntentKind.RUN, _BASE, _extract_run),

    ("system",
     r"\b(?:status|system\s*-?info|uptime|(?:\?|show|get)\s*(?:system|info))"
     r"|\b(?:ram|cpu|battery|how\s+fast|disk)\b",
     IntentKind.SYSTEM, _BASE, None),
]

# Compile once.
_RULES = [(name, re.compile(regex, re.IGNORECASE), kind, conf, extractor)
          for name, regex, kind, conf, extractor in _RULES]


class IntentClassifier:
    """Maps free text onto an Intent with parameters and confidence."""

    def __init__(self) -> None:
        self._rules = _RULES

    # -------------------------------------------------------------- api
    def classify(self, text: str) -> Intent:
        lowered = text.strip()
        for _name, pattern, kind, confidence, extractor in self._rules:
            m = pattern.search(lowered)
            if m:
                params = extractor(m, text) if extractor else {}
                return Intent(kind=kind, raw=text, parameters=params,
                              confidence=confidence)
        return Intent(kind=IntentKind.GENERAL, raw=text,
                      parameters={}, confidence=0.3)

    def candidates(self, text: str, top: int = 3) -> List[Intent]:
        """Return the top-N distinct candidate intents (for an LLM ranker)."""
        lowered = text.strip()
        seen: set[IntentKind] = set()
        out: List[Intent] = []
        for _name, pattern, kind, _conf, extractor in self._rules:
            if kind in seen:
                continue
            if pattern.search(lowered):
                intent = self.classify(text)
                if intent.kind not in seen:
                    seen.add(intent.kind)
                    out.append(intent)
            if len(out) >= top:
                break
        return out if out else [self.classify(text)]

    def supported_kinds(self) -> List[str]:
        return [k.value for k in IntentKind]