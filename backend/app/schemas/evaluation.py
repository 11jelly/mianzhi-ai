from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


class AnswerEvidenceItem(BaseModel):
    dimension: Literal["logic", "technical", "expression", "project_depth"]
    polarity: Literal["strength", "improvement"]
    quote: str
    reason: str
    suggestion: str | None = None


class ExpressionMetrics(BaseModel):
    character_count: int
    sentence_count: int
    average_sentence_length: float | None = None
    filler_word_count: int
    filler_word_rate: float
    repetition_hint: str | None = None
    structure_signal_count: int
    estimated_speech_rate: float | None = None
    speech_rate_unit: str | None = None
    speech_rate_status: str
    speech_rate_note: str


class EvaluationResult(BaseModel):
    total_score: int = Field(ge=0, le=100)
    logic_score: int = Field(ge=0, le=25)
    technical_score: int = Field(ge=0, le=30)
    expression_score: int = Field(ge=0, le=20)
    project_depth_score: int = Field(ge=0, le=25)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(min_length=1)
    improvement_suggestion: str = Field(min_length=1)
    detailed_feedback: str = Field(min_length=1)
    evidence_items: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("strengths", "weaknesses")
    @classmethod
    def clean_string_list(cls, value: list[str], info: ValidationInfo) -> list[str]:
        cleaned = [item.strip() for item in value if item.strip()]
        if info.field_name == "weaknesses" and not cleaned:
            raise ValueError("list must contain non-empty strings")
        return cleaned

    @model_validator(mode="after")
    def validate_total_score(self) -> "EvaluationResult":
        total = (
            self.logic_score
            + self.technical_score
            + self.expression_score
            + self.project_depth_score
        )
        if self.total_score != total:
            raise ValueError("total_score must equal the sum of dimension scores")
        return self


class EvaluationRead(EvaluationResult):
    id: str
    answer_id: str
    created_at: datetime
    evidence_items: list[AnswerEvidenceItem] = Field(default_factory=list)
    expression_metrics: ExpressionMetrics | None = None

    model_config = ConfigDict(from_attributes=True)
