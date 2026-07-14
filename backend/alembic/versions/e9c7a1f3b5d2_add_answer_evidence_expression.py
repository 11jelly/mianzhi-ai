"""add_answer_evidence_expression

Revision ID: e9c7a1f3b5d2
Revises: d4f0b7a2c91e
Create Date: 2026-06-24 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from alembic import op

revision: str = "e9c7a1f3b5d2"
down_revision: str | None = "d4f0b7a2c91e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = mysql.JSON() if op.get_context().dialect.name == "mysql" else sa.JSON()
    op.add_column(
        "interview_answers",
        sa.Column("recording_duration_seconds", sa.Float(), nullable=True),
    )
    op.add_column(
        "answer_evaluations",
        sa.Column("evidence_items_json", json_type, nullable=True),
    )
    op.add_column(
        "answer_evaluations",
        sa.Column("expression_metrics_json", json_type, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("answer_evaluations", "expression_metrics_json")
    op.drop_column("answer_evaluations", "evidence_items_json")
    op.drop_column("interview_answers", "recording_duration_seconds")
