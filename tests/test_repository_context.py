from pathlib import Path

from proofpatch.repository_context import build_repository_context


def _git(repo: Path, *args: str) -> None:
    import subprocess
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def test_context_contains_repo_state_and_bounded_readme(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n\nA repository.\n")
    (tmp_path / "app.py").write_text("print('hello')\n")
    _git(tmp_path, "add", "README.md", "app.py")
    _git(tmp_path, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init")

    context = build_repository_context(tmp_path, max_readme_chars=10)

    assert context.branch == "main"
    assert context.head
    assert context.files == (".proofpatch-test-init", "README.md", "app.py")
    assert context.readme == "# Demo\n\nA "


def test_context_includes_untracked_files(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("draft\n")

    context = build_repository_context(tmp_path)

    assert "?? notes.txt" in context.status
    assert "notes.txt" in context.files
