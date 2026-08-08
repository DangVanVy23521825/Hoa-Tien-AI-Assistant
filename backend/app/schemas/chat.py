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
    # Chỉ có khi matched thủ tục — frontend dùng để sinh QR nộp hồ sơ trực tuyến
    online_url: str | None = None
    # Frontend dùng message_id để gửi feedback 👍👎, matched_source_id (code thủ tục) để in checklist
    message_id: uuid.UUID | None = None
    matched_source_id: str | None = None


class FeedbackRequest(BaseModel):
    message_id: uuid.UUID
    helpful: bool


class PublicStatsOut(BaseModel):
    total_answered: int
    top_questions: list[str]


class TopProcedureOut(BaseModel):
    name: str
    count: int


class UnmatchedQuestionOut(BaseModel):
    question: str
    created_at: datetime


class AdminStatsOut(BaseModel):
    total: int
    matched: int
    unmatched: int
    smalltalk: int = 0
    helpful: int
    unhelpful: int
    top_procedures: list[TopProcedureOut]
    recent_unmatched: list[UnmatchedQuestionOut]


class ChatHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question: str
    answer: str
    matched_source_type: str
    created_at: datetime
