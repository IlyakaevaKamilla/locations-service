import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException

from app.db.models import Level, LocationLevel, LocationStyle, Style
from app.services.references import ReferenceService

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.crud.references import (
    admin_create_reference,
    admin_delete_reference,
    admin_update_reference,
    list_locations_by_reference,
    list_references,
)
from app.routes.admin import (
    admin_references_router,
    create_levels,
    create_style,
    delete_level_by_id,
    delete_style_by_id,
)
from app.routes.references import (
    read_level_locations,
    read_levels,
    read_style_locations,
    read_styles,
    router,
)
from tests.fakes import FakeSession, make_location, make_reference


def test_list_references_applies_search_and_pagination(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=1, name="mountain")

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [style]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(
        list_references(session, Style, name="mou", limit=10, offset=0)
    )

    assert items == [style]
    assert total == 1


def test_list_references_without_search_returns_all(monkeypatch):
    session = FakeSession()
    level = make_reference(Level, id=2, name="pro")

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [level]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(list_references(session, Level))

    assert items == [level]
    assert total == 1


def test_list_references_filters_by_single_id(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=5, name="mountain")

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [style]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(list_references(session, Style, id=5))

    assert items == [style]
    assert total == 1


def test_list_references_filters_by_id_list(monkeypatch):
    session = FakeSession()
    styles = [
        make_reference(Style, id=1, name="mountain"),
        make_reference(Style, id=2, name="sea"),
    ]

    async def fake_scalar(statement):
        return 2

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: styles))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(list_references(session, Style, id=[1, 2]))

    assert items == styles
    assert total == 2


def test_list_references_filters_by_name(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=1, name="mountain")

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [style]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(list_references(session, Style, name="mou"))

    assert items == [style]
    assert total == 1


def test_list_references_combines_name_and_id(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=1, name="mountain")

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [style]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(list_references(session, Style, name="mou", id=1))

    assert items == [style]
    assert total == 1


def test_list_references_empty_id_list_returns_all(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=1, name="mountain")

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [style]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    items, total = asyncio.run(list_references(session, Style, id=[]))

    assert items == [style]
    assert total == 1


def test_list_references_builds_where_for_name_and_id(monkeypatch):
    session = FakeSession()
    captured = {}

    async def fake_scalar(statement):
        captured["total_sql"] = str(statement.compile(dialect=None))
        return 1

    async def fake_execute(statement):
        captured["sql"] = str(statement.compile(dialect=None))
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=list))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    asyncio.run(list_references(session, Style, name="mou", id=[1, 2]))

    sql = captured["sql"]
    assert "styles.id IN" in sql
    assert "lower(styles.name) LIKE" in sql

    total_sql = captured["total_sql"]
    assert "styles.id IN" in total_sql
    assert "lower(styles.name) LIKE" in total_sql


def test_admin_create_reference_commits_and_refreshes(monkeypatch):
    session = FakeSession()

    monkeypatch.setattr(session, "add", lambda obj: None)
    monkeypatch.setattr(session, "commit", session.commit)

    async def fake_refresh(obj, attribute_names=None):
        return None

    monkeypatch.setattr(session, "refresh", fake_refresh)

    result = asyncio.run(admin_create_reference(session, Style, "mountain"))

    assert result is not None
    assert session.commits == 1


def test_admin_delete_reference_returns_true_when_deleted(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=1)

    async def fake_get_reference_by_id(db, model, item_id):
        assert db is session
        assert model is Style
        assert item_id == 1
        return style

    async def fake_delete(obj):
        return None

    monkeypatch.setattr(
        "app.crud.references.get_reference_by_id", fake_get_reference_by_id
    )
    monkeypatch.setattr(session, "delete", fake_delete)
    monkeypatch.setattr(session, "commit", session.commit)

    result = asyncio.run(admin_delete_reference(session, Style, 1))

    assert result is True
    assert session.commits == 1


def test_admin_delete_reference_returns_false_when_missing(monkeypatch):
    session = FakeSession()

    async def fake_get_reference_by_id(db, model, item_id):
        return None

    monkeypatch.setattr(
        "app.crud.references.get_reference_by_id", fake_get_reference_by_id
    )

    result = asyncio.run(admin_delete_reference(session, Style, 999))

    assert result is False
    assert session.commits == 0


def test_list_locations_by_reference_joins_style_junction(monkeypatch):
    session = FakeSession()
    location = make_location(id=1)

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [location]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    locations, total = asyncio.run(
        list_locations_by_reference(
            session, 1, LocationStyle, LocationStyle.style_id, limit=20, offset=0
        )
    )

    assert locations == [location]
    assert total == 1


def test_list_locations_by_reference_joins_level_junction(monkeypatch):
    session = FakeSession()
    location = make_location(id=1)

    async def fake_scalar(statement):
        return 1

    async def fake_execute(statement):
        return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [location]))

    monkeypatch.setattr(session, "scalar", fake_scalar)
    monkeypatch.setattr(session, "execute", fake_execute)

    locations, total = asyncio.run(
        list_locations_by_reference(
            session, 2, LocationLevel, LocationLevel.level_id, limit=20, offset=0
        )
    )

    assert locations == [location]
    assert total == 1


def test_list_styles_returns_reference_list_response(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)
    style = make_reference(Style, id=1, name="mountain")

    async def fake_list_references(db, model, **kwargs):
        assert db is session
        assert model is Style
        assert kwargs["name"] == "mou"
        assert kwargs["limit"] == 10
        assert kwargs["offset"] == 0
        return [style], 1

    monkeypatch.setattr("app.services.references.list_references", fake_list_references)

    result = asyncio.run(service.list_styles(name="mou", limit=10, offset=0))

    assert result.total == 1
    assert result.items[0].name == "mountain"


def test_list_levels_returns_reference_list_response(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)
    level = make_reference(Level, id=2, name="pro")

    async def fake_list_references(db, model, **kwargs):
        assert db is session
        assert model is Level
        return [level], 1

    monkeypatch.setattr("app.services.references.list_references", fake_list_references)

    result = asyncio.run(service.list_levels())

    assert result.total == 1
    assert result.items[0].name == "pro"


@pytest.mark.asyncio
async def test_create_reference_raises_400_on_duplicate(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)

    async def fake_is_name_unique(db, model, name, exclude_id=None):
        assert db is session
        assert model is Style
        assert name == "mountain"
        return False

    monkeypatch.setattr("app.services.references.is_name_unique", fake_is_name_unique)

    with pytest.raises(HTTPException) as exc_info:
        await service.admin_create_style("mountain")

    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail


def test_create_reference_returns_admin_read(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)
    style = make_reference(Style, id=1, name="mountain")

    async def fake_is_name_unique(db, model, name, exclude_id=None):
        assert db is session
        assert model is Style
        assert name == "mountain"
        return True

    async def fake_admin_create_reference(db, model, name):
        assert db is session
        assert model is Style
        assert name == "mountain"
        return style

    monkeypatch.setattr("app.services.references.is_name_unique", fake_is_name_unique)
    monkeypatch.setattr(
        "app.services.references.admin_create_reference", fake_admin_create_reference
    )

    result = asyncio.run(service.admin_create_style("mountain"))

    assert result.id == 1
    assert result.name == "mountain"


def test_admin_update_reference_commits_and_refreshes(monkeypatch):
    session = FakeSession()
    style = make_reference(Style, id=1, name="old")

    async def fake_get_reference_by_id(db, model, item_id):
        assert db is session
        assert model is Style
        assert item_id == 1
        return style

    async def fake_refresh(obj, attribute_names=None):
        return None

    monkeypatch.setattr(
        "app.crud.references.get_reference_by_id", fake_get_reference_by_id
    )
    monkeypatch.setattr(session, "commit", session.commit)
    monkeypatch.setattr(session, "refresh", fake_refresh)

    result = asyncio.run(admin_update_reference(session, Style, 1, name="new"))

    assert result is style
    assert style.name == "new"
    assert session.commits == 1


def test_admin_update_reference_returns_none_when_missing(monkeypatch):
    session = FakeSession()

    async def fake_get_reference_by_id(db, model, item_id):
        return None

    monkeypatch.setattr(
        "app.crud.references.get_reference_by_id", fake_get_reference_by_id
    )

    result = asyncio.run(admin_update_reference(session, Style, 999, name="new"))

    assert result is None
    assert session.commits == 0


@pytest.mark.asyncio
async def test_update_reference_raises_404_when_missing(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)

    async def fake_get_reference_by_id(db, model, item_id):
        return None

    async def fake_is_name_unique(db, model, name, exclude_id=None):
        return True

    monkeypatch.setattr(
        "app.crud.references.get_reference_by_id", fake_get_reference_by_id
    )
    monkeypatch.setattr("app.services.references.is_name_unique", fake_is_name_unique)

    with pytest.raises(HTTPException) as exc_info:
        await service.admin_update_style(item_id=999, name="new")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_reference_raises_400_on_duplicate_name(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)
    style = make_reference(Style, id=1, name="old")

    async def fake_get_reference_by_id(db, model, item_id):
        return style

    async def fake_is_name_unique(db, model, name, exclude_id=None):
        assert db is session
        assert model is Style
        assert name == "new"
        assert exclude_id == 1
        return False

    monkeypatch.setattr(
        "app.services.references.get_reference_by_id", fake_get_reference_by_id
    )
    monkeypatch.setattr("app.services.references.is_name_unique", fake_is_name_unique)

    with pytest.raises(HTTPException) as exc_info:
        await service.admin_update_style(item_id=1, name="new")

    assert exc_info.value.status_code == 400
    assert "already exists" in exc_info.value.detail


def test_update_reference_returns_admin_read(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)
    style = make_reference(Style, id=1, name="new")

    async def fake_get_reference_by_id(db, model, item_id):
        return style

    async def fake_is_name_unique(db, model, name, exclude_id=None):
        assert exclude_id == 1
        return True

    async def fake_admin_update_reference(db, model, item_id, **kwargs):
        assert db is session
        assert model is Style
        assert item_id == 1
        assert kwargs == {"name": "new"}
        return style

    monkeypatch.setattr(
        "app.services.references.get_reference_by_id", fake_get_reference_by_id
    )
    monkeypatch.setattr("app.services.references.is_name_unique", fake_is_name_unique)
    monkeypatch.setattr(
        "app.services.references.admin_update_reference", fake_admin_update_reference
    )

    result = asyncio.run(service.admin_update_style(item_id=1, name="new"))

    assert result.id == 1
    assert result.name == "new"


@pytest.mark.asyncio
async def test_delete_reference_raises_404_when_missing(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)

    async def fake_admin_delete_reference(db, model, item_id):
        return False

    monkeypatch.setattr(
        "app.services.references.admin_delete_reference", fake_admin_delete_reference
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.admin_delete_style(999)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_reference_locations_raises_404_when_reference_missing(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)

    async def fake_get_reference_by_id(db, model, item_id):
        return None

    monkeypatch.setattr(
        "app.services.references.get_reference_by_id", fake_get_reference_by_id
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.list_style_locations(999)

    assert exc_info.value.status_code == 404


def test_list_reference_locations_returns_id_name_and_locations(monkeypatch):
    session = FakeSession()
    service = ReferenceService(session)
    style = make_reference(Style, id=1, name="mountain")
    location = make_location(id=1)

    async def fake_get_reference_by_id(db, model, item_id):
        assert db is session
        assert model is Style
        assert item_id == 1
        return style

    async def fake_list_locations_by_reference(
        db, item_id, junction_model, reference_field, **kwargs
    ):
        assert db is session
        assert item_id == 1
        assert junction_model is LocationStyle
        assert reference_field is LocationStyle.style_id
        assert kwargs["limit"] == 20
        assert kwargs["offset"] == 0
        return [location], 1

    monkeypatch.setattr(
        "app.services.references.get_reference_by_id", fake_get_reference_by_id
    )
    monkeypatch.setattr(
        "app.services.references.list_locations_by_reference",
        fake_list_locations_by_reference,
    )

    result = asyncio.run(service.list_style_locations(1))

    assert result.id == 1
    assert result.name == "mountain"
    assert result.total == 1
    assert result.limit == 20
    assert result.offset == 0
    assert result.locations[0].id == 1


def test_read_styles_passes_query_params_to_service():
    service = SimpleNamespace()

    async def fake_list_styles(**kwargs):
        service.kwargs = kwargs
        return SimpleNamespace()

    service.list_styles = fake_list_styles

    asyncio.run(
        read_styles(
            service=service,
            name="mou",
            limit=10,
            offset=5,
        )
    )

    assert service.kwargs["name"] == "mou"
    assert service.kwargs["limit"] == 10
    assert service.kwargs["offset"] == 5


def test_read_levels_passes_query_params_to_service():
    service = SimpleNamespace()

    async def fake_list_levels(**kwargs):
        service.kwargs = kwargs
        return SimpleNamespace()

    service.list_levels = fake_list_levels

    asyncio.run(
        read_levels(
            service=service,
            name="pro",
            limit=10,
            offset=5,
        )
    )

    assert service.kwargs["name"] == "pro"
    assert service.kwargs["limit"] == 10
    assert service.kwargs["offset"] == 5


def test_read_style_locations_passes_params_to_service():
    service = SimpleNamespace()

    async def fake_list_style_locations(style_id, **kwargs):
        service.kwargs = {"style_id": style_id, **kwargs}
        return SimpleNamespace()

    service.list_style_locations = fake_list_style_locations

    asyncio.run(
        read_style_locations(
            style_id=1,
            service=service,
            limit=10,
            offset=5,
        )
    )

    assert service.kwargs["style_id"] == 1
    assert service.kwargs["limit"] == 10
    assert service.kwargs["offset"] == 5


def test_read_level_locations_passes_params_to_service():
    service = SimpleNamespace()

    async def fake_list_level_locations(level_id, **kwargs):
        service.kwargs = {"level_id": level_id, **kwargs}
        return SimpleNamespace()

    service.list_level_locations = fake_list_level_locations

    asyncio.run(
        read_level_locations(
            level_id=2,
            service=service,
            limit=10,
            offset=5,
        )
    )

    assert service.kwargs["level_id"] == 2
    assert service.kwargs["limit"] == 10
    assert service.kwargs["offset"] == 5


def test_admin_create_style_passes_name_to_service():
    service = SimpleNamespace()

    async def fake_admin_create_style(name):
        service.name = name
        return SimpleNamespace()

    service.admin_create_style = fake_admin_create_style
    style_data = SimpleNamespace(name="mountain")

    asyncio.run(create_style(service=service, style_data=style_data))

    assert service.name == "mountain"


def test_admin_create_levels_passes_name_to_service():
    service = SimpleNamespace()

    async def fake_admin_create_level(name):
        service.name = name
        return SimpleNamespace()

    service.admin_create_level = fake_admin_create_level
    level_data = SimpleNamespace(name="pro")

    asyncio.run(create_levels(service=service, level_data=level_data))

    assert service.name == "pro"


def test_admin_delete_style_passes_id_to_service():
    service = SimpleNamespace()

    async def fake_admin_delete_style(style_id):
        service.style_id = style_id

    service.admin_delete_style = fake_admin_delete_style

    asyncio.run(delete_style_by_id(service=service, style_id=1))

    assert service.style_id == 1


def test_admin_delete_level_passes_id_to_service():
    service = SimpleNamespace()

    async def fake_admin_delete_level(level_id):
        service.level_id = level_id

    service.admin_delete_level = fake_admin_delete_level

    asyncio.run(delete_level_by_id(service=service, level_id=2))

    assert service.level_id == 2


def test_references_openapi_exposes_public_and_admin_paths():
    app = FastAPI()
    app.include_router(router)
    app.include_router(admin_references_router)

    paths = app.openapi()["paths"]

    assert "/api/references/styles" in paths
    assert "/api/references/levels" in paths
    assert "/api/references/styles/{style_id}/locations" in paths
    assert "/api/references/levels/{level_id}/locations" in paths
    assert "/api/admin/references/styles" in paths
    assert "/api/admin/references/levels" in paths
    assert "/api/admin/references/styles/{style_id}" in paths
    assert "/api/admin/references/levels/{level_id}" in paths


def test_references_search_requires_min_three_characters():
    app = FastAPI()
    app.include_router(router)

    parameters = app.openapi()["paths"]["/api/references/styles"]["get"]["parameters"]
    search_schema = next(
        parameter["schema"] for parameter in parameters if parameter["name"] == "name"
    )

    assert search_schema["anyOf"][0]["minLength"] == 3
