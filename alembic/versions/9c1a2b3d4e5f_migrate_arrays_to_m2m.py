"""Migrate location arrays to m2m junction tables.

Revision ID: 9c1a2b3d4e5f
Revises: 8b7c9d2e4f10
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "9c1a2b3d4e5f"
down_revision: Union[str, Sequence[str], None] = "8b7c9d2e4f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create junction tables, migrate data, drop array columns."""
    # Create junction tables
    op.create_table(
        "location_activities",
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("location_id", "activity_id"),
    )
    op.create_table(
        "location_styles",
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("style", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("location_id", "style"),
    )
    op.create_table(
        "location_levels",
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("location_id", "level"),
    )

    # Migrate data from array columns
    op.execute(
        """
        INSERT INTO location_activities (location_id, activity_id)
        SELECT id, unnest(activity_ids)
        FROM locations
        WHERE activity_ids IS NOT NULL AND cardinality(activity_ids) > 0
        """
    )
    op.execute(
        """
        INSERT INTO location_styles (location_id, style)
        SELECT id, unnest(styles)
        FROM locations
        WHERE styles IS NOT NULL AND cardinality(styles) > 0
        """
    )
    op.execute(
        """
        INSERT INTO location_levels (location_id, level)
        SELECT id, unnest(levels)
        FROM locations
        WHERE levels IS NOT NULL AND cardinality(levels) > 0
        """
    )

    # Drop GIN indexes
    op.drop_index("ix_locations_activity_ids_gin", table_name="locations")
    op.drop_index("ix_locations_styles_gin", table_name="locations")
    op.drop_index("ix_locations_levels_gin", table_name="locations")

    # Drop array columns
    op.drop_column("locations", "activity_ids")
    op.drop_column("locations", "styles")
    op.drop_column("locations", "levels")


def downgrade() -> None:
    """Re-add array columns, migrate data back, drop junction tables."""
    op.add_column(
        "locations",
        sa.Column("activity_ids", sa.ARRAY(sa.Integer()), server_default=sa.text("'{}'::integer[]"), nullable=False),
    )
    op.add_column(
        "locations",
        sa.Column("styles", sa.ARRAY(sa.String()), server_default=sa.text("'{}'::varchar[]"), nullable=False),
    )
    op.add_column(
        "locations",
        sa.Column("levels", sa.ARRAY(sa.String()), server_default=sa.text("'{}'::varchar[]"), nullable=False),
    )

    op.execute(
        """
        UPDATE locations l
        SET activity_ids = COALESCE(
            (SELECT array_agg(la.activity_id ORDER BY la.activity_id)
             FROM location_activities la WHERE la.location_id = l.id),
            '{}'::integer[]
        )
        """
    )
    op.execute(
        """
        UPDATE locations l
        SET styles = COALESCE(
            (SELECT array_agg(ls.style ORDER BY ls.style)
             FROM location_styles ls WHERE ls.location_id = l.id),
            '{}'::varchar[]
        )
        """
    )
    op.execute(
        """
        UPDATE locations l
        SET levels = COALESCE(
            (SELECT array_agg(ll.level ORDER BY ll.level)
             FROM location_levels ll WHERE ll.location_id = l.id),
            '{}'::varchar[]
        )
        """
    )

    op.create_index("ix_locations_activity_ids_gin", "locations", ["activity_ids"], unique=False, postgresql_using="gin")
    op.create_index("ix_locations_styles_gin", "locations", ["styles"], unique=False, postgresql_using="gin")
    op.create_index("ix_locations_levels_gin", "locations", ["levels"], unique=False, postgresql_using="gin")

    op.drop_table("location_levels")
    op.drop_table("location_styles")
    op.drop_table("location_activities")
