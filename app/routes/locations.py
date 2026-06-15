from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from pydantic import BeforeValidator

from app.dependencies.auth import get_current_user_id, get_optional_current_user_id
from app.schemas.locations import (
    FavoriteStateResponse,
    LocationFilterOptions,
    LocationListResponse,
    LocationRead,
)
from app.services.locations import LocationService, get_location_service

router = APIRouter(prefix="/api/locations", tags=["locations"])
MAX_INT32 = 2_147_483_647


def _split_query_values(values: list[str] | None, *, max_length: int | None = None) -> list[str] | None:
    """Normalize repeated and comma-separated query values into one validated list."""
    if not values:
        return None

    result: list[str] = []
    for value in values:
        for part in value.split(","):
            normalized = part.strip()
            if not normalized:
                continue
            if max_length is not None and len(normalized) > max_length:
                raise HTTPException(
                    status_code=422,
                    detail=f"filter value must contain at most {max_length} characters",
                )
            result.append(normalized)
    return result or None


def _parse_activity_ids(values: Any) -> list[int] | None:
    """Parse repeated and comma-separated activity ids from query parameters."""
    if values is not None and not isinstance(values, list):
        values = [values]

    raw_values = _split_query_values([str(value) for value in values] if values is not None else None)
    if raw_values is None:
        return None

    activity_ids: list[int] = []
    for value in raw_values:
        try:
            activity_id = int(value)
        except ValueError as exc:
            raise ValueError("activity_id must be an integer") from exc
        if activity_id < 1:
            raise ValueError("activity_id must be greater than or equal to 1")
        if activity_id > MAX_INT32:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
        activity_ids.append(activity_id)
    return activity_ids


def _parse_location_id(location_id: Annotated[str, Path()]) -> int:
    try:
        parsed_location_id = int(location_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="location_id must be an integer",
        ) from exc
    if parsed_location_id < 1 or parsed_location_id > MAX_INT32:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return parsed_location_id


ActivityIdQuery = Annotated[
    list[int] | None,
    BeforeValidator(_parse_activity_ids),
    Query(description="Activity ids. Supports repeated values and CSV, e.g. activity_id=1&activity_id=2 or 1,2."),
]
LocationIdPath = Annotated[int, Depends(_parse_location_id)]
SearchQuery = Annotated[str | None, Query(max_length=255)]
StringListQuery = Annotated[list[str] | None, Query()]
LimitQuery = Annotated[int, Query(ge=1, le=100)]
OffsetQuery = Annotated[int, Query(ge=0)]
OptionalUserId = Annotated[int | None, Depends(get_optional_current_user_id)]
CurrentUserId = Annotated[int, Depends(get_current_user_id)]
LocationServiceDep = Annotated[LocationService, Depends(get_location_service)]


@router.get("", response_model=LocationListResponse)
async def read_locations(
    user_id: OptionalUserId,
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
    return await service.list_locations(
        search=search,
        region=_split_query_values(region, max_length=255),
        city=_split_query_values(city, max_length=255),
        country=_split_query_values(country, max_length=120),
        activity_id=activity_id,
        styles=_split_query_values(styles, max_length=120),
        levels=_split_query_values(levels, max_length=120),
        limit=limit,
        offset=offset,
        user_id=user_id,
    )


@router.get("/filters", response_model=LocationFilterOptions)
async def read_location_filters(
    service: LocationServiceDep,
):
    return await service.list_filter_options()


@router.get("/favorites", response_model=LocationListResponse)
async def read_favorite_locations(
    user_id: CurrentUserId,
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
    is_active: bool | None = True,
):
    """Return current user's favorite locations using the same filters as the public list."""
    return await service.list_favorites(
        user_id=user_id,
        search=search,
        region=_split_query_values(region, max_length=255),
        city=_split_query_values(city, max_length=255),
        country=_split_query_values(country, max_length=120),
        activity_id=activity_id,
        styles=_split_query_values(styles, max_length=120),
        levels=_split_query_values(levels, max_length=120),
        is_active=is_active,
        limit=limit,
        offset=offset,
    )


@router.get("/{location_id}", response_model=LocationRead)
async def read_location(
    location_id: LocationIdPath,
    user_id: OptionalUserId,
    service: LocationServiceDep,
):
    return await service.get_location(location_id, user_id=user_id)


@router.post("/{location_id}/favorite", response_model=FavoriteStateResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite_location(
    location_id: LocationIdPath,
    user_id: CurrentUserId,
    service: LocationServiceDep,
):
    return await service.add_favorite(location_id, user_id)


@router.delete("/{location_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite_location(
    location_id: LocationIdPath,
    user_id: CurrentUserId,
    service: LocationServiceDep,
):
    await service.remove_favorite(location_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
