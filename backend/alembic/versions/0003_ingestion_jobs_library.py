"""add library_id to ingestion_jobs, make book_id nullable

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Make book_id nullable
    op.alter_column(
        "ingestion_jobs",
        "book_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    # 2. Add library_id column
    op.add_column(
        "ingestion_jobs",
        sa.Column("library_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # 3. Add foreign key
    op.create_foreign_key(
        "fk_ingestion_jobs_library_id",
        "ingestion_jobs",
        "libraries",
        ["library_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # 4. Add index
    op.create_index("ix_jobs_library", "ingestion_jobs", ["library_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_library", table_name="ingestion_jobs")
    op.drop_constraint("fk_ingestion_jobs_library_id", "ingestion_jobs", type_="foreignkey")
    op.drop_column("ingestion_jobs", "library_id")
    op.alter_column(
        "ingestion_jobs",
        "book_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )