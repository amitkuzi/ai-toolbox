from .base import Backend
from .files import FilesBackend
from .sqlite import SqliteBackend

BACKENDS = {"files": FilesBackend, "sqlite": SqliteBackend}


def get_backend(name: str, base_dir) -> Backend:
    try:
        cls = BACKENDS[name]
    except KeyError:
        raise ValueError(f"unknown backend '{name}' — choose one of {sorted(BACKENDS)}")
    return cls(base_dir)
