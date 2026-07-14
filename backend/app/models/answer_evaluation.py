from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnswerEvaluation(Base):
    __tablename__ = "answer_evaluations"
    __table_args__ = (
        CheckConstraint("total_score >= 0 AND total_score <= 100", name="ck_eval_total_score"),
        CheckConstraint("logic_score >= 0 AND logic_score <= 25", name="ck_eval_logic_score"),
        CheckConstraint(
            "technical_score >= 0 AND technical_score <= 30",
            name="ck_eval_technical_score",
        ),
        CheckConstraint(
            "expression_score >= 0 AND expression_score <= 20",
            name="ck_eval_expression_score",
        ),
        CheckConstraint(
            "project_depth_score >= 0 AND project_depth_score <= 25",
            name="ck_eval_project_depth_score",
        ),
        CheckConstraint(
            "total_score = logic_score + technical_score + expression_score + project_depth_score",
            name="ck_eval_total_score_sum",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    answer_id: Mapped[str] = mapped_column(
        ForeignKey("interview_answers.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    logic_score: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_score: Mapped[int] = mapped_column(Integer, nullable=False)
    expression_score: Mapped[int] = mapped_column(Integer, nullable=False)
    project_depth_score: Mapped[int] = mapped_column(Integer, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    evidence_items_json: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    expression_metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    improvement_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    detailed_feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    answer = relationship("InterviewAnswer", back_populates="evaluation")

    @property
    def evidence_items(self) -> list[dict]:
        return self.evidence_items_json or []

    @property
    def expression_metrics(self) -> dict | None:
        return self.expression_metrics_json
