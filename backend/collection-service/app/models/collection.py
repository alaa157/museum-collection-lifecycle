from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CollectionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ON_DISPLAY = "ON_DISPLAY"
    IN_STORAGE = "IN_STORAGE"
    ON_LOAN = "ON_LOAN"
    UNDER_CONSERVATION = "UNDER_CONSERVATION"
    MISSING = "MISSING"
    DEACCESSIONED = "DEACCESSIONED"


class MovementStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AcquisitionType(str, Enum):
    PURCHASE = "PURCHASE"
    DONATION = "DONATION"
    BEQUEST = "BEQUEST"
    TRANSFER = "TRANSFER"
    EXCAVATION = "EXCAVATION"
    FOUND_IN_COLLECTION = "FOUND_IN_COLLECTION"
    OTHER = "OTHER"


class ImageType(str, Enum):
    PRIMARY = "PRIMARY"
    DETAIL = "DETAIL"
    CONDITION = "CONDITION"
    CONSERVATION = "CONSERVATION"
    DOCUMENTATION = "DOCUMENTATION"


collection_materials = __import__("sqlalchemy").Table(
    "collection_item_materials",
    Base.metadata,
    __import__("sqlalchemy").Column(
        "collection_item_id",
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    __import__("sqlalchemy").Column(
        "material_id",
        ForeignKey("materials.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

collection_creators = __import__("sqlalchemy").Table(
    "collection_item_creators",
    Base.metadata,
    __import__("sqlalchemy").Column(
        "collection_item_id",
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    __import__("sqlalchemy").Column(
        "creator_id",
        ForeignKey("creators.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ObjectType(Base):
    __tablename__ = "object_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text())

    items = relationship("CollectionItem", back_populates="object_type")


class Culture(Base):
    __tablename__ = "cultures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    region: Mapped[str | None] = mapped_column(String(150))

    items = relationship("CollectionItem", back_populates="culture")


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text())

    items = relationship(
        "CollectionItem",
        secondary=collection_materials,
        back_populates="materials",
    )


class Creator(Base):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    birth_year: Mapped[int | None] = mapped_column(Integer)
    death_year: Mapped[int | None] = mapped_column(Integer)
    nationality: Mapped[str | None] = mapped_column(String(150))

    items = relationship(
        "CollectionItem",
        secondary=collection_creators,
        back_populates="creators",
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text())

    parent = relationship("Location", remote_side=[id], back_populates="children")
    children = relationship("Location", back_populates="parent")
    items = relationship("CollectionItem", back_populates="current_location")


class CollectionItem(Base):
    __tablename__ = "collection_items"

    id: Mapped[UUID] = mapped_column(
        default=uuid4,
        primary_key=True,
    )
    accession_number: Mapped[str] = mapped_column(String(100), nullable=False)
    object_number: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    classification: Mapped[str | None] = mapped_column(String(255))
    period_date: Mapped[str | None] = mapped_column(String(150))
    dimensions: Mapped[dict | None] = mapped_column(JSONB)
    techniques: Mapped[str | None] = mapped_column(Text())
    place_of_origin: Mapped[str | None] = mapped_column(String(255))

    object_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("object_types.id", ondelete="SET NULL")
    )
    culture_id: Mapped[int | None] = mapped_column(
        ForeignKey("cultures.id", ondelete="SET NULL")
    )
    current_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )

    acquisition_method: Mapped[AcquisitionType | None] = mapped_column(
        SAEnum(AcquisitionType, name="acquisition_type")
    )
    acquisition_date: Mapped[date | None] = mapped_column(Date)

    ownership_status: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="OWNED",
    )
    legal_status: Mapped[str | None] = mapped_column(String(255))
    current_condition: Mapped[str | None] = mapped_column(String(255))
    value: Mapped[float | None] = mapped_column(Float)
    insurance_value: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text())

    previous_status: Mapped[CollectionStatus | None] = mapped_column(
        SAEnum(
            CollectionStatus,
            name="collection_status",
            create_type=False,
        ),
        nullable=True,
    )

    status: Mapped[CollectionStatus] = mapped_column(
        SAEnum(CollectionStatus, name="collection_status"),
        default=CollectionStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    object_type = relationship("ObjectType", back_populates="items")
    culture = relationship("Culture", back_populates="items")
    current_location = relationship("Location", back_populates="items")
    materials = relationship(
        "Material",
        secondary=collection_materials,
        back_populates="items",
    )
    creators = relationship(
        "Creator",
        secondary=collection_creators,
        back_populates="items",
    )
    acquisitions = relationship(
        "Acquisition",
        back_populates="collection_item",
        cascade="all, delete-orphan",
    )
    provenance_records = relationship(
        "ProvenanceRecord",
        back_populates="collection_item",
        cascade="all, delete-orphan",
        order_by="ProvenanceRecord.start_date",
    )
    movements = relationship(
        "Movement",
        back_populates="collection_item",
        cascade="all, delete-orphan",
        order_by="Movement.created_at",
    )
    movement_requests = relationship(
        "MovementRequest",
        back_populates="collection_item",
        cascade="all, delete-orphan",
        order_by="MovementRequest.created_at",
    )
    attachments = relationship(
        "Attachment",
        back_populates="collection_item",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("accession_number", name="uq_collection_item_accession"),
        UniqueConstraint("object_number", name="uq_collection_item_object_number"),
        Index("ix_collection_items_title", "title"),
    )


class Acquisition(Base):
    __tablename__ = "acquisitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    acquisition_type: Mapped[AcquisitionType] = mapped_column(
        SAEnum(AcquisitionType, name="acquisition_type"),
        nullable=False,
    )
    acquisition_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str | None] = mapped_column(String(3))
    legal_documentation: Mapped[str | None] = mapped_column(Text())
    notes: Mapped[str | None] = mapped_column(Text())
    responsible_user_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    collection_item = relationship("CollectionItem", back_populates="acquisitions")


class ProvenanceRecord(Base):
    __tablename__ = "provenance_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    previous_owner: Mapped[str] = mapped_column(String(255), nullable=False)
    ownership_period: Mapped[str | None] = mapped_column(String(255))
    acquisition_source: Mapped[str | None] = mapped_column(String(255))
    transaction_type: Mapped[str | None] = mapped_column(String(100))
    record_date: Mapped[date | None] = mapped_column(Date)
    start_date: Mapped[date | None] = mapped_column(Date)
    geographic_location: Mapped[str | None] = mapped_column(String(255))
    evidence_documentation: Mapped[str | None] = mapped_column(Text())
    notes: Mapped[str | None] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    collection_item = relationship(
        "CollectionItem",
        back_populates="provenance_records",
    )


class MovementRequest(Base):
    __tablename__ = "movement_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_location_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id", ondelete="SET NULL")
    )
    to_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id", ondelete="RESTRICT"),
        nullable=False,
    )
    requested_by: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_by: Mapped[int | None] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text(), nullable=False)
    status: Mapped[MovementStatus] = mapped_column(
        SAEnum(MovementStatus, name="movement_status"),
        default=MovementStatus.REQUESTED,
        nullable=False,
        index=True,
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    collection_item = relationship(
        "CollectionItem",
        back_populates="movement_requests",
    )


class Movement(Base):
    __tablename__ = "movements"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_location_id: Mapped[int | None] = mapped_column(Integer)
    to_location_id: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_request_id: Mapped[int] = mapped_column(
        ForeignKey("movement_requests.id", ondelete="RESTRICT"),
        nullable=False,
    )
    moved_by: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text())
    moved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    collection_item = relationship("CollectionItem", back_populates="movements")


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    storage_category: Mapped[str] = mapped_column(String(100), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(150), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    image_type: Mapped[ImageType | None] = mapped_column(
        SAEnum(ImageType, name="image_type")
    )
    photographer: Mapped[str | None] = mapped_column(String(255))
    caption: Mapped[str | None] = mapped_column(Text())
    uploaded_by: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    collection_item = relationship("CollectionItem", back_populates="attachments")


class CollectionEvent(Base):
    __tablename__ = "collection_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    performed_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
