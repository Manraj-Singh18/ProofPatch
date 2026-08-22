from pathlib import Path

from proofpatch.api import LocalAgentService


def test_local_agent_service_submit_and_get(tmp_path: Path) -> None:
    service = LocalAgentService()
    job = service.submit("fix add", tmp_path)
    assert job.status == "queued"
    assert job.task == "fix add"
    assert Path(job.repo) == tmp_path.resolve()
    assert service.get(job.id) == job


def test_local_agent_service_missing_job() -> None:
    assert LocalAgentService().get("missing") is None
