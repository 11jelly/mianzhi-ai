from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.evaluation import EvaluationRead
from app.schemas.interview_question import InterviewQuestionRead


class AnswerSubmitRequest(BaseModel):
    question_id: str
    answer_text: str = Field(min_length=20, max_length=5000)
    recording_duration_seconds: float | None = Field(default=None, ge=0, le=300)

    @field_validator("answer_text")
    @classmethod
    def strip_answer_text(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 20:
            raise ValueError("answer_text must be at least 20 characters after trimming")
        return stripped


class AnswerRead(BaseModel):
    id: str
    session_id: str
    question_id: str
    answer_text: str
    recording_duration_seconds: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerSubmitResponse(BaseModel):
    answer: AnswerRead
    evaluation: EvaluationRead
    session_status: str
    answered_question_count: int
    question_count: int
    next_question: InterviewQuestionRead | None
    agent_action: str | None = None
    agent_reason_summary: str | None = None


class AnswerHistoryItem(BaseModel):
    question_id: str
    sequence: int
    category: str
    question_text: str
    question_type: str = "PRIMARY"
    parent_question_id: str | None = None
    answer_text: str
    recording_duration_seconds: float | None = None
    evaluation: EvaluationRead
    created_at: datetime
