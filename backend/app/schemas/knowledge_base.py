from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class KnowledgeBaseSummary(BaseModel):
    id: str
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class KnowledgeBaseRead(KnowledgeBaseSummary):
    document_count: int = 0
    chunk_count: int = 0
    status: str = "EMPTY"
    created_at: datetime
    updated_at: datetime


class KnowledgeDocumentRead(BaseModel):
    id: str
    knowledge_base_id: str
    original_filename: str
    file_type: str
    content_hash: str
    extracted_text_length: int
    status: str
    error_message: str | None = None
    chunk_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class KnowledgeSearchItem(BaseModel):
    chunk_id: str
    document_name: str
    content_preview: str
    score: float


class KnowledgeSearchResponse(BaseModel):
    items: list[KnowledgeSearchItem]


class RagSource(BaseModel):
    knowledge_base_id: str
    knowledge_base_name: str
    document_name: str
    content_preview: str
    score: float
