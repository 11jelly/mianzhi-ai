from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewResumeLink(Base):
    __tablename__ = "interview_resume_links"

    interview_session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id"),
        primary_key=True,
    )
    resume_id: Mapped[str | None] = mapped_column(
        ForeignKey("user_resumes.id"),
        nullable=True,
        index=True,
    )
    resume_title_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    resume_context_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    interview = relationship("InterviewSession", back_populates="resume_link")
    resume = relationship("UserResume")
