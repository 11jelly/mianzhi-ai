from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentEventRead(BaseModel):
    id: str
    session_id: str
    source_question_id: str
    event_type: str
    decision: str
    reason_summary: str | None
    follow_up_question_id: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
