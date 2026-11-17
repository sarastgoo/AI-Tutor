"""Library management endpoints."""
import asyncio
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.services.job_service import JobService
from app.services.ingestion_worker import IngestionWorker
from app.api.deps import SessionDep
from app.models.library import Library
from app.schemas.library import (
    LibraryCreate,
    LibraryResponse,
    ScanResponse,
    ScannedFileDTO,
)
from app.services.library_service import LibraryService
from app.models.books import Book
from app.models.sources import SourceFile

router = APIRouter(tags=["libraries"])


@router.post(
    "/libraries",
    response_model=LibraryResponse,
    status_code=status.HTTP_201_CREATED,
)

async def create_library(body: LibraryCreate, session: SessionDep) -> Library:
    """Create a new library pointing to a local folder."""
    svc = LibraryService(session)
    try:
        lib = await svc.create_library(name=body.name, root_path=body.root_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return lib


@router.get("/libraries", response_model=list[LibraryResponse])
async def list_libraries(session: SessionDep) -> list[Library]:
    svc = LibraryService(session)
    return await svc.list_libraries()


@router.get("/libraries/{library_id}", response_model=LibraryResponse)
async def get_library(library_id: str, session: SessionDep) -> Library:
    svc = LibraryService(session)
    lib = await svc.get_library(library_id)  # type: ignore[arg-type]
    if lib is None:
        raise HTTPException(status_code=404, detail="Library not found")
    return lib


@router.post(
    "/libraries/{library_id}/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_library(
    library_id: str,
    session: SessionDep,
    max_files: int | None = None,
) -> ScanResponse:
    """Scan the library's root folder for supported files."""
    svc = LibraryService(session)
    try:
        result = await svc.scan_library(library_id, max_files=max_files)  # type: ignore[arg-type]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ScanResponse(
        library_id=result.library_id,
        root_path=result.root_path,
        total_files=result.total_files,
        pdf_files=result.pdf_files,
        audio_files=result.audio_files,
        files=[
            ScannedFileDTO(
                path=f.path,
                relative_path=f.relative_path,
                media_type=f.media_type,
                size_bytes=f.size_bytes,
            )
            for f in result.files
        ],
    )

# این endpoint را به فایل اضافه کنید (قبل از end فایل):
@router.post(
    "/libraries/{library_id}/ingest",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_ingestion(library_id: str, session: SessionDep) -> dict:
    """Queue a background ingestion job for a library.

    The worker (run separately) will pick this up and process it.
    """
    svc = LibraryService(session)
    lib = await svc.get_library(library_id)  # type: ignore[arg-type]
    if lib is None:
        raise HTTPException(status_code=404, detail="Library not found")

    jobs = JobService(session)
    job = await jobs.create_job(book_id=None, library_id=lib.id)
    await session.commit()

    return {
        "job_id": str(job.id),
        "library_id": str(lib.id),
        "status": "queued",
    }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, session: SessionDep) -> dict:
    """Get the status of a background job."""
    jobs = JobService(session)
    job = await jobs.get_job(job_id)  # type: ignore[arg-type]
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": str(job.id),
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "attempt_count": job.attempt_count,
        "created_at": job.created_at.isoformat(),
    }

@router.get("/libraries/{library_id}/books")
async def list_library_books(library_id: str, session: SessionDep) -> list[dict]:
    """List all Books associated with a Library."""
    # پیدا کردن SourceFileهای این Library
    stmt = select(SourceFile.book_id).where(
        SourceFile.book_id.in_(
            select(Book.id).where(Book.title.like(f"%{library_id}%")) # این منطق نیاز به اصلاح دارد
        )
    )