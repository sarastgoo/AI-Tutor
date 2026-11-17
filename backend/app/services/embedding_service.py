"""Embedding Service: multilingual-e5-small for semantic search."""
import uuid
from dataclasses import dataclass
from typing import Any

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import ContentBlock, SourceSpan
from app.models.rag import (
    ChunkSourceSpan,
    DocumentChunk,
    EmbeddingProfile,
)


@dataclass
class EmbeddingResult:
    """Result of an embedding operation."""
    chunks_created: int
    embeddings_created: int
    elapsed_s: float


class EmbeddingService:
    """Creates chunks from content blocks and generates embeddings."""

    _model = None  # Lazy-loaded
    MODEL_NAME = "intfloat/multilingual-e5-small"
    MODEL_REVISION = "main"  # Update if pinning a specific revision
    DIMENSIONS = 384
    CHUNKER_VERSION = "v1-simple"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        if EmbeddingService._model is None:
            EmbeddingService._model = SentenceTransformer(self.MODEL_NAME)
            # Verify dimension
            dim = EmbeddingService._model.get_sentence_embedding_dimension()
            if dim != self.DIMENSIONS:
                raise RuntimeError(
                    f"Model dimension mismatch: expected {self.DIMENSIONS}, got {dim}"
                )

    @property
    def model(self) -> SentenceTransformer:
        return EmbeddingService._model

    async def get_or_create_profile(self) -> EmbeddingProfile:
        """Get or create the embedding profile for our model."""
        stmt = select(EmbeddingProfile).where(
            EmbeddingProfile.model_name == self.MODEL_NAME,
            EmbeddingProfile.model_revision == self.MODEL_REVISION,
        )
        result = await self._session.execute(stmt)
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = EmbeddingProfile(
                model_name=self.MODEL_NAME,
                model_revision=self.MODEL_REVISION,
                dimensions=self.DIMENSIONS,
                distance_metric="cosine",
                preprocessing={
                    "query_prefix": "query: ",
                    "passage_prefix": "passage: ",
                },
            )
            self._session.add(profile)
            await self._session.flush()
        return profile

    async def chunk_content_blocks(
        self, book_id: uuid.UUID, target_chunk_size: int = 400
    ) -> list[DocumentChunk]:
        """Group content blocks into chunks of ~target_chunk_size characters."""
        from app.models.sources import SourceFile

        # Load all blocks for the book
        stmt = (
            select(ContentBlock)
            .join(SourceFile, SourceFile.id == ContentBlock.source_file_id)
            .where(SourceFile.book_id == book_id)
            .order_by(
                ContentBlock.source_file_id,
                ContentBlock.page_number,
                ContentBlock.block_order,
            )
        )
        result = await self._session.execute(stmt)
        blocks = list(result.scalars())

        chunks: list[DocumentChunk] = []
        current_text = ""
        current_blocks: list[ContentBlock] = []

        for block in blocks:
            text = (block.corrected_text or block.raw_text).strip()
            if not text:
                continue

            # If adding this block exceeds target, finalize current chunk
            if current_text and len(current_text) + len(text) + 1 > target_chunk_size:
                chunk = await self._finalize_chunk(book_id, current_text, current_blocks)
                chunks.append(chunk)
                current_text = ""
                current_blocks = []

            if current_text:
                current_text += " "
            current_text += text
            current_blocks.append(block)

        # Final chunk
        if current_text:
            chunk = await self._finalize_chunk(book_id, current_text, current_blocks)
            chunks.append(chunk)

        return chunks

    async def _finalize_chunk(
        self,
        book_id: uuid.UUID,
        text: str,
        blocks: list[ContentBlock],
    ) -> DocumentChunk:
        """Create a DocumentChunk and link its source spans."""
        import hashlib

        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        chunk = DocumentChunk(
            book_id=book_id,
            learning_node_id=None,  # No learning node mapping yet (P5+)
            content=text,
            content_hash=content_hash,
            chunker_version=self.CHUNKER_VERSION,
            status="active",
        )
        self._session.add(chunk)
        await self._session.flush()

        # Link source spans (one per content block)
        for ordinal, block in enumerate(blocks):
            span_stmt = select(SourceSpan).where(SourceSpan.content_block_id == block.id)
            span = (await self._session.execute(span_stmt)).scalar_one_or_none()
            if span:
                self._session.add(
                    ChunkSourceSpan(
                        chunk_id=chunk.id,
                        source_span_id=span.id,
                        ordinal=ordinal,
                    )
                )

        await self._session.flush()
        return chunk

    async def embed_book(self, book_id: uuid.UUID) -> EmbeddingResult:
        """Chunk and embed all content blocks of a book."""
        import time

        from sqlalchemy import text

        t0 = time.time()
        profile = await self.get_or_create_profile()

        # Chunk
        chunks = await self.chunk_content_blocks(book_id)

        # Embed
        if chunks:
            passages = [f"passage: {c.content}" for c in chunks]
            embeddings = self.model.encode(
                passages,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
            )

            # Store embeddings (raw SQL because pgvector isn't a SQLAlchemy type)
            for chunk, emb in zip(chunks, embeddings, strict=True):
                emb_str = "[" + ",".join(str(float(x)) for x in emb) + "]"
                await self._session.execute(
                    text(
                        """
                        INSERT INTO chunk_embeddings
                            (chunk_id, profile_id, embedding, content_hash)
                        VALUES (:chunk_id, :profile_id, :embedding, :content_hash)
                        ON CONFLICT (chunk_id, profile_id) DO UPDATE
                            SET embedding = EXCLUDED.embedding,
                                content_hash = EXCLUDED.content_hash
                        """
                    ),
                    {
                        "chunk_id": chunk.id,
                        "profile_id": profile.id,
                        "embedding": emb_str,
                        "content_hash": chunk.content_hash,
                    },
                )

        elapsed = time.time() - t0
        return EmbeddingResult(
            chunks_created=len(chunks),
            embeddings_created=len(chunks),
            elapsed_s=elapsed,
        )