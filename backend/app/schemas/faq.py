import uuid

from pydantic import BaseModel, ConfigDict


class FaqBase(BaseModel):
    question: str
    keywords: list[str] = []
    answer: str


class FaqCreate(FaqBase):
    pass


class FaqUpdate(BaseModel):
    question: str | None = None
    keywords: list[str] | None = None
    answer: str | None = None


class FaqOut(FaqBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
