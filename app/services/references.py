from __future__ import annotations

from typing import Any, ClassVar

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
from app.db.models import Level, LocationLevel, LocationStyle, Style
from app.schemas.admin import AdminLevelRead, AdminStyleRead
from app.schemas.references import ReferenceListResponse, ReferenceLocationsResponse
from app.types import JunctionT, ModelT, PossibleAdminSchemas


class ReferenceService:
    _RESPONSE_MAP: ClassVar[dict[type[ModelT], type[PossibleAdminSchemas]]] = {
        Style: AdminStyleRead,
        Level: AdminLevelRead,
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_response(self, model: type[ModelT], item: ModelT):
        """Convert model to respose scheme."""
        response_cls = self._RESPONSE_MAP.get(model)
        if response_cls is None:
            raise ValueError(f"Unsupported model: {model.__name__}")
        return response_cls.model_validate(item)

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
        id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Style, name=name, id=id, limit=limit, offset=offset
        )

    async def list_levels(
        self,
        *,
        name: str | None = None,
        id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Level, name=name, id=id, limit=limit, offset=offset
        )

    async def _list_references(
        self,
        model: type[ModelT],
        *,
        name: str | None = None,
        id: int | list[int] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceListResponse:
        items, total = await list_references(
            self.session,
            model=model,
            name=name,
            id=id,
            limit=limit,
            offset=offset,
        )
        return ReferenceListResponse(
            items=items, total=total, limit=limit, offset=offset
        )

    async def admin_create_style(
        self,
        name: str,
    ) -> AdminStyleRead:
        return await self._create_reference(model=Style, name=name)

    async def admin_create_level(
        self,
        name: str,
    ) -> AdminLevelRead:
        return await self._create_reference(model=Level, name=name)

    async def _create_reference(
        self, model: type[ModelT], name: str
    ) -> PossibleAdminSchemas:
        await self._ensure_name_unique(model=model, name=name)
        item = await admin_create_reference(self.session, model=model, name=name)
        return self._to_response(model=model, item=item)

    async def admin_update_style(self, item_id: int, name: str) -> AdminStyleRead:
        return await self._update_reference(model=Style, item_id=item_id, name=name)

    async def admin_update_level(self, item_id: int, name: str) -> AdminLevelRead:
        return await self._update_reference(model=Level, item_id=item_id, name=name)

    async def _update_reference(
        self, model: type[ModelT], item_id: int, name: str
    ) -> PossibleAdminSchemas:
        await self._ensure_name_unique(model=model, name=name, exclude_id=item_id)
        updated_item = await admin_update_reference(
            self.session, model=model, item_id=item_id, name=name
        )
        if updated_item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} with id {item_id} not found",
            )
        return self._to_response(model=model, item=updated_item)

    async def list_style_locations(
        self,
        style_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        return await self._list_reference_locations(
            model=Style,
            item_id=style_id,
            junction_model=LocationStyle,
            reference_field=LocationStyle.style_id,
            limit=limit,
            offset=offset,
        )

    async def list_level_locations(
        self,
        level_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        return await self._list_reference_locations(
            model=Level,
            item_id=level_id,
            junction_model=LocationLevel,
            reference_field=LocationLevel.level_id,
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
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        reference = await self._get_reference_or_404(model=model, item_id=item_id)
        locations, total = await list_locations_by_reference(
            self.session,
            item_id=item_id,
            junction_model=junction_model,
            reference_field=reference_field,
            limit=limit,
            offset=offset,
        )
        return ReferenceLocationsResponse(
            id=reference.id,
            name=reference.name,
            locations=locations,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def admin_delete_style(self, style_id: int) -> None:
        await self._delete_reference(model=Style, item_id=style_id)

    async def admin_delete_level(self, level_id: int) -> None:
        await self._delete_reference(model=Level, item_id=level_id)

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
