import uuid

from pydantic import BaseModel, ConfigDict


class KnowledgeArticleBase(BaseModel):
    category: str
    title: str
    keywords: list[str] = []
    content: str
    source_citation: str


class KnowledgeArticleCreate(KnowledgeArticleBase):
    pass


class KnowledgeArticleUpdate(BaseModel):
    category: str | None = None
    title: str | None = None
    keywords: list[str] | None = None
    content: str | None = None
    source_citation: str | None = None


class KnowledgeArticleOut(KnowledgeArticleBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
