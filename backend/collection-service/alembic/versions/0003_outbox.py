"""event outbox

Revision ID: 0003_outbox
Revises: 0002_dimensions_jsonb
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_outbox"
down_revision = "0002_dimensions_jsonb"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(150), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("producer", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text()),
        sa.UniqueConstraint("event_id", name="uq_outbox_event_id"),
    )
    op.create_index(
        "ix_outbox_unpublished",
        "outbox_events",
        ["published_at", "id"],
    )


def downgrade():
    op.drop_index("ix_outbox_unpublished", table_name="outbox_events")
    op.drop_table("outbox_events")