from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.knowledge_base import KnowledgeBaseSummary
from app.schemas.resume import InterviewResumeSummary

Difficulty = Literal["junior", "intermediate", "senior"]
InterviewType = Literal["technical", "project", "comprehensive", "product"]
QuestionCount = Literal[3, 5, 8]


class InterviewCreateRequest(BaseModel):
    target_role: str = Field(min_length=1, max_length=100)
    difficulty: Difficulty
    interview_type: InterviewType
    question_count: QuestionCount
    knowledge_base_ids: list[str] = Field(default_factory=list)
    use_active_resume: bool = True


class InterviewSessionRead(BaseModel):
    id: str
    target_role: str
    difficulty: Difficulty
    interview_type: InterviewType
    question_count: int
    current_question_index: int
    current_question_id: str | None = None
    follow_up_count: int = 0
    status: Literal["CREATED", "IN_PROGRESS", "READY_FOR_REPORT", "COMPLETED"]
    knowledge_bases: list[KnowledgeBaseSummary] = Field(default_factory=list)
    use_active_resume: bool = True
    resume: InterviewResumeSummary | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
