"""SaktiAI — `python -m ai.core` entry point.

Runs a quick brain query against the full wired pipeline and prints the
report message:

    python3 -m ai.core "install docker"
    python3 -m ai.core --dry-run "hello"
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ai.core import SaktiBrain


def _wired_brain() -> SaktiBrain:
    from ai.actions import ActionPipeline
    from ai.command import CommandTranslator
    from ai.context import ContextEngine
    from ai.memory import MemoryStore
    from ai.planner import TaskPlanner

    return SaktiBrain(
        context_engine=ContextEngine(),
        planner=TaskPlanner(),
        command_engine=CommandTranslator(),
        action_pipeline=ActionPipeline(continue_on_error=True),
        memory_store=MemoryStore(),
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai.core",
                                     description="SaktiAI quick brain query")
    parser.add_argument("text", nargs="*", default=["hello"])
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    text = " ".join(args.text)
    brain = _wired_brain()
    report = brain.process(text, dry_run=args.dry_run)

    print(report.message)
    if args.verbose:
        print(json.dumps(report.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())