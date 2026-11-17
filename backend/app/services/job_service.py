"""Job Service: manage ingestion jobs in the database."""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operations import IngestionJob


@dataclass
class JobStatus:
    id: uuid.UUID
    book_id: uuid.UUID | None
    status: str
    stage: str | None
    progress: dict
    attempt_count: int
    created_at: datetime


class JobService:
    """Creates and manages background jobs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(
        self, book_id: uuid.UUID | None = None, library_id: uuid.UUID | None = None
    ) -> IngestionJob:
        job = IngestionJob(
            book_id=book_id,
            library_id=library_id,
            status="pending",
            stage="queued",
            progress={"total": 0, "done": 0, "message": "Job queued"},
            attempt_count=0,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def get_job(self, job_id: uuid.UUID) -> IngestionJob | None:
        stmt = select(IngestionJob).where(IngestionJob.id == job_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update_progress(
        self,
        job_id: uuid.UUID,
        *,
        stage: str | None = None,
        status: str | None = None,
        progress: dict | None = None,
    ) -> None:
        job = await self.get_job(job_id)
        if job is None:
            return
        if stage is not None:
            job.stage = stage
        if status is not None:
            job.status = status
        if progress is not None:
            job.progress = progress
        await self._session.flush()

    async def claim_job(self, worker_id: str) -> IngestionJob | None:
        """Atomically claim a pending job for this worker."""
        stmt = (
            select(IngestionJob)
            .where(IngestionJob.status == "pending")
            .order_by(IngestionJob.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = (await self._session.execute(stmt)).scalar_one_or_none()
        if job is None:
            return None
        job.status = "running"
        job.claimed_by = worker_id
        job.heartbeat_at = datetime.now(timezone.utc)
        job.attempt_count += 1
        await self._session.flush()
        return job