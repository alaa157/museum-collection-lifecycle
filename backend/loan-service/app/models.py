from datetime import date, datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from sqlalchemy import ForeignKey
from sqlalchemy.dialects import postgresql


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), unique=True, nullable=False, default=uuid4
    )
    event_type: Mapped[str] = mapped_column(String(150), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    producer: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(postgresql.JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)


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


class LoanParty(Base):
    __tablename__ = "loan_parties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    party_type: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_information: Mapped[dict | None] = mapped_column(postgresql.JSON)


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    party_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("loan_parties.id", ondelete="RESTRICT"),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    insurance_value: Mapped[float | None] = mapped_column(Float)
    agreement_document: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class LoanItem(Base):
    __tablename__ = "loan_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    loan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_item_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False, index=True
    )
    condition_on_dispatch: Mapped[str | None] = mapped_column(Text)
    condition_on_return: Mapped[str | None] = mapped_column(Text)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class Exhibition(Base):
    __tablename__ = "exhibitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    curator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class ExhibitionItem(Base):
    __tablename__ = "exhibition_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exhibition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exhibitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    collection_item_id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), nullable=False, index=True
    )
    display_label: Mapped[str | None] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)