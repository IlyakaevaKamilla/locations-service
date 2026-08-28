from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.locations import LocationRead


class ReferenceBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)


class ReferenceRead(ReferenceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ReferenceListResponse(BaseModel):
    items: list[ReferenceRead]
    total: int
    limit: int
    offset: int


class ReferenceLocationsResponse(ReferenceRead):
    locations: list[LocationRead]
    total: int
    limit: int
    offset: int
