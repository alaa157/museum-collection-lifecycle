"""loan and exhibition foundation

Revision ID: 0001_loans
Revises:
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_loans"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "loan_parties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("party_type", sa.String(50), nullable=False),
        sa.Column("contact_information", sa.JSON()),
    )

    op.create_table(
        "loans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("direction", sa.String(20), nullable=False),
        sa.Column("party_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("insurance_value", sa.Float()),
        sa.Column("agreement_document", sa.Text()),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index("ix_loans_status", "loans", ["status"])

    op.create_table(
        "loan_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loan_id", sa.Integer(), nullable=False),
        sa.Column("collection_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("condition_on_dispatch", sa.Text()),
        sa.Column("condition_on_return", sa.Text()),
        sa.Column("returned_at", sa.DateTime(timezone=True)),
    )

    op.create_index("ix_loan_items_loan", "loan_items", ["loan_id"])
    op.create_index(
        "ix_loan_items_collection_item",
        "loan_items",
        ["collection_item_id"],
    )

    op.create_table(
        "exhibitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("curator_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index(
        "ix_exhibitions_status",
        "exhibitions",
        ["status"],
    )

    op.create_table(
        "exhibition_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("exhibition_id", sa.Integer(), nullable=False),
        sa.Column("collection_item_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_label", sa.String(255)),
        sa.Column("display_order", sa.Integer(), nullable=False),
    )

    op.create_index(
        "ix_exhibition_items_exhibition",
        "exhibition_items",
        ["exhibition_id"],
    )

    op.create_index(
        "ix_exhibition_items_collection_item",
        "exhibition_items",
        ["collection_item_id"],
    )


def downgrade():
    op.drop_index(
        "ix_exhibition_items_collection_item",
        table_name="exhibition_items",
    )
    op.drop_index(
        "ix_exhibition_items_exhibition",
        table_name="exhibition_items",
    )
    op.drop_table("exhibition_items")

    op.drop_index(
        "ix_exhibitions_status",
        table_name="exhibitions",
    )
    op.drop_table("exhibitions")

    op.drop_index(
        "ix_loan_items_collection_item",
        table_name="loan_items",
    )
    op.drop_index(
        "ix_loan_items_loan",
        table_name="loan_items",
    )
    op.drop_table("loan_items")

    op.drop_index("ix_loans_status", table_name="loans")
    op.drop_table("loans")
    op.drop_table("loan_parties")
