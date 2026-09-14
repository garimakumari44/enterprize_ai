"""
Dynamic loader for workflow nodes.

The NodeLoader discovers and imports Python modules containing workflow
nodes. Imported modules register themselves with the global registry
using the @register_node decorator.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil
from pathlib import Path

logger = logging.getLogger(__name__)


class NodeLoader:
    """
    Discovers and imports workflow node modules.
    """

    def __init__(self) -> None:
        self._loaded_modules: set[str] = set()

    # ------------------------------------------------------------------
    # Package Loading
    # ------------------------------------------------------------------

    def load_package(self, package_name: str) -> None:
        """
        Load every module inside a package.

        Example:
            loader.load_package("app.nodes.ai")
        """
        package = importlib.import_module(package_name)

        if not hasattr(package, "__path__"):
            raise ValueError(f"{package_name} is not a package.")

        for _, module_name, is_package in pkgutil.walk_packages(
            package.__path__,
            prefix=f"{package_name}.",
        ):
            if is_package:
                continue

            self.load_module(module_name)

    # ------------------------------------------------------------------
    # Module Loading
    # ------------------------------------------------------------------

    def load_module(self, module_name: str) -> None:
        """
        Import a module if it has not already been imported.
        """
        if module_name in self._loaded_modules:
            return

        importlib.import_module(module_name)

        self._loaded_modules.add(module_name)

        logger.info("Loaded node module: %s", module_name)

    # ------------------------------------------------------------------
    # Directory Loading
    # ------------------------------------------------------------------

    def load_directory(
        self,
        directory: str | Path,
        package_prefix: str,
    ) -> None:
        """
        Load every .py file from a directory.

        Example:
            loader.load_directory(
                "app/nodes/ai",
                "app.nodes.ai",
            )
        """
        directory = Path(directory)

        for file in directory.rglob("*.py"):
            if file.name.startswith("_"):
                continue

            module = (
                package_prefix
                + "."
                + ".".join(file.relative_to(directory).with_suffix("").parts)
            )

            self.load_module(module)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @property
    def loaded_modules(self) -> tuple[str, ...]:
        """Return all loaded module names."""
        return tuple(sorted(self._loaded_modules))

    def is_loaded(self, module_name: str) -> bool:
        """Return True if a module has already been loaded."""
        return module_name in self._loaded_modules

    def clear(self) -> None:
        """Clear the loaded module cache."""
        self._loaded_modules.clear()


# ----------------------------------------------------------------------
# Global Loader
# ----------------------------------------------------------------------

node_loader = NodeLoader()