"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config import settings
from app.db.session import check_db_connection, engine
from app.logging import configure_logging, get_logger

configure_logging(settings.LOG_LEVEL)
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup + shutdown hooks."""
    log.info("app_starting", version=settings.APP_VERSION, env=settings.ENVIRONMENT)
    ok = await check_db_connection()
    if not ok:
        log.error("db_unavailable_at_startup")
    else:
        log.info("db_connected")
    yield
    log.info("app_shutting_down")
    await engine.dispose()


app = FastAPI(
    title="AI English Tutor",
    version=settings.APP_VERSION,
    description="Local-first bilingual AI English tutor",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "prod" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    import uuid

    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback

    request_id = getattr(request.state, "request_id", None)
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    log.error(
        "unhandled_exception",
        exc_info=exc,
        request_id=request_id,
        path=str(request.url),
        traceback=tb,
    )
    detail = str(exc) if settings.ENVIRONMENT != "prod" else "An unexpected error occurred."
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": detail,
                "details": {},
                "request_id": request_id,
            }
        },
    )


app.include_router(api_router)