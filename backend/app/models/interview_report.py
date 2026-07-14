from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewReport(Base):
    __tablename__ = "interview_reports"
    __table_args__ = (
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_report_overall_score",
        ),
        CheckConstraint(
            "logic_score >= 0 AND logic_score <= 25",
            name="ck_report_logic_score",
        ),
        CheckConstraint(
            "technical_score >= 0 AND technical_score <= 30",
            name="ck_report_technical_score",
        ),
        CheckConstraint(
            "expression_score >= 0 AND expression_score <= 20",
            name="ck_report_expression_score",
        ),
        CheckConstraint(
            "project_depth_score >= 0 AND project_depth_score <= 25",
            name="ck_report_project_depth_score",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    overall_score: Mapped[int] = mapped_column(Integer, nullable=False)
    logic_score: Mapped[int] = mapped_column(Integer, nullable=False)
    technical_score: Mapped[int] = mapped_column(Integer, nullable=False)
    expression_score: Mapped[int] = mapped_column(Integer, nullable=False)
    project_depth_score: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    role_gap_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    improvement_plan: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    next_practice_questions: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    session = relationship("InterviewSession", back_populates="report")
