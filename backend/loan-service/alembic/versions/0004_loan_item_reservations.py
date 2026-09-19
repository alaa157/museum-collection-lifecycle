"""loan item reservations

Revision ID: 0004_loan_item_reservations
Revises: 0003_local_fks
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_loan_item_reservations"
down_revision = "0003_local_fks"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "loan_item_reservations",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "collection_item_id",
            sa.String(36),
            nullable=False,
        ),
        sa.Column(
            "loan_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "collection_item_id",
            name="uq_loan_item_reservation",
        ),
    )

    op.create_index(
        "ix_loan_item_reservations_collection_item_id",
        "loan_item_reservations",
        ["collection_item_id"],
    )

    op.create_index(
        "ix_loan_item_reservations_loan_id",
        "loan_item_reservations",
        ["loan_id"],
    )


def downgrade():
    op.drop_index(
        "ix_loan_item_reservations_loan_id",
        table_name="loan_item_reservations",
    )

    op.drop_index(
        "ix_loan_item_reservations_collection_item_id",
        table_name="loan_item_reservations",
    )

    op.drop_table("loan_item_reservations")