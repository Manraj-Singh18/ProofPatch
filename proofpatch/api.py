from __future__ import annotations

import traceback
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from uuid import uuid4

from .e2e_agent import run_local_agent


@dataclass
class AgentJob:
    id: str
    task: str
    repo: str
    status: str = "queued"
    report: dict[str, Any] | None = None
    error: str | None = None


class LocalAgentService:
    """In-process job service; inference runs off the HTTP request thread."""

    def __init__(self) -> None:
        self._jobs: dict[str, AgentJob] = {}
        self._lock = Lock()

    def submit(self, task: str, repo: str | Path) -> AgentJob:
        job = AgentJob(str(uuid4()), task, str(Path(repo).resolve()))
        with self._lock:
            self._jobs[job.id] = job
        return job

    def start(self, job_id: str, max_attempts: int = 3) -> AgentJob:
        with self._lock:
            job = self._jobs[job_id]
            if job.status in {"running", "accepted", "rejected", "failed"}:
                return job
            job.status = "running"
        Thread(target=self._run, args=(job_id, max_attempts), daemon=True).start()
        return self.get(job_id)  # type: ignore[return-value]

    def _run(self, job_id: str, max_attempts: int) -> None:
        job = self.get(job_id)
        if job is None:
            return
        try:
            print(f"[ProofPatch] job {job_id} started: {job.task}", flush=True)
            report = run_local_agent(job.task, job.repo, max_attempts=max_attempts)
            with self._lock:
                job.report = report.to_dict()
                job.status = "accepted" if report.accepted else "rejected"
            print(f"[ProofPatch] job {job_id} finished: {job.status}", flush=True)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
            with self._lock:
                job.error = error
                job.status = "failed"
            print(f"[ProofPatch] job {job_id} failed: {error}", flush=True)

    def get(self, job_id: str) -> AgentJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def as_dict(self, job_id: str) -> dict[str, Any] | None:
        return asdict(self.get(job_id)) if self.get(job_id) else None
