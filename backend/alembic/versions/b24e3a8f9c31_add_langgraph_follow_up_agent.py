"""add_langgraph_follow_up_agent

Revision ID: b24e3a8f9c31
Revises: a17c0d9f4b12
Create Date: 2026-06-22 21:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b24e3a8f9c31"
down_revision: str | None = "a17c0d9f4b12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interview_questions",
        sa.Column("question_type", sa.String(length=20), nullable=False, server_default="PRIMARY"),
    )
    op.add_column(
        "interview_questions",
        sa.Column("parent_question_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        op.f("ix_interview_questions_parent_question_id"),
        "interview_questions",
        ["parent_question_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_interview_questions_parent_question_id",
        "interview_questions",
        "interview_questions",
        ["parent_question_id"],
        ["id"],
    )

    op.add_column(
        "interview_sessions",
        sa.Column("current_question_id", sa.String(length=36), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("follow_up_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        op.f("ix_interview_sessions_current_question_id"),
        "interview_sessions",
        ["current_question_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_interview_sessions_current_question_id",
        "interview_sessions",
        "interview_questions",
        ["current_question_id"],
        ["id"],
    )

    op.create_table(
        "interview_agent_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("source_question_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("decision", sa.String(length=40), nullable=False),
        sa.Column("reason_summary", sa.Text(), nullable=True),
        sa.Column("follow_up_question_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.ForeignKeyConstraint(["source_question_id"], ["interview_questions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interview_agent_events_session_id"),
        "interview_agent_events",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_interview_agent_events_source_question_id"),
        "interview_agent_events",
        ["source_question_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_interview_agent_events_source_question_id"),
        table_name="interview_agent_events",
    )
    op.drop_index(op.f("ix_interview_agent_events_session_id"), table_name="interview_agent_events")
    op.drop_table("interview_agent_events")
    op.drop_constraint(
        "fk_interview_sessions_current_question_id",
        "interview_sessions",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_interview_sessions_current_question_id"),
        table_name="interview_sessions",
    )
    op.drop_column("interview_sessions", "follow_up_count")
    op.drop_column("interview_sessions", "current_question_id")
    op.drop_constraint(
        "fk_interview_questions_parent_question_id",
        "interview_questions",
        type_="foreignkey",
    )
    op.drop_index(
        op.f("ix_interview_questions_parent_question_id"),
        table_name="interview_questions",
    )
    op.drop_column("interview_questions", "parent_question_id")
    op.drop_column("interview_questions", "question_type")
