"""ProofPatch: evidence-backed verification for AI coding claims."""

from .models import Claim, ClaimStatus, EvidenceItem, VerificationResult
from .pipeline import VerificationReport, verify_repository

__version__ = "0.1.0"

__all__ = [
    "Claim",
    "ClaimStatus",
    "EvidenceItem",
    "VerificationResult",
    "VerificationReport",
    "verify_repository",
]
