"""Canonical path identity for prospective source-metadata control planes.

Artifact identity is always a POSIX project-relative path.  Executable argv
uses the absolute path derived from the same identity object.  Existing
symlink components are rejected rather than resolved into another authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


class PathIdentityError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class CanonicalPathIdentity:
    project_relative: str
    absolute: str


def canonical_path_identity(
    value: str | os.PathLike[str],
    *,
    project_root: str | os.PathLike[str],
    cwd: str | os.PathLike[str] | None = None,
    must_exist: bool = False,
) -> CanonicalPathIdentity:
    """Return the sole canonical identity for a path within ``project_root``.

    Relative inputs are interpreted against the explicitly supplied ``cwd``
    (or the process cwd).  Dot and parent components are collapsed.  The
    result must remain inside the physical project root and may not traverse
    a symlink.  Nonexistent future output paths are allowed unless
    ``must_exist`` is true.
    """
    root_input = Path(project_root)
    try:
        root = root_input.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise PathIdentityError("CANONICAL_PROJECT_ROOT_INVALID") from exc
    if not root.is_dir() or root_input.absolute() != root:
        raise PathIdentityError("CANONICAL_PROJECT_ROOT_AMBIGUOUS")

    raw = Path(value)
    base = Path(cwd) if cwd is not None else Path.cwd()
    lexical = Path(os.path.abspath(os.fspath(raw if raw.is_absolute() else base / raw)))
    try:
        relative = lexical.relative_to(root)
    except ValueError as exc:
        raise PathIdentityError("PATH_OUTSIDE_CANONICAL_PROJECT_ROOT") from exc

    current = root
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise PathIdentityError("SYMLINK_PATH_AUTHORITY_AMBIGUITY")

    if must_exist and not lexical.exists():
        raise PathIdentityError("CANONICAL_PATH_MISSING")
    try:
        resolved = lexical.resolve(strict=must_exist)
    except (OSError, RuntimeError) as exc:
        raise PathIdentityError("CANONICAL_PATH_INVALID") from exc
    if resolved != lexical:
        raise PathIdentityError("SYMLINK_PATH_AUTHORITY_AMBIGUITY")
    return CanonicalPathIdentity(relative.as_posix(), lexical.as_posix())
