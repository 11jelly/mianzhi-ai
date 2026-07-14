from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ResumeSourceType = Literal["UPLOAD", "PASTE"]
ResumeStatus = Literal["PROCESSING", "READY", "FAILED"]


class ResumePasteRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    resume_text: str = Field(min_length=1, max_length=200_000)
    activate: bool = True


class ResumeUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)


class ResumeRead(BaseModel):
    id: str
    title: str
    source_type: ResumeSourceType
    original_filename: str | None = None
    normalized_text: str | None = None
    content_hash: str
    status: ResumeStatus
    error_message: str | None = None
    is_active: bool
    extracted_text_length: int
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ResumeSummary(BaseModel):
    id: str
    title: str
    status: ResumeStatus
    is_active: bool
    extracted_text_length: int
    created_at: datetime


class InterviewResumeSummary(BaseModel):
    resume_id: str | None = None
    resume_title: str
    used_context: bool = True


class ResumeSearchItem(BaseModel):
    chunk_id: str
    resume_title: str
    content_preview: str
    score: float
