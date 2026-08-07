"""SaktiAI — TaskPlanner.

Breaks a user task into ordered, verifiable steps. Rule-driven, with a
stable interface so an LLM-backed planner can slot in later (Strategy
pattern). Each step carries a description, a candidate command, and an
"expected" success condition so the action pipeline can verify it.

Example
-------
"Install Docker"  ->
    step 1: detect OS (uname -o)
    step 2: install docker package (pacman -S --noconfirm docker)
    step 3: enable service (systemctl enable --now docker)
    step 4: verify (docker --version)
"""

from __future__ import annotations

import os
from typing import Callable, List, Optional

from ..core.types import ContextSnapshot, Intent, IntentKind, Plan

# Each rule: (label, desc, [commands], validator)
_PlanRule = Callable[[Intent, ContextSnapshot], Optional[Plan]]


def _first_step_os() -> List[str]:
    return ["uname -o", "cat /etc/os-release"]


def _install_plan(intent: Intent, ctx: ContextSnapshot) -> Optional[Plan]:
    target = intent.parameters.get("target")
    if not target:
        return None
    plan = Plan(intent=intent.kind.value,
                summary=f"Install {target}")
    plan.add_step("Detect the target OS and package manager",
                  command="uname -o && cat /etc/os-release",
                  expected="os-release exists")
    for cmd in _install_candidates(target):
        plan.add_step(f"Install package (candidate: {cmd})", command=cmd,
                      expected="exit code 0")
    plan.add_step("Verify the installation", command=f"{target} --version",
                  validator="allow_check",
                  expected="version string printed")
    return plan


def _create_plan(intent: Intent, ctx: ContextSnapshot) -> Optional[Plan]:
    stack = intent.parameters.get("stack", "react")
    plan = Plan(intent=intent.kind.value,
                summary=f"Scaffold a {stack} project")
    plan.add_step("Create working directory",
                  command=f"mkdir -p ~/Projects/{stack}")
    plan.add_step(f"Scaffold {stack} skeleton",
                  command=f"npx create-{stack}-app@latest ~/Projects/{stack} --use-npm",
                  validator="allow_check",
                  expected="skeleton files created")
    plan.add_step("Install dependencies",
                  command="npm install",
                  expected="node_modules")
    return plan


def _deploy_plan(intent: Intent, ctx: ContextSnapshot) -> Optional[Plan]:
    plan = Plan(intent=intent.kind.value, summary="Deploy website (static)")
    plan.add_step("Build the site",
                  command="npm run build", expected="dist/ produced")
    plan.add_step("Publish build artifacts", command="",
                  expected="published")
    return plan


def _scan_network_plan(intent: Intent, ctx: ContextSnapshot) -> Optional[Plan]:
    plan = Plan(intent=intent.kind.value, summary="Scan the local network")
    plan.add_step("Discover local subnet hosts",
                  command="ip route show | cut -d ' ' -f 1 | head -1",
                  expected="subnet detected")
    plan.add_step("Run nmap scan", command="nmap -sn 192.168.1.0/24",
                  expected="hosts listed")
    return plan


def _organize_plan(intent: Intent, ctx: ContextSnapshot) -> Optional[Plan]:
    plan = Plan(intent=intent.kind.value, summary="Organize Downloads folder")
    plan.add_step("List Downloads contents",
                  command="ls -la ~/Downloads",
                  expected="files listed")
    plan.add_step("Sort files by type",
                  command="find ~/Downloads -maxdepth 1 -type f | awk -F. "
                          "'{print tolower($NF)}' | sort | uniq -c",
                  expected="category counts")
    return plan


def _generic_plan(intent: Intent, ctx: ContextSnapshot) -> Optional[Plan]:
    plan = Plan(intent=intent.kind.value, summary=intent.raw[:60])
    plan.add_step("Interpret the request",
                  command="", expected="interpreted")
    plan.add_step("Execute best-effort action", command="",
                  expected="done")
    return plan


PLANNER_RULES = {
    IntentKind.INSTALL: _install_plan,
    IntentKind.CREATE: _create_plan,
    IntentKind.DEPLOY: _deploy_plan,
    IntentKind.SCAN_NETWORK: _scan_network_plan,
    IntentKind.ORGANIZE: _organize_plan,
}


def _install_candidates(target: str) -> List[str]:
    """Heuristic: guess package-manager commands based on host OS."""
    import platform
    if platform.system() == "Darwin":
        return [f"brew install {target}"]
    if os.path.exists("/etc/arch-release"):
        return [f"pacman -S --noconfirm {target}"]
    if os.path.exists("/etc/debian_version"):
        return [f"apt-get install -y {target}"]
    return [f"pacman -S --noconfirm {target}",
            f"apt-get install -y {target}"]


class TaskPlanner:
    """Plans tasks using the PLANNER_RULES registry (strategy pattern)."""

    def __init__(self, rules: Optional[dict] = None) -> None:
        self._rules = rules or dict(PLANNER_RULES)

    def plan(self, intent: Intent, ctx: ContextSnapshot) -> Plan:
        builder = self._rules.get(intent.kind) or _generic_plan
        return builder(intent, ctx) or _generic_plan(intent, ctx)