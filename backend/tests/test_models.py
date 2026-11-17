"""Tests that all 28 tables were created correctly."""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


EXPECTED_TABLES = {
    "alembic_version",
    "users",
    "books",
    "source_files",
    "learning_nodes",
    "content_blocks",
    "node_content_mappings",
    "audio_tracks",
    "audio_segments",
    "node_audio_mappings",
    "source_spans",
    "lexemes",
    "lexeme_enrichments",
    "vocabulary_occurrences",
    "document_chunks",
    "chunk_source_spans",
    "embedding_profiles",
    "chunk_embeddings",
    "learning_sessions",
    "chat_messages",
    "exercise_attempts",
    "speaking_attempts",
    "learning_progress",
    "vocabulary_reviews",
    "error_patterns",
    "ingestion_jobs",
    "processing_artifacts",
    "review_tasks",
    "export_jobs",
}


@pytest.mark.asyncio
async def test_all_tables_exist(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT tablename FROM pg_tables "
            "WHERE schemaname = 'public' "
            "ORDER BY tablename"
        )
    )
    actual = {row[0] for row in result.fetchall()}
    missing = EXPECTED_TABLES - actual
    assert not missing, f"Missing tables: {missing}"


@pytest.mark.asyncio
async def test_pgvector_extension(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    )
    version = result.scalar_one_or_none()
    assert version is not None


@pytest.mark.asyncio
async def test_chunk_embeddings_has_vector_column(db_session: AsyncSession) -> None:
    result = await db_session.execute(
        text(
            "SELECT data_type, udt_name FROM information_schema.columns "
            "WHERE table_name = 'chunk_embeddings' AND column_name = 'embedding'"
        )
    )
    row = result.fetchone()
    assert row is not None
    assert row[1] == "vector"