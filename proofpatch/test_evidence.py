from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Iterable


class TestEvidenceError(RuntimeError):
    """Raised when test evidence cannot be collected."""


@dataclass(frozen=True)
class TestEvidence:
    """Normalized evidence extracted from a test command."""

    command: tuple[str, ...]
    exit_code: int
    passed: int
    failed: int
    errors: int
    raw_output: str

    @property
    def all_tests_pass(self) -> bool:
        return self.exit_code == 0 and self.failed == 0 and self.errors == 0 and self.passed > 0


_PYTEST_SUMMARY = re.compile(
    r"(?:(?P<passed>\d+)\s+passed)?"
    r"(?:,\s*)?(?:(?P<failed>\d+)\s+failed)?"
    r"(?:,\s*)?(?:(?P<errors>\d+)\s+errors?)?"
)


def _summary(output: str) -> tuple[int, int, int]:
    passed = failed = errors = 0
    for line in reversed(output.splitlines()):
        match = _PYTEST_SUMMARY.search(line)
        if match and any(match.groupdict().values()):
            passed = int(match.group("passed") or 0)
            failed = int(match.group("failed") or 0)
            errors = int(match.group("errors") or 0)
            break
    return passed, failed, errors


def collect_test_evidence(
    repo: str | Path = ".", command: Iterable[str] = ("pytest", "-q")
) -> TestEvidence:
    """Run a test command and normalize its result into deterministic evidence."""
    args = tuple(command)
    if not args:
        raise TestEvidenceError("test command cannot be empty")

    try:
        result = subprocess.run(
            list(args), cwd=Path(repo).resolve(), capture_output=True, text=True
        )
    except OSError as exc:
        raise TestEvidenceError(f"unable to execute test command: {' '.join(args)}") from exc

    output = (result.stdout + result.stderr).strip()
    passed, failed, errors = _summary(output)
    return TestEvidence(
        command=args,
        exit_code=result.returncode,
        passed=passed,
        failed=failed,
        errors=errors,
        raw_output=output,
    )
