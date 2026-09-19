from datetime import date, datetime
from enum import Enum
from uuid import UUID

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


# ... LoanParty, Loan unchanged except direction/status can stay String storing enum values ...


class Loan(Base):
    ...
    party_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("loan_parties.id", ondelete="RESTRICT"),
        nullable=False,
    )

class LoanItem(Base):
    ...
    loan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("loans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

class ExhibitionItem(Base):
    ...
    exhibition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exhibitions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )