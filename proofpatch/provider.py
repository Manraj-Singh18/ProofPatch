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
    raw_response: str | None = None


class ModelProvider(Protocol):
    def complete(self, request: AgentRequest) -> AgentResponse:
        """Return proposed edits and optional claims; never decide verification status."""


class ProviderBackend:
    """Adapter that performs one model request per edit attempt."""

    def __init__(self, provider: ModelProvider):
        self.provider = provider
        self._response: AgentResponse | None = None
        self._request_key: tuple[str, str] | None = None

    @property
    def raw_response(self) -> str | None:
        return self._response.raw_response if self._response else None

    def _complete(self, task: str, context: RepositoryContext) -> AgentResponse:
        key = (task, repr(context))
        if self._request_key != key:
            self._response = self.provider.complete(AgentRequest(task, context))
            self._request_key = key
        assert self._response is not None
        return self._response

    def propose_edits(self, task: str, repo: Path, context: RepositoryContext, previous=None) -> Sequence[FileEdit]:
        return self._complete(task, context).edits

    def claims(self, task: str, repo: Path, context: RepositoryContext) -> Sequence[Claim]:
        # Claims are not evidence and do not require a second model inference.
        # Reuse claims returned with the edit proposal when present; otherwise
        # use the deterministic claim that ProofPatch independently verifies.
        if self._response is not None and self._response.claims:
            return self._response.claims
        return (Claim("proofpatch-tests", "ALL_TESTS_PASS", "all tests pass"),)
