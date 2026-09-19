"""processed event inbox

Revision ID: 0006_processed_events
Revises: 0005_conservation_previous_status
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_processed_events"
down_revision = "0005_conservation_previous_status"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "processed_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False),
        sa.Column("consumer", sa.String(100), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "event_id",
            name="uq_processed_event_id",
        ),
    )

    op.create_index(
        "ix_processed_events_event_id",
        "processed_events",
        ["event_id"],
    )


def downgrade():
    op.drop_index(
        "ix_processed_events_event_id",
        table_name="processed_events",
    )

    op.drop_table("processed_events")