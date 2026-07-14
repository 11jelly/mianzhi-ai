from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.interview_answer import InterviewAnswer
    from app.models.interview_question import InterviewQuestion


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "sequence", name="uq_interview_questions_session_sequence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id"),
        nullable=False,
        index=True,
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    expected_points: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    question_type: Mapped[str] = mapped_column(String(20), default="PRIMARY", nullable=False)
    parent_question_id: Mapped[str | None] = mapped_column(
        ForeignKey("interview_questions.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    session = relationship(
        "InterviewSession",
        back_populates="questions",
        foreign_keys=[session_id],
    )
    answer: Mapped["InterviewAnswer | None"] = relationship(
        back_populates="question",
        uselist=False,
    )
    parent_question: Mapped["InterviewQuestion | None"] = relationship(
        remote_side=[id],
        back_populates="follow_up_questions",
    )
    follow_up_questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="parent_question",
    )
