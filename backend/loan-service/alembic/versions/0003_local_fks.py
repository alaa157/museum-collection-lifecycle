"""local foreign keys for loan domain

Revision ID: 0003_local_fks
Revises: 0002_loan_item_unique
Create Date: 2026-09-08
"""

from alembic import op

revision = "0003_local_fks"
down_revision = "0002_loan_item_unique"  # or 0001_loans if 0002 not applied
branch_labels = None
depends_on = None


def upgrade():
    op.create_foreign_key(
        "fk_loans_party_id",
        "loans",
        "loan_parties",
        ["party_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_foreign_key(
        "fk_loan_items_loan_id",
        "loan_items",
        "loans",
        ["loan_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_exhibition_items_exhibition_id",
        "exhibition_items",
        "exhibitions",
        ["exhibition_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_exhibition_items_exhibition_id", "exhibition_items", type_="foreignkey")
    op.drop_constraint("fk_loan_items_loan_id", "loan_items", type_="foreignkey")
    op.drop_constraint("fk_loans_party_id", "loans", type_="foreignkey")