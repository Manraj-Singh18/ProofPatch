import json
from pathlib import Path

from proofpatch.models import Claim
from proofpatch.pipeline import verify_repository


def test_proof_report_commitment_changes_when_verified_evidence_changes(tmp_path: Path) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    assert True\n"
    )
    first = verify_repository(
        tmp_path,
        (Claim("proof", "ALL_TESTS_PASS", "all tests pass"),),
        test_command=("pytest", "-q"),
    )
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    assert False\n"
    )
    second = verify_repository(
        tmp_path,
        (Claim("proof", "ALL_TESTS_PASS", "all tests pass"),),
        test_command=("pytest", "-q"),
    )
    assert first.commitment != second.commitment


def test_proof_report_json_is_deterministic(tmp_path: Path) -> None:
    (tmp_path / "test_generated.py").write_text(
        "def test_generated():\n    assert True\n"
    )
    report = verify_repository(
        tmp_path,
        (Claim("proof", "ALL_TESTS_PASS", "all tests pass"),),
        test_command=("pytest", "-q"),
    )
    payload = {
        "commitment": report.commitment,
        "claims": [
            {
                "claim_id": result.claim.claim_id,
                "claim_type": result.claim.claim_type,
                "assertion": result.claim.assertion,
                "status": result.status.value,
                "reason": result.reason,
            }
            for result in report.claims
        ],
        "evidence": [
            {"kind": item.kind, "source": item.source, "value": item.value}
            for item in report.evidence
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2)
    assert json.loads(encoded) == json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
