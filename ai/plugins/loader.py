"""SaktiAI — PluginLoader.

Discovers and loads Sakti plugins from a scan directory
(`~/.local/share/sakti/plugins/`). Each plugin file is a Python module
with a `Plugin` attribute exposing a class derived from `SaktiPlugin`.
"""

from __future__ import annotations

import importlib.util
import logging
import os
from typing import Dict, List, Optional, Type

from .base import SaktiPlugin

LOG = logging.getLogger(__name__)

DEFAULT_DIR = os.path.join(os.path.expanduser("~"),
                           ".local", "share", "sakti", "plugins")


class PluginLoader:
    """Loads plugins from a directory."""

    def __init__(self, directory: str = DEFAULT_DIR) -> None:
        self.directory = directory

    def discover(self) -> List[str]:
        """Return list of plugin module paths found."""
        os.makedirs(self.directory, exist_ok=True)
        return sorted(
            os.path.join(self.directory, name)
            for name in os.listdir(self.directory)
            if name.endswith(".py") and not name.startswith("__")
        )

    def load(self, brain=None) -> Dict[str, SaktiPlugin]:
        plugins: Dict[str, SaktiPlugin] = {}
        for path in self.discover():
            try:
                module = self._import_module(path)
                candidate = getattr(module, "Plugin", None)
                if candidate is None:
                    candidate = self._first_sakti_plugin(module)
                if candidate is None:
                    LOG.warning("plugin has no Plugin attr: %s", path)
                    continue
                instance = candidate(brain=brain)
                if isinstance(instance, SaktiPlugin):
                    plugins[instance.name] = instance
                else:
                    LOG.warning("plugin object is not a SaktiPlugin: %s", path)
            except Exception as exc:
                LOG.error("failed to load plugin %s: %s", path, exc)
        return plugins

    # ------------------------------------------------------ internal
    @staticmethod
    def _import_module(path: str):
        name = f"sakti_plugin_{os.path.splitext(os.path.basename(path))[0]}"
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def _first_sakti_plugin(module) -> Optional[Type[SaktiPlugin]]:
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, SaktiPlugin) \
                    and attr is not SaktiPlugin:
                return attr
        return None