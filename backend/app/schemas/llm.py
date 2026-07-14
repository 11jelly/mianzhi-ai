from pydantic import BaseModel, Field, field_validator, model_validator


class GeneratedQuestion(BaseModel):
    sequence: int = Field(ge=1)
    category: str = Field(min_length=1, max_length=50)
    question_text: str = Field(min_length=1)
    expected_points: list[str] | None = None

    @field_validator("expected_points")
    @classmethod
    def remove_empty_points(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned = [item.strip() for item in value if item.strip()]
        return cleaned or None


class GeneratedQuestionSet(BaseModel):
    questions: list[GeneratedQuestion]


class FollowUpDecision(BaseModel):
    should_follow_up: bool
    follow_up_category: str | None = None
    follow_up_question: str | None = None
    reason_summary: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_follow_up_fields(self) -> "FollowUpDecision":
        if self.should_follow_up:
            if not self.follow_up_category or not self.follow_up_category.strip():
                raise ValueError("follow_up_category is required")
            if not self.follow_up_question or not self.follow_up_question.strip():
                raise ValueError("follow_up_question is required")
        return self
