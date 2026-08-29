from fastapi import APIRouter, status

from app.routes.query_params import (
    ActivityIdQuery,
    LimitQuery,
    LocationIdPath,
    LocationServiceDep,
    OffsetQuery,
    ReferenceServiceDep,
    SearchQuery,
    StringListQuery,
    _split_query_values,
)
from app.schemas.admin import (
    AdminLevelCreate,
    AdminLevelRead,
    AdminLocationCreate,
    AdminLocationListResponse,
    AdminLocationRead,
    AdminStyleCreate,
    AdminStyleRead,
)
from app.schemas.locations import LocationFilterOptions

router = APIRouter(prefix="/api/admin/locations", tags=["Admin Locations"])


@router.get("/", response_model=AdminLocationListResponse)
async def get_list_locations(
    service: LocationServiceDep,
    search: SearchQuery = None,
    region: StringListQuery = None,
    city: StringListQuery = None,
    country: StringListQuery = None,
    activity_id: ActivityIdQuery = None,
    styles: StringListQuery = None,
    levels: StringListQuery = None,
    limit: LimitQuery = 20,
    offset: OffsetQuery = 0,
):
    """Return locations using multi-value filters with OR inside each field."""
    return await service.list_all_locations(
        search=search,
        region=_split_query_values(region, max_length=255),
        city=_split_query_values(city, max_length=255),
        country=_split_query_values(country, max_length=120),
        activity_id=activity_id,
        styles=_split_query_values(styles, max_length=120),
        levels=_split_query_values(levels, max_length=120),
        limit=limit,
        offset=offset,
    )


@router.get("/filters", response_model=LocationFilterOptions)
async def read_location_filters(
    service: LocationServiceDep,
):
    return await service.list_filter_options()


@router.get("/{location_id}", response_model=AdminLocationRead)
async def read_location(
    location_id: LocationIdPath,
    service: LocationServiceDep,
):
    return await service.get_location_for_admin(location_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AdminLocationRead)
async def create_location(
    service: LocationServiceDep, location_data: AdminLocationCreate
) -> AdminLocationRead:
    return await service.admin_create_location(location_data)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location_by_id(service: LocationServiceDep, location_id: int):
    await service.admin_delete_location(location_id)


admin_references_router = APIRouter(
    prefix="/api/admin/references", tags=["Admin References"]
)


@admin_references_router.post(
    "/styles", status_code=status.HTTP_201_CREATED
)
async def create_style(
    service: ReferenceServiceDep, style_data: AdminStyleCreate
) -> AdminStyleRead:
    return await service.admin_create_style(style_data.name)


@admin_references_router.post(
    "/levels", status_code=status.HTTP_201_CREATED
)
async def create_levels(
    service: ReferenceServiceDep, level_data: AdminLevelCreate
) -> AdminLevelRead:
    return await service.admin_create_level(level_data.name)


@admin_references_router.delete(
    "/styles/{style_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_style_by_id(service: ReferenceServiceDep, style_id: int):
    await service.admin_delete_style(style_id)


@admin_references_router.delete(
    "/levels/{level_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_level_by_id(service: ReferenceServiceDep, level_id: int):
    await service.admin_delete_level(level_id)

# Нужен еще функционал патчить справочники
