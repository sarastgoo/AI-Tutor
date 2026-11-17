"""Direct worker test with verbose logging."""
import asyncio
import sys
import traceback

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    print("=" * 60)
    print("DIRECT WORKER TEST")
    print("=" * 60)

    from app.db.session import session_context
    from app.services.job_service import JobService
    from app.services.library_service import LibraryService
    from app.services.ingestion_worker import IngestionWorker

    async with session_context() as session:
        jobs = JobService(session)
        libs = LibraryService(session)

        print("\n[1] Claiming job...")
        job = await jobs.claim_job("direct-test")
        if job is None:
            print("    No pending jobs found.")
            return
        print(f"    Claimed: {job.id}")
        print(f"    Library: {job.library_id}")
        await session.commit()

        print("\n[2] Loading library...")
        lib = await libs.get_library(job.library_id)
        print(f"    Name: {lib.name}")
        print(f"    Root: {lib.root_path}")

        print("\n[3] Updating progress (scanning)...")
        await jobs.update_progress(job.id, stage="scanning", status="running")
        await session.commit()
        print("    OK")

        print("\n[4] Scanning library...")
        scan = await libs.scan_library(job.library_id)
        print(f"    Found {scan.total_files} files")
        await session.commit()

        print(f"\n[5] Registering {len(scan.files)} files...")
        worker = IngestionWorker("direct-test")
        for i, f in enumerate(scan.files, start=1):
            print(f"    [{i}/{len(scan.files)}] {f.relative_path} ({f.media_type})", flush=True)
            try:
                if f.media_type == "application/pdf":
                    await worker._register_pdf(session, lib, f, jobs, job.id)
                else:
                    await worker._register_audio(session, lib, f, jobs, job.id)
                await session.commit()
            except Exception as e:
                print(f"        FAILED: {type(e).__name__}: {e}")
                traceback.print_exc()
                await session.rollback()
                return

        print("\n[6] OCR on first PDF (2 pages)...")
        pdfs = [f for f in scan.files if f.media_type == "application/pdf"]
        if pdfs:
            try:
                await worker._ocr_sample_pdf(session, lib, pdfs[0], jobs, job.id)
                print("    OCR OK")
            except Exception as e:
                print(f"    OCR FAILED: {type(e).__name__}: {e}")
                traceback.print_exc()

        print("\n[7] STT on first 2 audios...")
        audios = [f for f in scan.files if f.media_type != "application/pdf"][:2]
        for audio_file in audios:
            print(f"    Transcribing {audio_file.relative_path}...")
            try:
                await worker._stt_sample_audio(session, lib, audio_file, jobs, job.id)
                print("        OK")
            except Exception as e:
                print(f"        FAILED: {type(e).__name__}: {e}")
                traceback.print_exc()

        print("\n[8] Marking completed...")
        await jobs.update_progress(
            job.id,
            status="completed",
            stage="done",
            progress={
                "total": scan.total_files,
                "registered": len(scan.files),
            },
        )
        await session.commit()
        print("    DONE")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
    print("=" * 60)
    print("TEST FINISHED")
    print("=" * 60)