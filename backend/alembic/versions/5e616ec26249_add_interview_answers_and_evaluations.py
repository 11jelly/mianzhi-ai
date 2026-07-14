"""add_interview_answers_and_evaluations

Revision ID: 5e616ec26249
Revises: 841c566025ec
Create Date: 2026-06-22 17:50:01.514938
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5e616ec26249"
down_revision: str | None = "841c566025ec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_answers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("question_id", sa.String(length=36), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["interview_questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interview_answers_question_id"),
        "interview_answers",
        ["question_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_interview_answers_session_id"),
        "interview_answers",
        ["session_id"],
        unique=False,
    )

    op.create_table(
        "answer_evaluations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("answer_id", sa.String(length=36), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("logic_score", sa.Integer(), nullable=False),
        sa.Column("technical_score", sa.Integer(), nullable=False),
        sa.Column("expression_score", sa.Integer(), nullable=False),
        sa.Column("project_depth_score", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("improvement_suggestion", sa.Text(), nullable=False),
        sa.Column("detailed_feedback", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("total_score >= 0 AND total_score <= 100", name="ck_eval_total_score"),
        sa.CheckConstraint("logic_score >= 0 AND logic_score <= 25", name="ck_eval_logic_score"),
        sa.CheckConstraint(
            "technical_score >= 0 AND technical_score <= 30",
            name="ck_eval_technical_score",
        ),
        sa.CheckConstraint(
            "expression_score >= 0 AND expression_score <= 20",
            name="ck_eval_expression_score",
        ),
        sa.CheckConstraint(
            "project_depth_score >= 0 AND project_depth_score <= 25",
            name="ck_eval_project_depth_score",
        ),
        sa.CheckConstraint(
            "total_score = logic_score + technical_score + expression_score + project_depth_score",
            name="ck_eval_total_score_sum",
        ),
        sa.ForeignKeyConstraint(["answer_id"], ["interview_answers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_answer_evaluations_answer_id"),
        "answer_evaluations",
        ["answer_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_answer_evaluations_answer_id"), table_name="answer_evaluations")
    op.drop_table("answer_evaluations")
    op.drop_index(op.f("ix_interview_answers_session_id"), table_name="interview_answers")
    op.drop_index(op.f("ix_interview_answers_question_id"), table_name="interview_answers")
    op.drop_table("interview_answers")
