"""collection foundation

Revision ID: 0001_collection
Revises:
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_collection"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "object_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.UniqueConstraint("name", name="uq_object_types_name"),
    )

    op.create_table(
        "cultures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("region", sa.String(150)),
        sa.UniqueConstraint("name", name="uq_cultures_name"),
    )

    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text()),
        sa.UniqueConstraint("name", name="uq_materials_name"),
    )

    op.create_table(
        "creators",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("birth_year", sa.Integer()),
        sa.Column("death_year", sa.Integer()),
        sa.Column("nationality", sa.String(150)),
    )

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("location_type", sa.String(50), nullable=False),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
        ),
        sa.Column("description", sa.Text()),
    )

    acquisition_enum = postgresql.ENUM(
        "PURCHASE",
        "DONATION",
        "BEQUEST",
        "TRANSFER",
        "EXCAVATION",
        "FOUND_IN_COLLECTION",
        "OTHER",
        name="acquisition_type",
    )

    collection_status_enum = postgresql.ENUM(
        "ACTIVE",
        "ON_DISPLAY",
        "IN_STORAGE",
        "ON_LOAN",
        "UNDER_CONSERVATION",
        "MISSING",
        "DEACCESSIONED",
        name="collection_status",
    )

    movement_enum = postgresql.ENUM(
        "REQUESTED",
        "APPROVED",
        "REJECTED",
        "IN_TRANSIT",
        "COMPLETED",
        "CANCELLED",
        name="movement_status",
    )

    image_enum = postgresql.ENUM(
        "PRIMARY",
        "DETAIL",
        "CONDITION",
        "CONSERVATION",
        "DOCUMENTATION",
        name="image_type",
    )

    op.create_table(
        "collection_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("accession_number", sa.String(100), nullable=False),
        sa.Column("object_number", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("classification", sa.String(255)),
        sa.Column(
            "object_type_id",
            sa.Integer(),
            sa.ForeignKey("object_types.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "culture_id",
            sa.Integer(),
            sa.ForeignKey("cultures.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "current_location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="SET NULL"),
        ),
        sa.Column("period_date", sa.String(150)),
        sa.Column("dimensions", sa.JSON()),
        sa.Column("techniques", sa.Text()),
        sa.Column("place_of_origin", sa.String(255)),
        sa.Column("acquisition_method", acquisition_enum),
        sa.Column("acquisition_date", sa.Date()),
        sa.Column("ownership_status", sa.String(100), nullable=False),
        sa.Column("legal_status", sa.String(255)),
        sa.Column("current_condition", sa.String(255)),
        sa.Column("value", sa.Float()),
        sa.Column("insurance_value", sa.Float()),
        sa.Column("notes", sa.Text()),
        sa.Column("status", collection_status_enum, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "accession_number",
            name="uq_collection_item_accession",
        ),
        sa.UniqueConstraint(
            "object_number",
            name="uq_collection_item_object_number",
        ),
    )

    op.create_index(
        "ix_collection_items_status",
        "collection_items",
        ["status"],
    )

    op.create_table(
        "collection_item_materials",
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "material_id",
            sa.Integer(),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "collection_item_creators",
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "creator_id",
            sa.Integer(),
            sa.ForeignKey("creators.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "acquisitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("acquisition_type", acquisition_enum, nullable=False),
        sa.Column("acquisition_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("price", sa.Float()),
        sa.Column("currency", sa.String(3)),
        sa.Column("legal_documentation", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("responsible_user_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "provenance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("previous_owner", sa.String(255), nullable=False),
        sa.Column("ownership_period", sa.String(255)),
        sa.Column("acquisition_source", sa.String(255)),
        sa.Column("transaction_type", sa.String(100)),
        sa.Column("record_date", sa.Date()),
        sa.Column("start_date", sa.Date()),
        sa.Column("geographic_location", sa.String(255)),
        sa.Column("evidence_documentation", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "movement_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_location_id", sa.Integer()),
        sa.Column(
            "to_location_id",
            sa.Integer(),
            sa.ForeignKey("locations.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Integer()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", movement_enum, nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_location_id", sa.Integer()),
        sa.Column("to_location_id", sa.Integer(), nullable=False),
        sa.Column(
            "movement_request_id",
            sa.Integer(),
            sa.ForeignKey("movement_requests.id", ondelete="SET NULL"),
            nullable=False,
        ),
        sa.Column("moved_by", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text()),
        sa.Column("moved_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(255), nullable=False),
        sa.Column("storage_category", sa.String(100), nullable=False),
        sa.Column("mime_type", sa.String(150), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("image_type", image_enum),
        sa.Column("photographer", sa.String(255)),
        sa.Column("caption", sa.Text()),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("stored_filename", name="uq_attachments_stored_filename"),
    )

    op.create_table(
        "collection_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "collection_item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("collection_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("performed_by", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("collection_events")
    op.drop_table("attachments")
    op.drop_table("movements")
    op.drop_table("movement_requests")
    op.drop_table("provenance_records")
    op.drop_table("acquisitions")
    op.drop_table("collection_item_creators")
    op.drop_table("collection_item_materials")
    op.drop_index("ix_collection_items_status", table_name="collection_items")
    op.drop_table("collection_items")
    op.drop_table("locations")
    op.drop_table("creators")
    op.drop_table("materials")
    op.drop_table("cultures")
    op.drop_table("object_types")

    postgresql.ENUM(name="image_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="movement_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="collection_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="acquisition_type").drop(op.get_bind(), checkfirst=True)
    