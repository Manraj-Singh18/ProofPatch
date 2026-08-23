from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence
import hashlib

from .commitment import evidence_commitment
from .edit_loop import EditLoopError, FileEdit, _apply_edits, _is_test_path, _normalized_path
from .evidence_ledger import build_ledger, file_hashes, patch_hash
from .models import Claim, ClaimStatus, EvidenceItem, VerificationResult
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


def _rejected_edit_report(error: EditLoopError) -> VerificationReport:
    claim = Claim("proofpatch-edit-policy", "EDIT_POLICY", "agent edits comply with protected-file policy")
    evidence = EvidenceItem(kind="integrity", source="edit-policy", value={"violation": str(error)})
    result = VerificationResult(claim=claim, status=ClaimStatus.CONTRADICTED, evidence=(evidence,), reason=str(error))
    package = {"claims": [{"claim_id": claim.claim_id, "claim_type": claim.claim_type, "assertion": claim.assertion, "status": result.status.value, "reason": result.reason}], "evidence": [{"kind": evidence.kind, "source": evidence.source, "value": evidence.value}]}
    return VerificationReport(claims=(result,), evidence=(evidence,), commitment=evidence_commitment(package))


def _with_ledger(report: VerificationReport, ledger: Sequence[EvidenceItem]) -> VerificationReport:
    evidence = tuple(report.evidence) + tuple(ledger)
    claims = [{"claim_id": r.claim.claim_id, "claim_type": r.claim.claim_type, "assertion": r.claim.assertion, "files": r.claim.files, "status": r.status.value, "reason": r.reason} for r in report.claims]
    commitment = evidence_commitment({"claims": claims, "evidence": [{"kind": e.kind, "source": e.source, "value": e.value} for e in evidence]})
    return VerificationReport(claims=report.claims, evidence=evidence, commitment=commitment)


def _mismatch_report(task: str, attempt: int, report: VerificationReport, ledger: Sequence[EvidenceItem]) -> TestLoopRun:
    claim = Claim("proofpatch-patch-integrity", "PATCH_INTEGRITY", "applied files match the proposed patch")
    evidence = EvidenceItem(kind="patch-application", source="proofpatch", value={"reason": "actual file hashes do not match proposed edit hashes", "matches_proposed": False})
    result = VerificationResult(claim=claim, status=ClaimStatus.CONTRADICTED, evidence=(evidence,), reason="applied file content does not match the proposed patch")
    final = _with_ledger(report, tuple(ledger) + (evidence,))
    claims = final.claims + (result,)
    package = {"claims": [{"claim_id": r.claim.claim_id, "claim_type": r.claim.claim_type, "assertion": r.claim.assertion, "files": r.claim.files, "status": r.status.value, "reason": r.reason} for r in claims], "evidence": [{"kind": e.kind, "source": e.source, "value": e.value} for e in final.evidence]}
    return TestLoopRun(task, attempt, VerificationReport(claims=claims, evidence=final.evidence, commitment=evidence_commitment(package)))


def _baseline_paths(context: RepositoryContext) -> set[str]:
    """Snapshot every repository file present at the start of the run."""
    return {_normalized_path(path) for path in context.files}


def run_test_loop(backend: TestLoopBackend, task: str, repo: str | Path = ".", test_command: Sequence[str] = ("pytest", "-q"), max_attempts: int = 3) -> TestLoopRun:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    root = Path(repo).resolve()
    previous = None

    # Capture the security baseline once, before any agent attempt can modify files.
    initial_context = build_repository_context(root)
    baseline_paths = _baseline_paths(initial_context)

    for attempt in range(1, max_attempts + 1):
        context = build_repository_context(root)
        tracked_paths = set(context.files)
        edits = tuple(backend.propose_edits(task, root, context, previous))
        normalized_edit_paths = tuple(_normalized_path(edit.path) for edit in edits)
        paths_to_hash = tuple(sorted(tracked_paths | set(normalized_edit_paths)))
        before = file_hashes(root, paths_to_hash)
        try:
            _apply_edits(root, edits, baseline_paths=baseline_paths)
        except EditLoopError as exc:
            return TestLoopRun(task, attempt, _rejected_edit_report(exc))
        after = file_hashes(root, paths_to_hash)
        changed_paths = list(normalized_edit_paths)

        protected_paths = {path for path in baseline_paths if _is_test_path(path)}
        protected_before = {path: before[path] for path in protected_paths if path in before}
        protected_after = {path: after.get(path) for path in protected_paths}

        expected_after = {
            normalized_path: hashlib.sha256(edit.content.encode("utf-8")).hexdigest()
            for normalized_path, edit in zip(normalized_edit_paths, edits)
        }
        actual_after = {p: after.get(p) for p in changed_paths}
        applied_matches_proposal = all(actual_after.get(p) == h for p, h in expected_after.items())
        ledger = build_ledger(root, edits, before, after, getattr(backend, "raw_response", None)) + (
            EvidenceItem(kind="patch-application", source="proofpatch", value={"patch_sha256": patch_hash(edits), "expected_after": expected_after, "actual_after": actual_after, "applied_matches_proposal": applied_matches_proposal, "matches_proposed": applied_matches_proposal}),
            EvidenceItem(kind="protected-files", source="sha256", value={"before": protected_before, "after": protected_after, "unchanged": protected_before == protected_after}),
        )
        post_context = build_repository_context(root)
        claims = tuple(backend.claims(task, root, post_context))
        previous = _with_ledger(verify_repository(root, claims, test_command=test_command), ledger)
        if not applied_matches_proposal:
            return _mismatch_report(task, attempt, previous, ledger)
        if previous.verified:
            return TestLoopRun(task, attempt, previous)
    return TestLoopRun(task, max_attempts, previous)
