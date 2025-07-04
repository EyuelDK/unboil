from pathlib import Path
from types import ModuleType


def walk_modules(root: Path | str | ModuleType):
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
            yield module_name