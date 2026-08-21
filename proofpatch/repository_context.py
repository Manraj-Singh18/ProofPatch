from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


@dataclass(frozen=True)
class RepositoryContext:
    """Deterministic, bounded repository context presented to an agent."""

    root: str
    head: str
    branch: str | None
    files: tuple[str, ...]
    status: tuple[str, ...]
    readme: str


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout


def build_repository_context(repo: str | Path = ".", max_readme_chars: int = 12000) -> RepositoryContext:
    """Build a stable repository summary without exposing arbitrary file contents."""
    root = Path(repo).resolve()
    head = _git(root, "rev-parse", "HEAD").strip()
    branch = _git(root, "branch", "--show-current").strip() or None
    status = tuple(line for line in _git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines() if line)

    files = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        files.append(path.relative_to(root).as_posix())
    files.sort()

    readme_path = next((root / name for name in ("README.md", "README.rst", "README") if (root / name).is_file()), None)
    readme = readme_path.read_text(errors="replace")[:max_readme_chars] if readme_path else ""

    return RepositoryContext(
        root=str(root),
        head=head,
        branch=branch,
        files=tuple(files),
        status=tuple(sorted(status)),
        readme=readme,
    )
