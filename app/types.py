from __future__ import annotations

from typing import TypeVar

from app.db.models import Level, LocationActivity, LocationLevel, LocationStyle, Style
from app.schemas.admin import AdminLevelRead, AdminStyleRead

PossibleModels = Style | Level
PossibleJunctionModels = LocationLevel | LocationStyle | LocationActivity
PossibleAdminSchemas = AdminLevelRead | AdminStyleRead
ModelT = TypeVar("ModelT", bound=PossibleModels)
JunctionT = TypeVar("JunctionT", bound=PossibleJunctionModels)
AdminSchemaT = TypeVar("AdminSchemaT", bound=PossibleAdminSchemas)
