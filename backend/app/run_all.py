"""Run both FastAPI (Uvicorn) and the background Worker in one process."""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn
from app.worker import main as worker_main


async def run():
    print("Starting background worker...")
    worker_task = asyncio.create_task(worker_main())
    
    print("Starting Uvicorn server...")
    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()
    
    worker_task.cancel()


if __name__ == "__main__":
    asyncio.run(run())