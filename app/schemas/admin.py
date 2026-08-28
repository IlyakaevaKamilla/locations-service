from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.locations import LocationBase
from app.schemas.references import ReferenceBase, ReferenceRead


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


class AdminReferenceCreate(ReferenceBase):
    pass


class AdminStyleRead(ReferenceRead):
    pass


class AdminLevelRead(ReferenceRead):
    pass


class AdminStyleCreate(AdminReferenceCreate):
    pass


class AdminLevelCreate(AdminReferenceCreate):
    pass
