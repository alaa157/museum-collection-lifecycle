
"""store collection status before conservation

Revision ID: 0004_movement_request_fk
Revises: 0003_outbox
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_movement_request_fk"
down_revision = "0003_outbox"
branch_labels = None
depends_on = None

def upgrade():
    op.drop_constraint(
        "movements_movement_request_id_fkey",  # confirm name in DB
        "movements",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "movements_movement_request_id_fkey",
        "movements",
        "movement_requests",
        ["movement_request_id"],
        ["id"],
        ondelete="RESTRICT",
    )

def downgrade():
    op.drop_constraint("movements_movement_request_id_fkey", "movements", type_="foreignkey")
    op.create_foreign_key(
        "movements_movement_request_id_fkey",
        "movements",
        "movement_requests",
        ["movement_request_id"],
        ["id"],
        ondelete="SET NULL",
    )