from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(OrmBase):
    created_at: datetime
    updated_at: datetime


class IDSchema(OrmBase):
    id: UUID


class PaginatedResponse(OrmBase):
    total: int
    page: int
    page_size: int
    results: list


class MessageResponse(BaseModel):
    detail: str
