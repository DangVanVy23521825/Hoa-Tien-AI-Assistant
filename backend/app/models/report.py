import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base

# Lĩnh vực phản ánh. Chuỗi cố định, Pydantic chặn giá trị lạ ở tầng schema.
# Nhãn tiếng Việt nằm ở frontend — đổi chữ hiển thị không cần migration.
REPORT_CATEGORIES = ("ha_tang", "moi_truong", "an_ninh", "thu_tuc", "khac")


class Report(Base):
    """Một phiếu phản ánh/kiến nghị của người dân.

    DB là nguồn sự thật: bản ghi được lưu TRƯỚC khi gửi mail, nên mail hỏng cũng
    không làm mất phản ánh.
    """

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Số thứ tự do Postgres cấp — dùng sinh mã phiếu người dân đọc được.
    # Dùng sequence thay vì COUNT(*)+1 để hai người gửi cùng lúc không ra trùng mã.
    # Phải là Identity() chứ không phải autoincrement=True: autoincrement chỉ có
    # tác dụng trên khoá chính, cột thường sẽ ra INTEGER trần và INSERT sẽ lỗi NOT NULL.
    seq: Mapped[int] = mapped_column(Integer, Identity(), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # timezone=True khai báo rõ: hạn mức 24h so sánh cột này với một datetime aware
    # (`datetime.now(timezone.utc)`), để cột naive thì Postgres phải tự ép kiểu theo
    # múi giờ phiên — sai âm thầm tuỳ cấu hình server.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["User"] = relationship()  # noqa: F821

    @property
    def code(self) -> str:
        """Mã phiếu hiển thị cho người dân, ví dụ "PA-0007"."""
        return f"PA-{self.seq:04d}"
