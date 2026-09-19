from datetime import date, datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class Status(str, Enum):
    ACTIVE = "ACTIVE"
    ON_DISPLAY = "ON_DISPLAY"
    IN_STORAGE = "IN_STORAGE"
    ON_LOAN = "ON_LOAN"
    UNDER_CONSERVATION = "UNDER_CONSERVATION"
    MISSING = "MISSING"
    DEACCESSIONED = "DEACCESSIONED"


class AcquisitionType(str, Enum):
    PURCHASE = "PURCHASE"
    DONATION = "DONATION"
    BEQUEST = "BEQUEST"
    TRANSFER = "TRANSFER"
    EXCAVATION = "EXCAVATION"
    FOUND_IN_COLLECTION = "FOUND_IN_COLLECTION"
    OTHER = "OTHER"


class MovementStatus(str, Enum):
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CollectionItemCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    accession_number: str = Field(min_length=1, max_length=100)
    object_number: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    classification: str | None = None
    object_type_id: int | None = None
    creator_ids: list[int] = Field(default_factory=list)
    culture_id: int | None = None
    material_ids: list[int] = Field(default_factory=list)
    period_date: str | None = None
    dimensions: dict | None = None
    techniques: str | None = None
    place_of_origin: str | None = None
    acquisition_method: AcquisitionType | None = None
    acquisition_date: date | None = None
    ownership_status: str = "OWNED"
    legal_status: str | None = None
    current_condition: str | None = None
    value: float | None = Field(default=None, ge=0)
    insurance_value: float | None = Field(default=None, ge=0)
    notes: str | None = None
    current_location_id: int | None = None


class CollectionItemUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    classification: str | None = None
    object_type_id: int | None = None
    creator_ids: list[int] | None = None
    culture_id: int | None = None
    material_ids: list[int] | None = None
    period_date: str | None = None
    dimensions: dict | None = None
    techniques: str | None = None
    place_of_origin: str | None = None
    ownership_status: str | None = None
    legal_status: str | None = None
    current_condition: str | None = None
    value: float | None = Field(default=None, ge=0)
    insurance_value: float | None = Field(default=None, ge=0)
    notes: str | None = None
    version: int = Field(ge=1)


class CollectionItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    accession_number: str
    object_number: str
    title: str
    status: Status
    current_location_id: int | None
    object_type_id: int | None
    culture_id: int | None
    value: float | None
    insurance_value: float | None
    version: int
    created_at: datetime


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location_type: str = Field(min_length=1, max_length=50)
    parent_id: int | None = None
    description: str | None = None


class AcquisitionCreate(BaseModel):
    acquisition_type: AcquisitionType
    acquisition_date: date
    source: str = Field(min_length=1, max_length=255)
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    legal_documentation: str | None = None
    notes: str | None = None


class ProvenanceCreate(BaseModel):
    previous_owner: str = Field(min_length=1, max_length=255)
    ownership_period: str | None = None
    acquisition_source: str | None = None
    transaction_type: str | None = None
    record_date: date | None = None
    start_date: date | None = None
    geographic_location: str | None = None
    evidence_documentation: str | None = None
    notes: str | None = None


class MovementRequestCreate(BaseModel):
    to_location_id: int
    reason: str = Field(min_length=1)


class MovementDecision(BaseModel):
    status: MovementStatus


class AttachmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    mime_type: str
    size_bytes: int
    checksum: str
    image_type: str | None
    photographer: str | None
    caption: str | None


class PaginatedCollectionResponse(BaseModel):
    items: list[CollectionItemResponse]
    total: int
    offset: int
    limit: int
