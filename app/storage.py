from __future__ import annotations

from threading import Lock
from app.models import JobRecord, JobStatus


class JobStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._jobs: dict[str, JobRecord] = {}

    def create(self, job_id: str) -> JobRecord:
        with self._lock:
            record = JobRecord(job_id=job_id, status=JobStatus.processing)
            self._jobs[job_id] = record
            return record

    def get(self, job_id: str) -> JobRecord | None:
        return self._jobs.get(job_id)

    def complete(self, job_id: str, result) -> None:
        with self._lock:
            rec = self._jobs.get(job_id)
            if not rec:
                return
            rec.status = JobStatus.completed
            rec.result = result
            self._jobs[job_id] = rec

    def fail(self, job_id: str, error: str) -> None:
        with self._lock:
            rec = self._jobs.get(job_id)
            if not rec:
                return
            rec.status = JobStatus.failed
            rec.error = error
            self._jobs[job_id] = rec


job_store = JobStore()
