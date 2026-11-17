"""Aggregate all v1 routers."""
from fastapi import APIRouter

from app.api.v1 import audio, books, embeddings, health, vocabulary

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(books.router)
api_router.include_router(audio.router)
api_router.include_router(vocabulary.router)
api_router.include_router(embeddings.router)