from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class LoanItemReservation(Base):
    __tablename__ = "loan_item_reservations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    collection_item_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )

    loan_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )