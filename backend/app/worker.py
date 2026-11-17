"""Standalone worker: polls for pending ingestion jobs and runs them."""
import asyncio
import signal
import sys
import traceback
import uuid

# ✅ مهم: قبل از هر import دیگری
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


WORKER_ID = f"worker-{uuid.uuid4().hex[:8]}"
POLL_INTERVAL = 3


async def claim_and_run_one() -> bool:
    """Claim one pending job, run it, return True if a job was processed."""
    from app.db.session import session_context
    from app.services.ingestion_worker import IngestionWorker
    from app.services.job_service import JobService

    async with session_context() as session:
        jobs = JobService(session)
        job = await jobs.claim_job(WORKER_ID)
        if job is None:
            return False

        print(f"[{WORKER_ID}] Claimed job {job.id} (library_id={job.library_id})")
        await session.commit()

        worker = IngestionWorker(worker_id=WORKER_ID)
        try:
            await worker.run(job.library_id, job.id)
            print(f"[{WORKER_ID}] Job {job.id} completed successfully")
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[{WORKER_ID}] ===== JOB FAILED =====")
            print(f"[{WORKER_ID}] Error: {type(e).__name__}: {e}")
            print(f"[{WORKER_ID}] Traceback:\n{tb}")
            print(f"[{WORKER_ID}] ========================")
            try:
                await jobs.update_progress(
                    job.id,
                    status="failed",
                    progress={"error": str(e), "traceback": tb},
                )
                await session.commit()
            except Exception as update_err:
                print(f"[{WORKER_ID}] Could not update job status: {update_err}")
        return True


async def main() -> None:
    print(f"=== Worker {WORKER_ID} started (polling every {POLL_INTERVAL}s) ===")
    print("Press Ctrl+C to stop.")

    stop = asyncio.Event()

    def handle_signal(*args):
        print("\n[worker] Stopping...")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            signal.signal(sig, lambda *a: stop.set())

    while not stop.is_set():
        try:
            processed = await claim_and_run_one()
            if not processed:
                await asyncio.sleep(POLL_INTERVAL)
        except Exception as e:
            print(f"[worker] Error in poll loop: {type(e).__name__}: {e}")
            traceback.print_exc()
            await asyncio.sleep(POLL_INTERVAL)

    print(f"=== Worker {WORKER_ID} stopped ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[worker] Interrupted by user")
        sys.exit(0)