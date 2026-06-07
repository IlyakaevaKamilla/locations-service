from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(150), unique=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    region: Mapped[str] = mapped_column(String(255), index=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    country: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        server_default=text("'Russia'"),
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    distance_to_city_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activity_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=list,
        server_default=text("'{}'::integer[]"),
    )
    styles: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default=text("'{}'::varchar[]"),
    )
    levels: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        server_default=text("'{}'::varchar[]"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    favorites: Mapped[list["FavoriteLocation"]] = relationship(back_populates="location", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_locations_country_region_city", "country", "region", "city"),
        Index("ix_locations_region_lower", func.lower(region)),
        Index("ix_locations_city_lower", func.lower(city)),
        Index("ix_locations_country_lower", func.lower(country)),
        Index("ix_locations_activity_ids_gin", activity_ids, postgresql_using="gin"),
        Index("ix_locations_styles_gin", styles, postgresql_using="gin"),
        Index("ix_locations_levels_gin", levels, postgresql_using="gin"),
    )


class FavoriteLocation(Base):
    __tablename__ = "favorite_locations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    location: Mapped[Location] = relationship(back_populates="favorites")

    __table_args__ = (UniqueConstraint("user_id", "location_id", name="uq_favorite_locations_user_location"),)
