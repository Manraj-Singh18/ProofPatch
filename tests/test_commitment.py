from proofpatch.commitment import canonicalize, evidence_commitment


def test_canonicalization_is_key_order_independent() -> None:
    left = {"b": 2, "a": {"y": 4, "x": 3}}
    right = {"a": {"x": 3, "y": 4}, "b": 2}
    assert canonicalize(left) == canonicalize(right)
    assert evidence_commitment(left) == evidence_commitment(right)


def test_commitment_changes_when_evidence_changes() -> None:
    assert evidence_commitment({"passed": 2}) != evidence_commitment({"passed": 3})


def test_commitment_is_sha256_hex() -> None:
    commitment = evidence_commitment({"status": "VERIFIED"})
    assert len(commitment) == 64
    int(commitment, 16)
