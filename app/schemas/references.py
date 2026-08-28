from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.locations import LocationRead


class ReferenceBase(BaseModel):  # 1
    name: str = Field(min_length=1, max_length=150)


class ReferenceRead(ReferenceBase):  # 1
    model_config = ConfigDict(from_attributes=True)

    id: int


class ReferenceCreate(ReferenceBase):
    pass


class ReferenceListResponse(BaseModel):  # 1
    items: list[ReferenceRead]
    total: int
    limit: int
    offset: int


class ReferenceLocationsResponse(ReferenceRead):
    locations: list[LocationRead]
    total: int
    limit: int
    offset: int


class StyleRead(ReferenceRead):  # rename to admin
    pass


class LevelRead(ReferenceRead):  # rename to admin
    pass


class StyleCreate(ReferenceCreate):
    pass


class LevelCreate(ReferenceCreate):
    pass
