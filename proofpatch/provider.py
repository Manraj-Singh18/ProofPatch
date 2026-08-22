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
    def complete(self, request: AgentRequest) -> AgentResponse:
        """Return proposed edits and optional claims; never decide verification status."""


class ProviderBackend:
    """Adapter that performs one model request per edit/verification attempt."""

    def __init__(self, provider: ModelProvider):
        self.provider = provider
        self._response: AgentResponse | None = None
        self._request_key: tuple[str, str] | None = None

    def _complete(self, task: str, context: RepositoryContext) -> AgentResponse:
        key = (task, context.commitment)
        if self._request_key != key:
            self._response = self.provider.complete(AgentRequest(task, context))
            self._request_key = key
        return self._response

    def propose_edits(self, task: str, repo: Path, context: RepositoryContext, previous=None) -> Sequence[FileEdit]:
        response = self._complete(task, context)
        return response.edits

    def claims(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]:
        response = self._complete(task, context)
        if response.claims:
            return response.claims
        # The local provider intentionally does not ask the model to self-attest.
        # ProofPatch creates a deterministic test claim and verifies it from pytest evidence.
        return (Claim("proofpatch-tests", "ALL_TESTS_PASS", "all tests pass"),)
