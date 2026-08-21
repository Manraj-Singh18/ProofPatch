from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from .models import Claim
from .pipeline import VerificationReport, verify_repository
from .repository_context import RepositoryContext, build_repository_context


@dataclass(frozen=True)
class FileEdit:
    """A bounded file replacement proposed by the coding backend."""

    path: str
    content: str


class EditBackend(Protocol):
    def propose_edits(
        self, task: str, repo: Path, context: RepositoryContext
    ) -> Sequence[FileEdit]:
        """Return file edits for the current task."""

    def claims(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]:
        """Return claims about the resulting repository state."""


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


def _apply_edits(repo: Path, edits: Sequence[FileEdit]) -> None:
    root = repo.resolve()
    for edit in edits:
        target = (root / edit.path).resolve()
        if root != target and root not in target.parents:
            raise EditLoopError(f"edit escapes repository: {edit.path}")
        if target == root:
            raise EditLoopError("cannot replace repository root")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(edit.content)


def run_edit_loop(
    backend: EditBackend,
    task: str,
    repo: str | Path = ".",
    test_command: Sequence[str] = ("pytest", "-q"),
) -> EditRun:
    """Apply one bounded edit proposal, then independently verify its claims."""
    root = Path(repo).resolve()
    context = build_repository_context(root)
    edits = tuple(backend.propose_edits(task, root, context))
    _apply_edits(root, edits)
    post_context = build_repository_context(root)
    claims = tuple(backend.claims(task, root, post_context))
    verification = verify_repository(root, claims, test_command=test_command)
    return EditRun(task=task, edits=edits, verification=verification)
