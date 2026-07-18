import uuid

from pydantic import BaseModel, ConfigDict


class ProcedureBase(BaseModel):
    category: str
    name: str
    keywords: list[str] = []
    description: str
    documents: list[str] = []
    fee: str
    processing_time: str
    place_of_submission: str
    online_url: str
    legal_basis: str


class ProcedureCreate(ProcedureBase):
    code: str


class ProcedureUpdate(BaseModel):
    category: str | None = None
    name: str | None = None
    keywords: list[str] | None = None
    description: str | None = None
    documents: list[str] | None = None
    fee: str | None = None
    processing_time: str | None = None
    place_of_submission: str | None = None
    online_url: str | None = None
    legal_basis: str | None = None


class ProcedureOut(ProcedureBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
