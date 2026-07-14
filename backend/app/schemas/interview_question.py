from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class InterviewQuestionRead(BaseModel):
    id: str
    session_id: str
    sequence: int
    category: str
    question_text: str
    question_type: str = "PRIMARY"
    parent_question_id: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewStartResponse(BaseModel):
    session_id: str
    status: Literal["IN_PROGRESS"]
    question_count: int
    current_question_index: int = Field(ge=0)
    current_question: InterviewQuestionRead
