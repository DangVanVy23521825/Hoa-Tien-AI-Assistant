import uuid
from datetime import datetime

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.session import Base


class Contact(Base):
    """Bảng single-row: thông tin liên hệ UBND + thông tin chung xã."""

    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    office: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    portal_url: Mapped[str] = mapped_column(String(500), nullable=False)
    public_service_url: Mapped[str] = mapped_column(String(500), nullable=False)
    working_hours: Mapped[dict] = mapped_column(JSON, default=dict)
    commune_info: Mapped[dict] = mapped_column(JSON, default=dict)  # tên, diện tích, dân số, note lịch sử
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
