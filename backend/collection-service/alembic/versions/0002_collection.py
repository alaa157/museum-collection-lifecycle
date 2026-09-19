"""dimensions to jsonb

Revision ID: 0002_dimensions_jsonb
Revises: 0001_collection
Create Date: 2026-09-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_dimensions_jsonb"
down_revision = "0001_collection"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "collection_items",
        "dimensions",
        type_=postgresql.JSONB(),
        postgresql_using="dimensions::jsonb",
    )


def downgrade():
    op.alter_column(
        "collection_items",
        "dimensions",
        type_=sa.JSON(),
        postgresql_using="dimensions::json",
    )