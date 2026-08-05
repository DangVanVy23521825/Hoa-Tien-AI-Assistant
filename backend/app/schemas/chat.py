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


class ChatHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    question: str
    answer: str
    matched_source_type: str
    created_at: datetime
