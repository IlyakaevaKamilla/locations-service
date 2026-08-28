from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.references import (
    admin_create_reference,
    admin_delete_reference,
    get_reference_by_name,
    get_reference_by_id,
    list_references,
    list_locations_by_reference,
)
from app.db.database import get_async_session
from app.db.models import Level, Style
from app.schemas.references import (
    LevelRead,
    ReferenceListResponse,
    StyleRead,
    ReferenceLocationsResponse
)


class ReferenceService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_styles(
        self,
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Style, search=search, limit=limit, offset=offset
        )

    async def list_levels(
        self,
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        return await self._list_references(
            model=Level, search=search, limit=limit, offset=offset
        )

    async def _list_references(
        self,
        model: type[Style] | type[Level],
        *,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceListResponse:
        items, total = await list_references(
            self.session,
            model=model,
            search=search,
            limit=limit,
            offset=offset,
        )
        return ReferenceListResponse(
            items=items, total=total, limit=limit, offset=offset
        )

    async def admin_create_style(
        self, name: str,
    ) -> StyleRead:
        return await self._create_reference(model=Style, name=name)

    async def admin_create_level(
        self, name: str,
    ) -> LevelRead:
        return await self._create_reference(model=Level, name=name)

    async def _create_reference(
        self, model: type[Style] | type[Level], name: str
    ) -> StyleRead | LevelRead:
        existing = await get_reference_by_name(self.session, model=model, item_name=name)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{model.__name__} with that name already exists",
            )
        item = await admin_create_reference(self.session, model=model, name=name)
        return StyleRead.model_validate(item) if model is Style else LevelRead.model_validate(item)

    async def admin_delete_style(self, style_id: int) -> None:
        await self._delete_reference(model=Style, item_id=style_id)

    async def list_style_locations(
        self,
        style_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        return await self._list_reference_locations(
            model=Style, item_id=style_id, limit=limit, offset=offset
        )

    async def list_level_locations(
        self,
        level_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        return await self._list_reference_locations(
            model=Level, item_id=level_id, limit=limit, offset=offset
        )

    async def _list_reference_locations(
        self,
        model: type[Style] | type[Level],
        item_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> ReferenceLocationsResponse:
        reference = await get_reference_by_id(self.session, model=model, item_id=item_id)
        if reference is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )
        locations, total = await list_locations_by_reference(
            self.session,
            model=model,
            item_id=item_id,
            limit=limit,
            offset=offset,
        )
        return ReferenceLocationsResponse(
            id=reference.id,
            name=reference.name,
            locations=locations,
            total=total,
            limit=limit,
            offset=offset
        )

    async def admin_delete_level(self, level_id: int) -> None:
        await self._delete_reference(model=Level, item_id=level_id)

    async def _delete_reference(
        self, model: type[Style] | type[Level], item_id: int
    ) -> None:
        deleted = await admin_delete_reference(self.session, model=model, item_id=item_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{model.__name__} not found",
            )


async def get_reference_service(
    session: AsyncSession = Depends(get_async_session),
) -> ReferenceService:
    return ReferenceService(session)
