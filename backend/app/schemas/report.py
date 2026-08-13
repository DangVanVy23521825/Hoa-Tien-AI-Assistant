import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

ReportCategory = Literal["ha_tang", "moi_truong", "an_ninh", "thu_tuc", "khac"]


class ReportCreate(BaseModel):
    category: ReportCategory
    content: str = Field(min_length=20, max_length=2000)
    location: str | None = Field(default=None, max_length=200)

    @field_validator("content", mode="before")
    @classmethod
    def _strip_content(cls, v: object) -> object:
        """Cắt khoảng trắng TRƯỚC khi kiểm độ dài — nếu không, 20 dấu cách lọt qua min_length."""
        return v.strip() if isinstance(v, str) else v

    @field_validator("location", mode="before")
    @classmethod
    def _strip_location(cls, v: object) -> object:
        """Ô địa điểm bỏ trống hoặc chỉ có khoảng trắng đều coi như không nhập."""
        if isinstance(v, str):
            return v.strip() or None
        return v


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    seq: int
    category: ReportCategory
    content: str
    location: str | None
    created_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def code(self) -> str:
        return f"PA-{self.seq:04d}"
