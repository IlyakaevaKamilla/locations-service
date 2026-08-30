from __future__ import annotations

from typing import TypeVar

from app.db.models import Level, LocationActivity, LocationLevel, LocationStyle, Style
from app.schemas.admin import AdminLevelRead, AdminStyleRead

ModelT = TypeVar("ModelT", Style, Level)
JunctionT = TypeVar("JunctionT", LocationLevel, LocationStyle, LocationActivity)
AdminSchemaT = TypeVar("AdminSchemaT", AdminLevelRead, AdminStyleRead)
