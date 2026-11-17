"""Aggregate all v1 routers."""
from fastapi import APIRouter

from app.api.v1 import (
    audio,
    books,
    embeddings,
    exports,
    health,
    progress,
    retrieval,
    speaking,
    speech,
    tutor,
    vocabulary,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(books.router)
api_router.include_router(audio.router)
api_router.include_router(vocabulary.router)
api_router.include_router(embeddings.router)
api_router.include_router(retrieval.router)
api_router.include_router(tutor.router)
api_router.include_router(speech.router)
api_router.include_router(speaking.router)
api_router.include_router(exports.router)
api_router.include_router(progress.router)