"""add_resume_rag

Revision ID: d4f0b7a2c91e
Revises: c39f8a21d7e4
Create Date: 2026-06-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "d4f0b7a2c91e"
down_revision: str | None = "c39f8a21d7e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interview_sessions",
        sa.Column("use_active_resume", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "user_resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("extracted_text_length", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_resumes_owner_id", "user_resumes", ["owner_id"])

    json_type = mysql.JSON() if op.get_context().dialect.name == "mysql" else sa.JSON()
    op.create_table(
        "resume_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", json_type, nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("chunk_metadata", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["resume_id"], ["user_resumes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resume_id", "chunk_index", name="uq_resume_chunks_resume_index"),
    )
    op.create_index("ix_resume_chunks_resume_id", "resume_chunks", ["resume_id"])

    op.create_table(
        "interview_resume_links",
        sa.Column("interview_session_id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=True),
        sa.Column("resume_title_snapshot", sa.String(length=100), nullable=False),
        sa.Column("resume_context_snapshot", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["interview_session_id"], ["interview_sessions.id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["user_resumes.id"]),
        sa.PrimaryKeyConstraint("interview_session_id"),
    )
    op.create_index("ix_interview_resume_links_resume_id", "interview_resume_links", ["resume_id"])


def downgrade() -> None:
    op.drop_index("ix_interview_resume_links_resume_id", table_name="interview_resume_links")
    op.drop_table("interview_resume_links")
    op.drop_index("ix_resume_chunks_resume_id", table_name="resume_chunks")
    op.drop_table("resume_chunks")
    op.drop_index("ix_user_resumes_owner_id", table_name="user_resumes")
    op.drop_table("user_resumes")
    op.drop_column("interview_sessions", "use_active_resume")
