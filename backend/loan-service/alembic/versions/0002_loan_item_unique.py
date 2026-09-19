"""unique loan item pairs

Revision ID: 0002_loan_item_unique
Revises: 0001_loans
Create Date: 2026-09-08
"""

from alembic import op

revision = "0002_loan_item_unique"
down_revision = "0001_loans"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint(
        "uq_loan_item",
        "loan_items",
        ["loan_id", "collection_item_id"],
    )


def downgrade():
    op.drop_constraint("uq_loan_item", "loan_items", type_="unique")