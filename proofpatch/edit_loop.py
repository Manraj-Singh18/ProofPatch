from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence
import subprocess

from .models import Claim
from .pipeline import VerificationReport, verify_repository
from .repository_context import RepositoryContext, build_repository_context


@dataclass(frozen=True)
class FileEdit:
    """A bounded file replacement proposed by the coding backend."""

    path: str
    content: str


class EditBackend(Protocol):
    def propose_edits(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[FileEdit]: ...
    def claims(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]: ...


class EditLoopError(RuntimeError):
    """Raised when an agent edit violates runtime boundaries."""


@dataclass(frozen=True)
class EditRun:
    task: str
    edits: tuple[FileEdit, ...]
    verification: VerificationReport

    @property
    def accepted(self) -> bool:
        return self.verification.verified


def _normalized_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def _is_test_path(path: str) -> bool:
    """Return whether a repository-relative path is a Python test file."""
    normalized = _normalized_path(path)
    name = normalized.rsplit("/", 1)[-1]
    return (
        name.startswith("test_") and name.endswith(".py")
    ) or (
        name.startswith("test") and name.endswith(".py")
    ) or "/tests/" in f"/{normalized}/"


_PROTECTED_DIRECTORIES = frozenset({
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
})


def _is_protected_path(path: str) -> bool:
    """Return whether an agent must never modify this path."""
    normalized = _normalized_path(path)
    parts = normalized.split("/") if normalized else ()
    if any(part in _PROTECTED_DIRECTORIES for part in parts):
        return True
    return _is_test_path(normalized)


def _protected_path_reason(path: str) -> str:
    normalized = _normalized_path(path)
    parts = normalized.split("/") if normalized else ()
    protected_dir = next((part for part in parts if part in _PROTECTED_DIRECTORIES), None)
    if protected_dir:
        return f"agent edits may not modify protected runtime/toolchain path: {path}"
    return f"agent edits may not modify test files: {path}"


def _git_tracked_paths(repo: Path) -> set[str]:
    """Return paths present in the repository's Git baseline.

    The filesystem may contain untracked files left by a previous failed
    verification run. Those files are not part of the baseline and must not
    become protected merely because they happen to exist on disk.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()

    return {
        _normalized_path(path.decode("utf-8"))
        for path in result.stdout.split(b"\0")
        if path
    }


def _apply_edits(
    repo: Path,
    edits: Sequence[FileEdit],
    baseline_paths: set[str] | None = None,
) -> None:
    """
    Apply bounded agent edits.

    Runtime/toolchain directories are always protected. Test files that
    existed in the Git baseline are immutable. A newly-created regression
    test is allowed, even if a stale file with the same name was left by an
    earlier failed demo run.
    """
    root = repo.resolve()
    if baseline_paths is None:
        baseline_paths = _git_tracked_paths(root)
    baseline_paths = {
        _normalized_path(path)
        for path in baseline_paths
    }

    for edit in edits:
        normalized = _normalized_path(edit.path)
        if not normalized:
            raise EditLoopError("edit path cannot be empty")

        target = (root / normalized).resolve()

        if root != target and root not in target.parents:
            raise EditLoopError(f"edit escapes repository: {edit.path}")

        if target == root:
            raise EditLoopError("cannot replace repository root")

        parts = normalized.split("/") if normalized else ()
        if any(part in _PROTECTED_DIRECTORIES for part in parts):
            raise EditLoopError(_protected_path_reason(edit.path))

        # Protect only test files that were present in the baseline.
        # Untracked files left by previous runs are not baseline evidence.
        if normalized in baseline_paths and _is_test_path(normalized):
            raise EditLoopError(_protected_path_reason(edit.path))

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(edit.content, encoding="utf-8")


def run_edit_loop(backend: EditBackend, task: str, repo: str | Path = ".", test_command: Sequence[str] = ("pytest", "-q")) -> EditRun:
    """Apply one bounded edit proposal, then independently verify its claims."""
    root = Path(repo).resolve()
    context = build_repository_context(root)
    edits = tuple(backend.propose_edits(task, root, context))
    _apply_edits(root, edits, baseline_paths=_git_tracked_paths(root))
    post_context = build_repository_context(root)
    claims = tuple(backend.claims(task, root, post_context))
    verification = verify_repository(root, claims, test_command=test_command)
    return EditRun(task=task, edits=edits, verification=verification)
