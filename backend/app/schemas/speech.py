from pydantic import BaseModel, Field


class AsrTranscriptionResult(BaseModel):
    text: str = Field(min_length=1)
    model: str
    duration_seconds: float | None = None
