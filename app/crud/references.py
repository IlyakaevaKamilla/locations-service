from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Level, Style, Location, LocationLevel, LocationStyle
from sqlalchemy.orm import selectinload


async def get_reference_by_id(
    session: AsyncSession, model: type[Style] | type[Level], item_id: int
) -> Style | Level | None:
    result = await session.execute(select(model).where(model.id == item_id))
    return result.scalar_one_or_none()


async def get_reference_by_name(
    session: AsyncSession, model: type[Style] | type[Level], item_name: str
) -> Style | Level | None:
    result = await session.execute(select(model).where(model.name == item_name))
    return result.scalar_one_or_none()


async def list_references(
    session: AsyncSession,
    model: type[Style] | type[Level],
    *,
    search: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[Sequence[Style | Level], int]:
    """Return a paginated list of reference rows with optional filtering by name."""
    statement = select(model)
    if search:
        statement = statement.where(model.name.ilike(f"%{search.strip()}%"))

    total_statement = select(func.count()).select_from(statement.subquery())
    total = await session.scalar(total_statement)

    statement = statement.order_by(model.name).limit(limit).offset(offset)
    result = await session.execute(statement)
    return result.scalars().all(), int(total or 0)


async def admin_create_reference(
    session: AsyncSession,
    model: type[Style] | type[Level],
    name: str,
) -> Style | Level:
    item = model(name=name)
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def admin_delete_reference(
    session: AsyncSession, model: type[Style] | type[Level], item_id: int,
) -> bool:
    item = await get_reference_by_id(session, model, item_id)
    if item is None:
        return False

    await session.delete(item)
    await session.commit()
    return True


async def list_locations_by_reference(
    session: AsyncSession,
    model: type[Style] | type[Level],
    item_id: int,
    *,
    limit: int = 20,
    offset: int = 0,
) -> tuple[Sequence[Location], int]:
    """Return a paginated list of active locations linked to a reference row."""
    if model is Style:
        junction = LocationStyle
        reference_id = LocationStyle.style_id
    else:
        junction = LocationLevel
        reference_id = LocationLevel.level_id

    base_statement = (
        select(Location)
        .options(
            selectinload(Location.activities_rel),
            selectinload(Location.styles_rel),
            selectinload(Location.levels_rel),
        )
        .join(junction, junction.location_id == Location.id)
        .where(reference_id == item_id, Location.is_active.is_(True))
    )

    total_statement = select(func.count()).select_from(base_statement.subquery())
    total = await session.scalar(total_statement)

    statement = base_statement.order_by(Location.name).limit(limit).offset(offset)
    result = await session.execute(statement)
    return result.scalars().all(), int(total or 0)
