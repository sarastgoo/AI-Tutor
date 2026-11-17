"""Retrieval Service: semantic search over document chunks."""
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embedding_service import EmbeddingService


@dataclass
class RetrievedChunk:
    """A retrieved chunk with its source provenance."""
    chunk_id: str
    content: str
    book_id: str
    score: float
    source_refs: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "book_id": self.book_id,
            "score": round(self.score, 4),
            "source_refs": self.source_refs,
        }


class RetrievalService:
    """Semantic search over chunks using embeddings."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._embedder = EmbeddingService(session)

    async def search(
        self,
        book_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Find top-k semantically similar chunks in a book."""
        # 1. Embed the query (with e5 'query:' prefix)
        profile = await self._embedder.get_or_create_profile()
        query_emb = self._embedder.model.encode(
            [f"query: {query}"],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        query_vec_str = "[" + ",".join(str(float(x)) for x in query_emb) + "]"

        # 2. Search using cosine similarity
        # pgvector's <=> operator is cosine distance; similarity = 1 - distance
        sql = text(
            """
            SELECT
                ce.chunk_id::text AS chunk_id,
                dc.content AS content,
                dc.book_id::text AS book_id,
                1 - (ce.embedding <=> CAST(:query_vec AS vector)) AS score
            FROM chunk_embeddings ce
            JOIN document_chunks dc ON dc.id = ce.chunk_id
            WHERE dc.book_id = CAST(:book_id AS uuid)
              AND ce.profile_id = CAST(:profile_id AS uuid)
            ORDER BY ce.embedding <=> CAST(:query_vec AS vector) ASC
            LIMIT :limit
            """
        )
        rows = await self._session.execute(
            sql,
            {
                "query_vec": query_vec_str,
                "book_id": book_id,
                "profile_id": str(profile.id),
                "limit": top_k,
            },
        )

        results: list[RetrievedChunk] = []
        for row in rows:
            # 3. For each chunk, load source refs (page numbers, etc.)
            source_refs = await self._get_source_refs(row.chunk_id)
            results.append(
                RetrievedChunk(
                    chunk_id=row.chunk_id,
                    content=row.content,
                    book_id=row.book_id,
                    score=float(row.score),
                    source_refs=source_refs,
                )
            )
        return results

    async def _get_source_refs(self, chunk_id: str) -> list[dict[str, Any]]:
        """Get provenance info for a chunk: page numbers, block ids."""
        sql = text(
            """
            SELECT DISTINCT
                cb.page_number,
                cb.source_file_id::text AS source_file_id,
                sf.relative_path
            FROM chunk_source_spans css
            JOIN source_spans ss ON ss.id = css.source_span_id
            JOIN content_blocks cb ON cb.id = ss.content_block_id
            JOIN source_files sf ON sf.id = cb.source_file_id
            WHERE css.chunk_id = CAST(:chunk_id AS uuid)
            ORDER BY cb.page_number
            """
        )
        rows = await self._session.execute(sql, {"chunk_id": chunk_id})
        return [
            {
                "page_number": r.page_number,
                "source_file_id": r.source_file_id,
                "source_file": r.relative_path,
            }
            for r in rows
        ]