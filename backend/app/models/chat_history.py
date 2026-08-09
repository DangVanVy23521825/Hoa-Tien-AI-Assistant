import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Khách chưa đăng nhập: UUID do trình duyệt sinh, dùng để đếm hạn mức hỏi thử.
    # Câu xã giao lưu với guest_id = NULL để không trừ lượt của khách.
    guest_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    matched_source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    matched_source_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 👍👎 của người dùng trên câu trả lời — null = chưa đánh giá
    feedback_helpful: Mapped[bool | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="chat_history")  # noqa: F821
