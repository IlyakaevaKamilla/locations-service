from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.references import (
    admin_create_reference,
    admin_delete_reference,
    admin_update_reference,
    get_reference_by_id,
    is_name_unique,
    list_locations_by_reference,
    list_references,
)
from app.db.database import get_async_session
from app.db.models import (
    City,
    Country,
    Level,
    LocationLevel,
    LocationStyle,
    Region,
    Style,
)
from app.schemas.locations import LocationRead
from app.schemas.references import (
    ReferenceListResponse,
    ReferenceLocationsResponse,
    ReferenceRead,
)
from app.types import JunctionT, ModelT


class ReferenceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_reference_or_404(self, model: type[ModelT], item_id: int) -> ModelT:
        """Get reference by ID or raise 404."""
        reference = await get_reference_by_id(
            self.session, model=model, item_id=item_id
        )
        if reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} with id {item_id} not found",
            )
        return reference

    async def _ensure_name_unique(
        self, model: type[ModelT], name: str, exclude_id: int | None = None
    ) -> None:
        """Raise 400 if name already exists."""
        is_unique = await is_name_unique(
            self.session, model=model, name=name, exclude_id=exclude_id
        )
        if not is_unique:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{model.__name__} with name '{name}' already exists",
            )

    async def list_styles(
        self,
        *,
        name: str | None = None,
        style_id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Style, name=name, item_id=style_id, limit=limit, offset=offset
        )

    async def list_levels(
        self,
        *,
        name: str | None = None,
        list_id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Level, name=name, item_id=list_id, limit=limit, offset=offset
        )

    async def list_cities(
        self,
        *,
        name: str | None = None,
        city_id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=City, name=name, item_id=city_id, limit=limit, offset=offset
        )

    async def list_regions(
        self,
        *,
        name: str | None = None,
        region_id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Region, name=name, item_id=region_id, limit=limit, offset=offset
        )

    async def list_countries(
        self,
        *,
        name: str | None = None,
        country_id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Country, name=name, item_id=country_id, limit=limit, offset=offset
        )

    async def _list_references(
        self,
        model: type[ModelT],
        *,
        name: str | None = None,
        item_id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceListResponse:
        items, total = await list_references(
            self.session,
            model=model,
            name=name,
            id=item_id,
            limit=limit,
            offset=offset,
        )
        return ReferenceListResponse(
            items=[ReferenceRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def admin_create_style(
        self,
        name: str,
    ) -> ReferenceRead:
        return await self._create_reference(model=Style, name=name)

    async def admin_create_level(
        self,
        name: str,
    ) -> ReferenceRead:
        return await self._create_reference(model=Level, name=name)

    async def _create_reference(self, model: type[ModelT], name: str) -> ReferenceRead:
        await self._ensure_name_unique(model=model, name=name)
        item = await admin_create_reference(self.session, model=model, name=name)
        return ReferenceRead.model_validate(item)

    async def _ensure_parent_exists(
        self, model: type[ModelT], parent_id: int, parent_name: str
    ) -> None:
        """Raise 404 if the parent reference does not exist."""
        parent = await get_reference_by_id(self.session, model=model, item_id=parent_id)
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{parent_name} with id {parent_id} not found",
            )

    async def admin_create_country(self, name: str) -> ReferenceRead:
        await self._ensure_name_unique(model=Country, name=name)
        item = await admin_create_reference(self.session, model=Country, name=name)
        return ReferenceRead.model_validate(item)

    async def admin_create_region(self, name: str, country_id: int) -> ReferenceRead:
        """Create a region linked to a country."""
        await self._ensure_parent_exists(
            model=Country, parent_id=country_id, parent_name="Country"
        )
        await self._ensure_name_unique(model=Region, name=name)
        item = await admin_create_reference(
            self.session, model=Region, name=name, country_id=country_id
        )
        return ReferenceRead.model_validate(item)

    async def admin_create_city(self, name: str, region_id: int) -> ReferenceRead:
        """Create a city linked to a region."""
        await self._ensure_parent_exists(
            model=Region, parent_id=region_id, parent_name="Region"
        )
        await self._ensure_name_unique(model=City, name=name)
        item = await admin_create_reference(
            self.session, model=City, name=name, region_id=region_id
        )
        return ReferenceRead.model_validate(item)

    async def admin_update_style(self, item_id: int, name: str) -> ReferenceRead:
        return await self._update_reference(model=Style, item_id=item_id, name=name)

    async def admin_update_level(self, item_id: int, name: str) -> ReferenceRead:
        return await self._update_reference(model=Level, item_id=item_id, name=name)

    async def admin_update_city(
        self, item_id: int, name: str, region_id: int | None
    ) -> ReferenceRead:
        fields = {"name": name}
        if region_id is not None:
            await self._ensure_parent_exists(
                model=Region, parent_id=region_id, parent_name="Region"
            )
            fields["region_id"] = region_id
        return await self._update_reference(model=City, item_id=item_id, **fields)

    async def admin_update_region(
        self, item_id: int, name: str, country_id: int | None
    ) -> ReferenceRead:
        fields = {"name": name}
        if country_id is not None:
            await self._ensure_parent_exists(
                model=Country, parent_id=country_id, parent_name="Country"
            )
            fields["country_id"] = country_id
        return await self._update_reference(model=Region, item_id=item_id, **fields)

    async def admin_update_country(self, item_id: int, name: str) -> ReferenceRead:
        return await self._update_reference(model=Country, item_id=item_id, name=name)

    async def _update_reference(
        self, model: type[ModelT], item_id: int, **fields
    ) -> ReferenceRead:
        if "name" in fields:
            await self._ensure_name_unique(
                model=model, name=fields["name"], exclude_id=item_id
            )
        updated_item = await admin_update_reference(
            self.session, model=model, item_id=item_id, **fields
        )
        if updated_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} with id {item_id} not found",
            )
        return ReferenceRead.model_validate(updated_item)

    async def list_style_locations(
        self,
        style_id: int,
        *,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        return await self._list_reference_locations(
            model=Style,
            item_id=style_id,
            junction_model=LocationStyle,
            reference_field=LocationStyle.style_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

    async def list_level_locations(
        self,
        level_id: int,
        *,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        return await self._list_reference_locations(
            model=Level,
            item_id=level_id,
            junction_model=LocationLevel,
            reference_field=LocationLevel.level_id,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )

    async def _list_reference_locations(
        self,
        model: type[ModelT],
        item_id: int,
        junction_model: type[JunctionT],
        reference_field: Any,
        *,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        reference = await self._get_reference_or_404(model=model, item_id=item_id)
        locations, total = await list_locations_by_reference(
            self.session,
            item_id=item_id,
            junction_model=junction_model,
            reference_field=reference_field,
            is_active=is_active,
            limit=limit,
            offset=offset,
        )
        return ReferenceLocationsResponse(
            id=reference.id,
            name=reference.name,
            locations=[LocationRead.model_validate(loc) for loc in locations],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def admin_delete_style(self, style_id: int) -> None:
        await self._delete_reference(model=Style, item_id=style_id)

    async def admin_delete_level(self, level_id: int) -> None:
        await self._delete_reference(model=Level, item_id=level_id)

    async def admin_delete_city(self, city_id: int) -> None:
        await self._delete_reference(model=City, item_id=city_id)

    async def admin_delete_region(self, region_id: int) -> None:
        await self._delete_reference(model=Region, item_id=region_id)

    async def admin_delete_country(self, country_id: int) -> None:
        await self._delete_reference(model=Country, item_id=country_id)

    async def _delete_reference(self, model: type[ModelT], item_id: int) -> None:
        deleted = await admin_delete_reference(
            self.session, model=model, item_id=item_id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )


async def get_reference_service(
    session: AsyncSession = Depends(get_async_session),
) -> ReferenceService:
    return ReferenceService(session)
