from datetime import date
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LoanStatus(str, Enum):
    REQUESTED = "REQUESTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    RETURN_DUE = "RETURN_DUE"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class LoanDirection(str, Enum):
    INCOMING = "INCOMING"
    OUTGOING = "OUTGOING"


class ExhibitionStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class LoanCreate(BaseModel):
    direction: LoanDirection
    party_id: int
    start_date: date
    due_date: date
    insurance_value: float | None = Field(default=None, ge=0)
    agreement_document: str | None = None
    notes: str | None = None
    collection_item_ids: list[UUID] = Field(min_length=1)

    @field_validator("collection_item_ids")
    @classmethod
    def no_duplicate_items(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("Duplicate collection item IDs.")
        return value


class LoanStatusUpdate(BaseModel):
    status: LoanStatus


class ExhibitionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    curator_id: int
    start_date: date
    end_date: date
    location: str = Field(min_length=1, max_length=255)


class ExhibitionStatusUpdate(BaseModel):
    status: ExhibitionStatus


class ExhibitionItemCreate(BaseModel):
    collection_item_id: UUID
    display_label: str | None = None
    display_order: int = 0