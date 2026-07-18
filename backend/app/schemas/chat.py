import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer_html: str
    source: str
    matched: bool
    matched_source_type: str


class ChatHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question: str
    answer: str
    matched_source_type: str
    created_at: datetime
