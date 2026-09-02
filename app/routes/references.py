from fastapi import APIRouter

from app.routes.query_params import (
    LimitQuery,
    OffsetQuery,
    ReferenceIdQuery,
    ReferenceNameQuery,
    ReferenceServiceDep,
)
from app.schemas.references import ReferenceListResponse

router = APIRouter(prefix="/api/references", tags=["references"])


@router.get("/styles", response_model=ReferenceListResponse)
async def read_styles(
    service: ReferenceServiceDep,
    name: ReferenceNameQuery = None,
    id: ReferenceIdQuery = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    return await service.list_styles(name=name, style_id=id, limit=limit, offset=offset)


@router.get("/levels", response_model=ReferenceListResponse)
async def read_levels(
    service: ReferenceServiceDep,
    name: ReferenceNameQuery = None,
    id: ReferenceIdQuery = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    return await service.list_levels(name=name, list_id=id, limit=limit, offset=offset)
