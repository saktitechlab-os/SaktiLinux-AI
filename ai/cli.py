#!/usr/bin/env python3
"""SaktiAI — CLI entry point.

Usage:
    python3 -m ai.cli chat "install docker" [--dry-run]
    python3 -m ai.cli status
    python3 -m ai.cli memory list [namespace]
    python3 -m ai.cli providers list
    python3 -m ai.cli plugins list
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import __version__
from ai.actions import ActionPipeline
from ai.command import CommandTranslator
from ai.context import ContextEngine
from ai.core import SaktiBrain
from ai.memory import MemoryStore
from ai.planner import TaskPlanner
from ai.plugins import PluginLoader
from ai.providers import ProviderManager
from ai.voice import VoiceEngine, WakeWord


def _check_ollama(brain: SaktiBrain) -> None:
    """Show a clear message when Ollama is registered but not running."""
    if brain.provider_manager is None:
        return
    try:
        running = brain.provider_manager.available_providers()
    except Exception as exc:
        print(f"[sakti] warning: could not check AI providers: {exc}",
              file=sys.stderr)
        return
    if not running:
        print("[sakti] note: Ollama is not running — "
              "using offline rule-based mode. Start it with `ollama serve` "
              "to enable local LLM replies.", file=sys.stderr)


def _brain() -> SaktiBrain:
    return SaktiBrain(
        context_engine=ContextEngine(),
        planner=TaskPlanner(),
        command_engine=CommandTranslator(),
        action_pipeline=ActionPipeline(continue_on_error=True),
        memory_store=MemoryStore(),
        provider_manager=ProviderManager(),
    )


def _cmd_chat(args) -> int:
    brain = _brain()
    _check_ollama(brain)
    report = brain.process(args.text, dry_run=args.dry_run)
    print(report.message)
    if args.verbose:
        print(json.dumps(report.to_dict(), indent=2))
    return 0 if not report.message.startswith("ERROR") else 1


def _cmd_status(args) -> int:
    brain = _brain()
    status = brain.status()
    print(f"sakti-ai {status['version']}  engine={status['engine']}  "
          f"ready={status['ready']}")
    print(f"Ollama running: {status['ollama_running']}")
    if not status["ollama_running"]:
        print("  -> start it with `ollama serve` for AI-powered replies")
    print("modules:")
    for name, loaded in status["modules"].items():
        print(f"  {name}: {'on' if loaded else 'off'}")
    return 0


def _cmd_memory(args) -> int:
    store = MemoryStore()
    # Parse flexible syntax: `memory`, `memory list`, `memory <namespace>`,
    # `memory list <namespace>`.
    namespace = args.namespace or "history"
    if namespace == "list":
        namespace = args.namespace2 or "history"

    if namespace not in store._namespaces:
        print(f"[sakti] error: unknown namespace '{namespace}'. "
              f"Valid: {', '.join(sorted(store._namespaces))}", file=sys.stderr)
        return 1

    log_kinds = ("history", "recent_commands")
    if namespace in log_kinds:
        entries = store.list(namespace).get("entries", [])
        print(f"{namespace} ({len(entries)} entries)")
        for entry in entries[-args.limit:]:
            print(f"  - {entry.get('value')}")
    else:
        data = store.list(namespace)
        print(f"{namespace} ({len(data)} entries)")
        for key, value in list(data.items())[: args.limit]:
            if not isinstance(value, (str, int, float)):
                print(f"  {key}: {json.dumps(value)}")
            else:
                print(f"  {key}: {value}")
    return 0


def _cmd_providers(args) -> int:
    mgr = ProviderManager()
    all_providers = list(mgr._providers.keys())
    available = mgr.available_providers()
    print("registered:", ", ".join(all_providers) or "(none)")
    print("available: ", ", ".join(available) or "(none)")
    if all_providers and not available:
        print("  -> Ollama is registered but not running. Start it with "
              "`ollama serve`.", file=sys.stderr)
    return 0


def _cmd_plugins(args) -> int:
    plugins = PluginLoader().load()
    if not plugins:
        print("no plugins found")
        return 0
    for plugin in plugins.values():
        meta = plugin.metadata()
        print(f"{meta['name']} v{meta['version']}  [{meta['intents']}]  {meta['description']}")
    return 0


def _cmd_wake(args) -> int:
    wake = WakeWord()
    if args.text and wake.is_active(args.text):
        print(f"wake word '{wake.detect(args.text)}' detected")
        return 0
    print("no wake word")
    return 1


def _main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="sakti", description="SaktiAI CLI")
    parser.add_argument("--version", action="version",
                        version=f"sakti-ai {__version__}")
    sub = parser.add_subparsers(dest="command")

    p_chat = sub.add_parser("chat", help="run a request through the brain")
    p_chat.add_argument("text")
    p_chat.add_argument("--dry-run", action="store_true")
    p_chat.add_argument("--verbose", "-v", action="store_true")
    p_chat.set_defaults(func=_cmd_chat)

    p_status = sub.add_parser("status", help="show brain status")
    p_status.set_defaults(func=_cmd_status)

    p_mem = sub.add_parser("memory", help="inspect memory")
    p_mem.add_argument("namespace", nargs="?", default="history")
    p_mem.add_argument("namespace2", nargs="?", default=None,
                       help="namespace used after 'memory list'")
    p_mem.add_argument("--limit", type=int, default=10)
    p_mem.set_defaults(func=_cmd_memory)

    p_prov = sub.add_parser("providers", help="list AI providers")
    p_prov.add_argument("action", nargs="?", default="list")
    p_prov.set_defaults(func=_cmd_providers)

    p_plg = sub.add_parser("plugins", help="list plugins")
    p_plg.add_argument("action", nargs="?", default="list")
    p_plg.set_defaults(func=_cmd_plugins)

    p_wake = sub.add_parser("wake", help="test wake word")
    p_wake.add_argument("text")
    p_wake.set_defaults(func=_cmd_wake)

    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(_main())