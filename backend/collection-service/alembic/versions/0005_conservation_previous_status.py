"""store collection status before conservation

Revision ID: 0005_conservation_previous_status
Revises: 0004_movement_request_fk
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_conservation_previous_status"
down_revision = "0004_movement_request_fk"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "collection_items",
        sa.Column(
            "previous_status",
            sa.String(50),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "collection_items",
        "previous_status",
    )