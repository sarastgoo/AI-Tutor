"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # books
    op.create_table(
        "books",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("edition", sa.String(100)),
        sa.Column("level", sa.String(50)),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('draft','processing','review_required','ready','failed')", name="ck_books_status"),
    )

    # source_files
    op.create_table(
        "source_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relative_path", sa.String(500), nullable=False),
        sa.Column("media_type", sa.String(100), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("page_count", sa.Integer()),
        sa.Column("duration_ms", sa.BigInteger()),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("book_id", "relative_path", name="uq_source_files_book_path"),
    )
    op.create_index("ix_source_files_sha256", "source_files", ["sha256"])
    op.create_index("ix_source_files_book_id", "source_files", ["book_id"])

    # learning_nodes
    op.create_table(
        "learning_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="CASCADE")),
        sa.Column("node_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("sequence_no", sa.Integer(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("node_type IN ('unit','lesson','section','exercise','other')", name="ck_learning_nodes_type"),
        sa.CheckConstraint("parent_id IS NULL OR parent_id <> id", name="ck_learning_nodes_no_self_parent"),
    )
    op.create_index("ix_learning_nodes_book_parent", "learning_nodes", ["book_id", "parent_id"])

    # content_blocks
    op.create_table(
        "content_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("block_order", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(50), nullable=False),
        sa.Column("bbox", postgresql.JSONB()),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("corrected_text", sa.Text()),
        sa.Column("text_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ocr_confidence", sa.Float()),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_file_id", "page_number", "block_order", name="uq_content_blocks_position"),
        sa.CheckConstraint("page_number >= 1", name="ck_content_blocks_page"),
        sa.CheckConstraint("block_order >= 0", name="ck_content_blocks_order"),
    )
    op.create_index("ix_blocks_page", "content_blocks", ["source_file_id", "page_number", "block_order"])

    # node_content_mappings
    op.create_table(
        "node_content_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_blocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("node_id", "block_id", name="uq_node_content_mappings"),
    )

    # audio_tracks
    op.create_table(
        "audio_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_files.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("label", sa.String(200)),
        sa.Column("duration_ms", sa.BigInteger(), nullable=False),
        sa.Column("transcription_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # audio_segments
    op.create_table(
        "audio_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("segment_index", sa.Integer(), nullable=False),
        sa.Column("start_ms", sa.BigInteger(), nullable=False),
        sa.Column("end_ms", sa.BigInteger(), nullable=False),
        sa.Column("raw_transcript", sa.Text(), nullable=False),
        sa.Column("corrected_transcript", sa.Text()),
        sa.Column("transcript_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("track_id", "segment_index", name="uq_audio_segments_position"),
        sa.CheckConstraint("start_ms >= 0 AND end_ms > start_ms", name="ck_audio_segments_time"),
    )
    op.create_index("ix_audio_segments_time", "audio_segments", ["track_id", "start_ms"])

    # node_audio_mappings
    op.create_table(
        "node_audio_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("track_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audio_tracks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_ms", sa.BigInteger()),
        sa.Column("end_ms", sa.BigInteger()),
        sa.Column("confidence", sa.Float()),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # source_spans
    op.create_table(
        "source_spans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("content_block_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("content_blocks.id", ondelete="CASCADE")),
        sa.Column("audio_segment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audio_segments.id", ondelete="CASCADE")),
        sa.Column("start_offset", sa.Integer()),
        sa.Column("end_offset", sa.Integer()),
        sa.Column("start_ms", sa.BigInteger()),
        sa.Column("end_ms", sa.BigInteger()),
        sa.Column("source_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("num_nonnulls(content_block_id, audio_segment_id) = 1", name="ck_source_spans_one_target"),
    )

    # lexemes
    op.create_table(
        "lexemes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("lemma", sa.String(200), nullable=False),
        sa.Column("pos", sa.String(20), nullable=False),
        sa.Column("sense_key", sa.String(100), nullable=False, server_default="unspecified"),
        sa.Column("ipa", sa.String(200)),
        sa.Column("persian_meaning", sa.Text()),
        sa.Column("cefr_level", sa.String(10)),
        sa.Column("enrichment_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("language", "lemma", "pos", "sense_key", name="uq_lexemes_sense"),
    )
    op.create_index("ix_lexemes_lemma", "lexemes", ["lemma"])

    # vocabulary_occurrences
    op.create_table(
        "vocabulary_occurrences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_span_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_spans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lexeme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lexemes.id", ondelete="SET NULL")),
        sa.Column("surface_form", sa.String(200), nullable=False),
        sa.Column("token_index", sa.Integer(), nullable=False),
        sa.Column("normalized_form", sa.String(200), nullable=False),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_span_id", "token_index", name="uq_occurrence_position"),
    )
    op.create_index("ix_occurrences_lexeme", "vocabulary_occurrences", ["lexeme_id"])

    # lexeme_enrichments
    op.create_table(
        "lexeme_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("lexeme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lexemes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_profile_id", postgresql.UUID(as_uuid=True)),
        sa.Column("meaning_fa", sa.Text()),
        sa.Column("example", sa.Text()),
        sa.Column("example_origin", sa.String(20)),
        sa.Column("review_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # document_chunks
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learning_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="SET NULL")),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("chunker_version", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chunks_book_node", "document_chunks", ["book_id", "learning_node_id"])

    # chunk_source_spans
    op.create_table(
        "chunk_source_spans",
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_chunks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("source_span_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_spans.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ordinal", sa.Integer(), nullable=False),
    )

    # embedding_profiles
    op.create_table(
        "embedding_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_name", sa.String(200), nullable=False),
        sa.Column("model_revision", sa.String(100), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("distance_metric", sa.String(20), nullable=False, server_default="cosine"),
        sa.Column("preprocessing", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # chunk_embeddings (with pgvector)
    op.execute(
        """
        CREATE TABLE chunk_embeddings (
            chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
            profile_id UUID NOT NULL REFERENCES embedding_profiles(id) ON DELETE CASCADE,
            embedding vector NOT NULL,
            content_hash CHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            PRIMARY KEY (chunk_id, profile_id)
        )
        """
    )

    # learning_sessions
    op.create_table(
        "learning_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("active_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="SET NULL")),
        sa.Column("mode", sa.String(20), nullable=False, server_default="guided"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_sessions_user", "learning_sessions", ["user_id"])

    # chat_messages
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_messages_session", "chat_messages", ["session_id"])

    # exercise_attempts
    op.create_table(
        "exercise_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learning_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_kind", sa.String(50), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("evaluation", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("score", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # speaking_attempts
    op.create_table(
        "speaking_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recording_path", sa.String(500), nullable=False),
        sa.Column("transcript", sa.Text()),
        sa.Column("stt_profile", sa.String(100)),
        sa.Column("feedback", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("pronunciation_status", sa.String(50), nullable=False, server_default="not_assessed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # learning_progress
    op.create_table(
        "learning_progress",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("learning_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("learning_nodes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("mastery_estimate", sa.Float()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("last_studied_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # vocabulary_reviews
    op.create_table(
        "vocabulary_reviews",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("lexeme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lexemes.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("interval_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ease_factor", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column("repetitions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_result", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # error_patterns
    op.create_table(
        "error_patterns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ingestion_jobs
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("stage", sa.String(50)),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("progress", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("claimed_by", sa.String(200)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_jobs_book", "ingestion_jobs", ["book_id"])

    # processing_artifacts
    op.create_table(
        "processing_artifacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("processor_version", sa.String(100), nullable=False),
        sa.Column("output_path", sa.String(500), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # review_tasks
    op.create_table(
        "review_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("resolution", postgresql.JSONB()),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # export_jobs
    op.create_table(
        "export_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("scope", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("options", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("source_manifest_hash", sa.String(64)),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("output_path", sa.String(500)),
        sa.Column("error", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    for table in [
        "export_jobs",
        "review_tasks",
        "processing_artifacts",
        "ingestion_jobs",
        "error_patterns",
        "vocabulary_reviews",
        "learning_progress",
        "speaking_attempts",
        "exercise_attempts",
        "chat_messages",
        "learning_sessions",
        "chunk_embeddings",
        "embedding_profiles",
        "chunk_source_spans",
        "document_chunks",
        "lexeme_enrichments",
        "vocabulary_occurrences",
        "lexemes",
        "source_spans",
        "node_audio_mappings",
        "audio_segments",
        "audio_tracks",
        "node_content_mappings",
        "content_blocks",
        "learning_nodes",
        "source_files",
        "books",
        "users",
    ]:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")