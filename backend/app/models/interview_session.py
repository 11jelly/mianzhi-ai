from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.interview_knowledge_base_link import InterviewKnowledgeBaseLink
    from app.models.interview_question import InterviewQuestion
    from app.models.interview_report import InterviewReport
    from app.models.interview_resume_link import InterviewResumeLink

user_id_type = BigInteger().with_variant(Integer, "sqlite")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[int] = mapped_column(
        user_id_type,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    interview_type: Mapped[str] = mapped_column(String(30), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_question_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "interview_questions.id",
            name="fk_interview_sessions_current_question_id",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    use_active_resume: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="CREATED", nullable=False)
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

    user = relationship("User", back_populates="interview_sessions")
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        foreign_keys="InterviewQuestion.session_id",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="InterviewQuestion.sequence",
    )
    current_question: Mapped["InterviewQuestion | None"] = relationship(
        foreign_keys=[current_question_id],
        post_update=True,
    )
    report: Mapped["InterviewReport | None"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        uselist=False,
    )
    knowledge_base_links: Mapped[list["InterviewKnowledgeBaseLink"]] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    resume_link: Mapped["InterviewResumeLink | None"] = relationship(
        back_populates="interview",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def knowledge_bases(self) -> list:
        return [
            link.knowledge_base
            for link in self.knowledge_base_links
            if getattr(link, "knowledge_base", None) is not None
        ]

    @property
    def resume(self) -> dict | None:
        if self.resume_link is None:
            return None
        return {
            "resume_id": self.resume_link.resume_id,
            "resume_title": self.resume_link.resume_title_snapshot,
            "used_context": True,
        }
