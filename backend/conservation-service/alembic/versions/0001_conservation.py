"""conservation foundation

Revision ID: 0001_conservation
Revises:
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_conservation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "condition_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collection_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("condition_score", sa.Float(), nullable=False),
        sa.Column("observed_damage", sa.Text()),
        sa.Column("environmental_concerns", sa.Text()),
        sa.Column("recommendations", sa.Text()),
        sa.Column("inspector_id", sa.Integer(), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("attachments", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index(
        "ix_condition_reports_item",
        "condition_reports",
        ["collection_item_id"],
    )

    op.create_table(
        "conservation_treatments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("collection_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("treatment_type", sa.String(255), nullable=False),
        sa.Column("conservator_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("materials_used", sa.JSON()),
        sa.Column("methodology", sa.Text()),
        sa.Column("before_after_documentation", sa.JSON()),
        sa.Column("result", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index(
        "ix_conservation_treatments_item",
        "conservation_treatments",
        ["collection_item_id"],
    )

    op.create_index(
        "ix_conservation_treatments_status",
        "conservation_treatments",
        ["status"],
    )

    op.create_table(
        "environmental_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("storage_area_id", sa.Integer(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature", sa.Float()),
        sa.Column("relative_humidity", sa.Float()),
        sa.Column("light_level", sa.Float()),
        sa.Column("source", sa.String(100), nullable=False),
    )

    op.create_index(
        "ix_environmental_observations_storage_area",
        "environmental_observations",
        ["storage_area_id"],
    )


def downgrade():
    op.drop_index(
        "ix_environmental_observations_storage_area",
        table_name="environmental_observations",
    )
    op.drop_table("environmental_observations")

    op.drop_index(
        "ix_conservation_treatments_status",
        table_name="conservation_treatments",
    )
    op.drop_index(
        "ix_conservation_treatments_item",
        table_name="conservation_treatments",
    )
    op.drop_table("conservation_treatments")

    op.drop_index(
        "ix_condition_reports_item",
        table_name="condition_reports",
    )
    op.drop_table("condition_reports")
