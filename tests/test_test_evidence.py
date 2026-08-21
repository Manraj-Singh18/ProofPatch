from pathlib import Path

from proofpatch.test_evidence import collect_test_evidence


def test_collects_passing_pytest_evidence(tmp_path: Path) -> None:
    (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert 1 == 1\n")
    evidence = collect_test_evidence(tmp_path)
    assert evidence.exit_code == 0
    assert evidence.passed == 1
    assert evidence.failed == 0
    assert evidence.errors == 0
    assert evidence.all_tests_pass is True


def test_does_not_call_failed_suite_successful(tmp_path: Path) -> None:
    (tmp_path / "test_bad.py").write_text("def test_bad():\n    assert 1 == 2\n")
    evidence = collect_test_evidence(tmp_path)
    assert evidence.exit_code != 0
    assert evidence.failed == 1
    assert evidence.all_tests_pass is False


def test_rejects_empty_command(tmp_path: Path) -> None:
    import pytest
    from proofpatch.test_evidence import TestEvidenceError

    with pytest.raises(TestEvidenceError):
        collect_test_evidence(tmp_path, ())
