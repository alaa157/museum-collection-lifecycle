"""audit foundation

Revision ID: 0001_audit
Revises:
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_audit"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer()),
        sa.Column("action", sa.String(150), nullable=False),
        sa.Column("entity_type", sa.String(150)),
        sa.Column("entity_id", sa.String(150)),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("correlation_id", sa.String(100)),
        sa.Column("old_state", sa.JSON()),
        sa.Column("new_state", sa.JSON()),
        sa.Column("event_payload", sa.JSON(), nullable=False),
    )

    op.create_index(
        "ix_audit_logs_user_id",
        "audit_logs",
        ["user_id"],
    )

    op.create_index(
        "ix_audit_logs_timestamp",
        "audit_logs",
        ["timestamp"],
    )


def downgrade():
    op.drop_index(
        "ix_audit_logs_timestamp",
        table_name="audit_logs",
    )
    op.drop_index(
        "ix_audit_logs_user_id",
        table_name="audit_logs",
    )
    op.drop_table("audit_logs")
