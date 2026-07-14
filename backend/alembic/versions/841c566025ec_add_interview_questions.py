"""add_interview_questions

Revision ID: 841c566025ec
Revises: 6fba3a7c8156
Create Date: 2026-06-22 16:29:40.285184
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "841c566025ec"
down_revision: str | None = "6fba3a7c8156"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_questions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("expected_points", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "sequence",
            name="uq_interview_questions_session_sequence",
        ),
    )
    op.create_index(
        op.f("ix_interview_questions_session_id"),
        "interview_questions",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_questions_session_id"), table_name="interview_questions")
    op.drop_table("interview_questions")
