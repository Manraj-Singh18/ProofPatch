"""Core data models for evidence-backed claim verification."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ClaimStatus(str, Enum):
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass(frozen=True)
class EvidenceItem:
    """A deterministic observation used to evaluate a claim."""

    kind: str
    value: Any
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Claim:
    """A structured assertion made by an AI coding agent."""

    claim_id: str
    claim_type: str
    assertion: str
    files: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VerificationResult:
    """Result of deterministic evidence evaluation."""

    claim: Claim
    status: ClaimStatus
    evidence: tuple[EvidenceItem, ...] = ()
    reason: str = ""
