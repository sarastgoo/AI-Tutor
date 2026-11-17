"""Library Service: manage libraries and scan their source folders."""
import os
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.library import Library

# فایل‌های پشتیبانی شده
SUPPORTED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}


@dataclass
class ScannedFile:
    """A file found during library scan."""
    path: str
    relative_path: str
    media_type: str
    size_bytes: int


@dataclass
class ScanResult:
    """Result of scanning a library's root folder."""
    library_id: uuid.UUID
    root_path: str
    total_files: int
    pdf_files: int
    audio_files: int
    files: list[ScannedFile] = field(default_factory=list)


class LibraryService:
    """Scans and manages library source folders."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_library(self, name: str, root_path: str) -> Library:
        """Create a new library and a corresponding Book."""
        root = Path(root_path).resolve()
        if not root.exists():
            raise ValueError(f"Path does not exist: {root}")
        if not root.is_dir():
            raise ValueError(f"Path is not a directory: {root}")

        # ✅ ساخت Book
        from app.models.books import Book
        book = Book(title=name, language="en", status="draft")
        self._session.add(book)
        await self._session.flush()

        # ✅ ساخت Library با book_id
        lib = Library(
            name=name,
            root_path=str(root),
            status="created",
            book_id=book.id,
        )
        self._session.add(lib)
        await self._session.flush()
        return lib

    async def get_library(self, library_id: uuid.UUID) -> Library | None:
        stmt = select(Library).where(Library.id == library_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list_libraries(self) -> list[Library]:
        stmt = select(Library).order_by(Library.created_at.desc())
        return list((await self._session.execute(stmt)).scalars())

    async def scan_library(self, library_id: uuid.UUID, max_files: int | None = None) -> ScanResult:
        """Scan the library root path for supported files."""
        lib = await self.get_library(library_id)
        if lib is None:
            raise ValueError(f"Library not found: {library_id}")

        root = Path(lib.root_path)
        if not root.exists():
            raise ValueError(f"Library root path no longer exists: {root}")

        files: list[ScannedFile] = []
        pdf_count = 0
        audio_count = 0

        for dirpath, _dirnames, filenames in os.walk(root):
            for filename in filenames:
                path = Path(dirpath) / filename
                ext = path.suffix.lower()
                media_type = SUPPORTED_EXTENSIONS.get(ext)
                if media_type is None:
                    continue

                try:
                    size = path.stat().st_size
                except OSError:
                    continue  # skip unreadable files

                rel = path.relative_to(root).as_posix()
                files.append(
                    ScannedFile(
                        path=str(path),
                        relative_path=rel,
                        media_type=media_type,
                        size_bytes=size,
                    )
                )
                if media_type == "application/pdf":
                    pdf_count += 1
                else:
                    audio_count += 1

                if max_files is not None and len(files) >= max_files:
                    break
            if max_files is not None and len(files) >= max_files:
                break

        lib.status = "scanned"
        await self._session.flush()

        return ScanResult(
            library_id=lib.id,
            root_path=str(root),
            total_files=len(files),
            pdf_files=pdf_count,
            audio_files=audio_count,
            files=files,
        )