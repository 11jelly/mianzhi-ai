"""add_interview_reports

Revision ID: a17c0d9f4b12
Revises: 5e616ec26249
Create Date: 2026-06-22 20:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a17c0d9f4b12"
down_revision: str | None = "5e616ec26249"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_reports",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("overall_score", sa.Integer(), nullable=False),
        sa.Column("logic_score", sa.Integer(), nullable=False),
        sa.Column("technical_score", sa.Integer(), nullable=False),
        sa.Column("expression_score", sa.Integer(), nullable=False),
        sa.Column("project_depth_score", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("role_gap_analysis", sa.Text(), nullable=False),
        sa.Column("improvement_plan", sa.JSON(), nullable=False),
        sa.Column("next_practice_questions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_report_overall_score",
        ),
        sa.CheckConstraint(
            "logic_score >= 0 AND logic_score <= 25",
            name="ck_report_logic_score",
        ),
        sa.CheckConstraint(
            "technical_score >= 0 AND technical_score <= 30",
            name="ck_report_technical_score",
        ),
        sa.CheckConstraint(
            "expression_score >= 0 AND expression_score <= 20",
            name="ck_report_expression_score",
        ),
        sa.CheckConstraint(
            "project_depth_score >= 0 AND project_depth_score <= 25",
            name="ck_report_project_depth_score",
        ),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_interview_reports_session_id"),
        "interview_reports",
        ["session_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_reports_session_id"), table_name="interview_reports")
    op.drop_table("interview_reports")
