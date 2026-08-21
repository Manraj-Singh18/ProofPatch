from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Sequence


class GitEvidenceError(RuntimeError):
    """Raised when Git evidence cannot be collected."""


@dataclass(frozen=True)
class GitEvidence:
    """Deterministic snapshot of repository state relevant to a claim."""

    head: str
    branch: str | None
    status_porcelain: tuple[str, ...]
    changed_files: tuple[str, ...]
    diff: str


def _run_git(repo: Path, args: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise GitEvidenceError(f"git command failed: git {' '.join(args)}") from exc
    return result.stdout


def collect_git_evidence(repo: str | Path = ".") -> GitEvidence:
    """Collect repository HEAD, branch, status, changed files, and diff.

    All collections are sorted/canonicalized so equivalent repository states
    produce stable evidence suitable for hashing and verification.
    """
    root = Path(repo).resolve()
    head = _run_git(root, ["rev-parse", "HEAD"]).strip()
    branch = _run_git(root, ["branch", "--show-current"]).strip() or None
    status = tuple(
        line
        for line in _run_git(root, ["status", "--porcelain=v1", "--untracked-files=all"])
        .splitlines()
        if line
    )

    changed = set()
    for line in status:
        path = line[3:] if len(line) >= 4 else ""
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path:
            changed.add(path)

    diff = _run_git(root, ["diff", "--no-ext-diff", "--binary"])
    return GitEvidence(
        head=head,
        branch=branch,
        status_porcelain=tuple(sorted(status)),
        changed_files=tuple(sorted(changed)),
        diff=diff,
    )
