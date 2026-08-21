from proofpatch.models import Claim, ClaimStatus, EvidenceItem
from proofpatch.verifier import verify_claim


def test_only_files_modified_claim_is_contradicted_by_extra_file() -> None:
    claim = Claim(
        "files-1",
        "ONLY_FILES_MODIFIED",
        "only src/app.py was modified",
        files=("src/app.py",),
    )
    evidence = (
        EvidenceItem(
            kind="git",
            value={"changed_files": ["src/app.py", "tests/test_app.py"]},
            source="git status --porcelain",
        ),
    )

    result = verify_claim(claim, evidence)

    assert result.status == ClaimStatus.CONTRADICTED
    assert "tests/test_app.py" in result.reason


def test_only_files_modified_claim_is_verified_when_exact() -> None:
    claim = Claim(
        "files-2",
        "ONLY_FILES_MODIFIED",
        "only src/app.py was modified",
        files=("src/app.py",),
    )
    evidence = (
        EvidenceItem(
            kind="git",
            value={"changed_files": ["src/app.py"]},
            source="git status --porcelain",
        ),
    )

    assert verify_claim(claim, evidence).status == ClaimStatus.VERIFIED
