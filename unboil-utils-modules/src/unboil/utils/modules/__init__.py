import importlib
from fnmatch import fnmatch
from pathlib import Path
from types import ModuleType


def import_modules(
    root: Path | str | ModuleType, 
    patterns: str | list[str] | None = None
):
    for module_name in walk_modules(root, patterns):
        importlib.import_module(module_name)


def walk_modules(
    root: Path | str | ModuleType, 
    patterns: str | list[str] | None = None
):
    if isinstance(root, ModuleType):
        roots = [Path(item) for item in root.__path__]
    else:
        roots = [Path(root)]
    for root in roots:
        for path in root.rglob("*.py"):
            relative_path = path.relative_to(root.parent)
            nodes = [*relative_path.parts[:-1]]
            leaf = relative_path.stem
            if leaf != "__init__":
                nodes.append(leaf)
            module_name = ".".join(nodes)
            if patterns is None:
                yield module_name
            else:
                if isinstance(patterns, str):
                    patterns = [patterns]
                is_match = any(
                    fnmatch(module_name, pattern) 
                    for pattern in patterns
                )
                if is_match:
                    yield module_name