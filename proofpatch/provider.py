from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from .edit_loop import FileEdit
from .models import Claim
from .repository_context import RepositoryContext


@dataclass(frozen=True)
class AgentRequest:
    task: str
    context: RepositoryContext


@dataclass(frozen=True)
class AgentResponse:
    edits: tuple[FileEdit, ...]
    claims: tuple[Claim, ...]


class ModelProvider(Protocol):
    """Provider-neutral interface for a coding model."""

    def complete(self, request: AgentRequest) -> AgentResponse:
        """Return proposed edits and claims; do not decide verification status."""


class ProviderBackend:
    """Adapter from a model provider to the bounded edit-loop backend."""

    def __init__(self, provider: ModelProvider):
        self.provider = provider

    def propose_edits(self, task: str, repo: Path, context: RepositoryContext, previous=None) -> Sequence[FileEdit]:
        return self.provider.complete(AgentRequest(task, context)).edits

    def claims(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]:
        return self.provider.complete(AgentRequest(task, context)).claims
