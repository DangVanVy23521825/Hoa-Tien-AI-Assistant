import uuid

from pydantic import BaseModel, ConfigDict


class ContactBase(BaseModel):
    office: str
    address: str
    phone: str
    portal_url: str
    public_service_url: str
    working_hours: dict
    commune_info: dict


class ContactUpdate(BaseModel):
    office: str | None = None
    address: str | None = None
    phone: str | None = None
    portal_url: str | None = None
    public_service_url: str | None = None
    working_hours: dict | None = None
    commune_info: dict | None = None


class ContactOut(ContactBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
