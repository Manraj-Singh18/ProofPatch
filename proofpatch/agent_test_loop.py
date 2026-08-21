from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from .edit_loop import FileEdit, _apply_edits
from .models import Claim
from .pipeline import VerificationReport, verify_repository
from .repository_context import RepositoryContext, build_repository_context


class TestLoopBackend(Protocol):
    def propose_edits(self, task: str, repo: Path, context: RepositoryContext, previous: VerificationReport | None) -> Sequence[FileEdit]: ...
    def claims(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]: ...


@dataclass(frozen=True)
class TestLoopRun:
    task: str
    attempts: int
    verification: VerificationReport

    @property
    def accepted(self) -> bool:
        return self.verification.verified


def run_test_loop(
    backend: TestLoopBackend,
    task: str,
    repo: str | Path = ".",
    test_command: Sequence[str] = ("pytest", "-q"),
    max_attempts: int = 3,
) -> TestLoopRun:
    """Iterate on bounded edits until verification succeeds or attempts are exhausted."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    root = Path(repo).resolve()
    previous = None
    for attempt in range(1, max_attempts + 1):
        context = build_repository_context(root)
        edits = tuple(backend.propose_edits(task, root, context, previous))
        _apply_edits(root, edits)
        post_context = build_repository_context(root)
        claims = tuple(backend.claims(task, root, post_context))
        previous = verify_repository(root, claims, test_command=test_command)
        if previous.verified:
            return TestLoopRun(task, attempt, previous)

    return TestLoopRun(task, max_attempts, previous)
