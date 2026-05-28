from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(OrmBase):
    created_at: datetime
    updated_at: datetime


class IDSchema(OrmBase):
    id: UUID


class PagedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int
    limit: int


class MessageResponse(BaseModel):
    detail: str
