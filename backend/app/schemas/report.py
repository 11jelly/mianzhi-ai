from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.evaluation import AnswerEvidenceItem, ExpressionMetrics


class ImprovementPlanItem(BaseModel):
    priority: int = Field(ge=1, le=10)
    topic: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    actions: list[str] = Field(min_length=1)
    expected_outcome: str = Field(min_length=1)

    @field_validator("actions")
    @classmethod
    def clean_actions(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("actions must contain non-empty strings")
        return cleaned


class ReportGenerationResult(BaseModel):
    summary: str = Field(min_length=1)
    strengths: list[str] = Field(min_length=1)
    weaknesses: list[str] = Field(min_length=1)
    role_gap_analysis: str = Field(min_length=1)
    improvement_plan: list[ImprovementPlanItem] = Field(min_length=1)
    next_practice_questions: list[str] = Field(min_length=1)

    @field_validator("strengths", "weaknesses", "next_practice_questions")
    @classmethod
    def clean_string_list(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if not cleaned:
            raise ValueError("list must contain non-empty strings")
        return cleaned


class InterviewReportRead(BaseModel):
    id: str
    session_id: str
    overall_score: int
    logic_score: int
    technical_score: int
    expression_score: int
    project_depth_score: int
    summary: str
    strengths: list[str]
    weaknesses: list[str]
    role_gap_analysis: str
    improvement_plan: list[dict[str, Any]]
    next_practice_questions: list[str]
    answer_evidence: list[dict[str, Any]] = Field(default_factory=list)
    expression_analysis: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AnswerEvidenceGroup(BaseModel):
    question_id: str
    sequence: int
    category: str
    question_text: str
    question_type: str
    parent_question_id: str | None = None
    answer_text: str
    evidence_items: list[AnswerEvidenceItem] = Field(default_factory=list)


class ExpressionAnalysisAnswerItem(BaseModel):
    question_id: str
    sequence: int
    question_text: str
    answer_text: str
    recording_duration_seconds: float | None = None
    metrics: ExpressionMetrics | None = None


class ExpressionAnalysisSummary(BaseModel):
    average_answer_length: float | None = None
    average_sentence_length: float | None = None
    total_filler_word_count: int | None = None
    total_structure_signal_count: int | None = None
    average_estimated_speech_rate: float | None = None
    speech_rate_unit: str | None = None
    sample_size: int
    speech_rate_sample_size: int


class ExpressionAnalysisReport(BaseModel):
    summary: ExpressionAnalysisSummary
    answers: list[ExpressionAnalysisAnswerItem] = Field(default_factory=list)
