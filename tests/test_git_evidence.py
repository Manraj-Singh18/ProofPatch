from pathlib import Path
import subprocess

from proofpatch.git_evidence import collect_git_evidence


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def test_collects_head_branch_and_clean_state(tmp_path: Path) -> None:
    git(tmp_path, "init", "-b", "main")
    (tmp_path / "README.md").write_text("hello\n")
    git(tmp_path, "add", "README.md")
    git(tmp_path, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init")

    evidence = collect_git_evidence(tmp_path)

    assert evidence.head == git(tmp_path, "rev-parse", "HEAD")
    assert evidence.branch == "main"
    assert evidence.status_porcelain == ()
    assert evidence.changed_files == ()
    assert evidence.diff == ""


def test_collects_untracked_and_modified_files(tmp_path: Path) -> None:
    git(tmp_path, "init", "-b", "main")
    (tmp_path / "tracked.txt").write_text("one\n")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-m", "init")
    (tmp_path / "tracked.txt").write_text("two\n")
    (tmp_path / "new.txt").write_text("new\n")

    evidence = collect_git_evidence(tmp_path)

    assert " M tracked.txt" in evidence.status_porcelain
    assert "?? new.txt" in evidence.status_porcelain
    assert evidence.changed_files == ("new.txt", "tracked.txt")
    assert "-one" in evidence.diff
    assert "+two" in evidence.diff
