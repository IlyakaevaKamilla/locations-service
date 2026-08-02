from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.locations import LocationBase


class AdminLocationBase(LocationBase):
    pass


class AdminLocationRead(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AdminLocationCreate(AdminLocationBase):
    model_config = ConfigDict(from_attributes=True)


class AdminLocationListResponse(BaseModel):
    items: list[AdminLocationRead]
    total: int
    limit: int
    offset: int
