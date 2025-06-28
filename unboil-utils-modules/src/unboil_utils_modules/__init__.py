import importlib
from pathlib import Path
from types import ModuleType


def walk_modules(module: ModuleType, prefix: str | None = None):
    for root in module.__path__:
        for path in Path(root).rglob("*.py"):
            parts = []
            while path != Path(root).parent:
                parts.append(path.stem)
                path = path.parent
            module_name = ".".join(parts[::-1])
            if prefix is not None:
                module_name = f"{prefix}{module_name}"
            yield module_name