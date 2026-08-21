from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from .models import Claim
from .pipeline import VerificationReport, verify_repository


class AgentBackend(Protocol):
    """Model adapter used by the coding-agent runtime."""

    def solve(self, task: str, repo: Path) -> Sequence[Claim]:
        """Implement the task and return claims about the resulting state."""


@dataclass(frozen=True)
class AgentRun:
    task: str
    claims: tuple[Claim, ...]
    verification: VerificationReport

    @property
    def accepted(self) -> bool:
        return self.verification.verified


class CodingAgent:
    """Minimal verification-first coding-agent runtime.

    The backend is responsible only for making repository changes and returning
    claims. ProofPatch independently verifies those claims before accepting the run.
    """

    def __init__(self, backend: AgentBackend):
        self.backend = backend

    def run(
        self,
        task: str,
        repo: str | Path = ".",
        test_command: Sequence[str] = ("pytest", "-q"),
    ) -> AgentRun:
        root = Path(repo).resolve()
        claims = tuple(self.backend.solve(task, root))
        verification = verify_repository(root, claims, test_command=test_command)
        return AgentRun(task=task, claims=claims, verification=verification)
