"""Ingestion Worker: processes library files in batches."""
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import Library
from app.services.job_service import JobService
from app.services.library_service import LibraryService


@dataclass
class WorkerStats:
    pdf_processed: int = 0
    pdf_failed: int = 0
    audio_processed: int = 0
    audio_failed: int = 0


class IngestionWorker:
    def __init__(self, worker_id: str = "default") -> None:
        self._worker_id = worker_id

    async def run(self, library_id: uuid.UUID, job_id: uuid.UUID) -> None:
        from app.db.session import session_context

        async with session_context() as session:
            jobs = JobService(session)
            libs = LibraryService(session)

            job = await jobs.get_job(job_id)
            if job is None:
                return

            lib = await libs.get_library(library_id)
            if lib is None:
                await jobs.update_progress(job_id, status="failed", progress={"error": "Library not found"})
                await session.commit()
                return

            await jobs.update_progress(job_id, stage="scanning", status="running")
            await session.commit()

            scan = await libs.scan_library(library_id)
            await session.commit()
            total = scan.total_files
            if total == 0:
                await jobs.update_progress(job_id, status="completed", progress={"total": 0})
                await session.commit()
                return

            stats = WorkerStats()
            processed = 0

            # Step 1: Register all files
            for f in scan.files:
                try:
                    if f.media_type == "application/pdf":
                        await self._register_pdf(session, lib, f, jobs, job_id)
                    else:
                        await self._register_audio(session, lib, f, jobs, job_id)
                    await session.commit()
                except Exception as e:
                    print(f"[worker] Register failed for {f.relative_path}: {type(e).__name__}: {e}")
                    await session.rollback()
                    continue

                processed += 1
                if processed % 10 == 0:
                    await jobs.update_progress(
                        job_id,
                        progress={"stage": "registering", "total": total, "done": processed, "current_file": f.relative_path},
                    )
                    await session.commit()

            await jobs.update_progress(
                job_id,
                progress={"stage": "registering", "total": total, "done": processed},
            )
            await session.commit()

            # Step 2: OCR first PDF
            await jobs.update_progress(job_id, stage="ocr")
            await session.commit()

            pdfs = [f for f in scan.files if f.media_type == "application/pdf"]
            if pdfs:
                try:
                    await self._ocr_sample_pdf(session, lib, pdfs[0], jobs, job_id)
                    stats.pdf_processed = 1
                except Exception as e:
                    print(f"[worker] OCR failed: {type(e).__name__}: {e}")
                    stats.pdf_failed = 1
                await session.commit()

            # Step 3: STT first 2 audios
            await jobs.update_progress(job_id, stage="stt")
            await session.commit()

            audios = [f for f in scan.files if f.media_type != "application/pdf"][:2]
            for audio_file in audios:
                try:
                    await self._stt_sample_audio(session, lib, audio_file, jobs, job_id)
                    stats.audio_processed += 1
                except Exception as e:
                    print(f"[worker] STT failed: {type(e).__name__}: {e}")
                    stats.audio_failed += 1
                await session.commit()

            # Complete
            await jobs.update_progress(
                job_id,
                status="completed",
                stage="done",
                progress={
                    "total": total,
                    "registered": processed,
                    "pdf_processed": stats.pdf_processed,
                    "pdf_failed": stats.pdf_failed,
                    "audio_processed": stats.audio_processed,
                    "audio_failed": stats.audio_failed,
                },
            )
            await session.commit()

    async def _register_pdf(self, session, lib, f, jobs, job_id):
        from app.services.ingestion_service import IngestionService
        svc = IngestionService(session)
        book = await svc.get_or_create_book(lib.name)
        await svc.register_source_file(book, Path(f.path), relative_path=f.relative_path)

    async def _register_audio(self, session, lib, f, jobs, job_id):
        from app.services.ingestion_service import IngestionService
        svc = IngestionService(session)
        book = await svc.get_or_create_book(lib.name)
        await svc.register_audio_file(book, Path(f.path), relative_path=f.relative_path)

    async def _ocr_sample_pdf(self, session, lib, f, jobs, job_id):
        from app.services.ingestion_service import IngestionService
        svc = IngestionService(session)
        book = await svc.get_or_create_book(lib.name)
        pdf_path = Path(f.path)
        src = await svc.register_source_file(book, pdf_path, relative_path=f.relative_path)

        for pn in range(min(2, src.page_count or 0)):
            n = await svc.ingest_page(src, pdf_path, pn)
            print(f"[worker] OCR page {pn+1}: {n} blocks")
            await session.commit()

    async def _stt_sample_audio(self, session, lib, f, jobs, job_id):
        from app.services.ingestion_service import IngestionService
        svc = IngestionService(session)
        book = await svc.get_or_create_book(lib.name)
        audio_path = Path(f.path)
        src = await svc.register_audio_file(book, audio_path, relative_path=f.relative_path)

        n = await svc.ingest_audio(src, audio_path)
        print(f"[worker] STT {f.relative_path}: {n} segments")
        await session.commit()