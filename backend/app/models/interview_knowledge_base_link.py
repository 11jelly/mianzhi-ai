from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class InterviewKnowledgeBaseLink(Base):
    __tablename__ = "interview_knowledge_base_links"
    __table_args__ = (
        UniqueConstraint(
            "interview_session_id",
            "knowledge_base_id",
            name="uq_interview_knowledge_base_links",
        ),
    )

    interview_session_id: Mapped[str] = mapped_column(
        ForeignKey("interview_sessions.id"),
        primary_key=True,
    )
    knowledge_base_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_bases.id"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    interview = relationship("InterviewSession", back_populates="knowledge_base_links")
    knowledge_base = relationship("KnowledgeBase", back_populates="interview_links")
