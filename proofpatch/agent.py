from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from .models import Claim
from .pipeline import VerificationReport, verify_repository
from .repository_context import RepositoryContext, build_repository_context


class AgentBackend(Protocol):
    """Model adapter used by the coding-agent runtime."""

    def solve(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]:
        """Implement the task using explicit repository context and return claims."""


@dataclass(frozen=True)
class AgentRun:
    task: str
    claims: tuple[Claim, ...]
    verification: VerificationReport
    context: RepositoryContext

    @property
    def accepted(self) -> bool:
        return self.verification.verified


class CodingAgent:
    """Verification-first coding-agent runtime with bounded repository context."""

    def __init__(self, backend: AgentBackend):
        self.backend = backend

    def run(
        self,
        task: str,
        repo: str | Path = ".",
        test_command: Sequence[str] = ("pytest", "-q"),
    ) -> AgentRun:
        root = Path(repo).resolve()
        context = build_repository_context(root)
        claims = tuple(self.backend.solve(task, root, context))
        verification = verify_repository(root, claims, test_command=test_command)
        return AgentRun(task=task, claims=claims, verification=verification, context=context)
