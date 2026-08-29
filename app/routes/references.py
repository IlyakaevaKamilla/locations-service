from fastapi import APIRouter

from app.routes.query_params import (
    LimitQuery,
    OffsetQuery,
    ReferenceIdQuery,
    ReferenceNameQuery,
    ReferenceServiceDep,
)
from app.schemas.references import ReferenceListResponse, ReferenceLocationsResponse

router = APIRouter(prefix="/api/references", tags=["references"])


@router.get("/styles", response_model=ReferenceListResponse)
async def read_styles(
    service: ReferenceServiceDep,
    name: ReferenceNameQuery = None,
    id: ReferenceIdQuery = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    return await service.list_styles(name=name, id=id, limit=limit, offset=offset)


@router.get("/levels", response_model=ReferenceListResponse)
async def read_levels(
    service: ReferenceServiceDep,
    name: ReferenceNameQuery = None,
    id: ReferenceIdQuery = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    return await service.list_levels(name=name, id=id, limit=limit, offset=offset)


@router.get("/styles/{style_id}/locations", response_model=ReferenceLocationsResponse)
async def read_style_locations(
    style_id: int,
    service: ReferenceServiceDep,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    """Return a paginated list of active locations linked to a style."""
    return await service.list_style_locations(style_id, limit=limit, offset=offset)


@router.get("/levels/{level_id}/locations", response_model=ReferenceLocationsResponse)
async def read_level_locations(
    level_id: int,
    service: ReferenceServiceDep,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    """Return a paginated list of active locations linked to a level."""
    return await service.list_level_locations(level_id, limit=limit, offset=offset)
