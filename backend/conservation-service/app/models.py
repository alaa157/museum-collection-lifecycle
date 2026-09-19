from datetime import date, datetime
from uuid import UUID, uuid4
from sqlalchemy import Date, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum
from app.db import Base


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[UUID] = mapped_column(unique=True, nullable=False, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(150), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    producer: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text())


class TreatmentStatus(str):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ConditionReport(Base):
    __tablename__ = "condition_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    condition_score: Mapped[float] = mapped_column(Float, nullable=False)
    observed_damage: Mapped[str | None] = mapped_column(Text())
    environmental_concerns: Mapped[str | None] = mapped_column(Text())
    recommendations: Mapped[str | None] = mapped_column(Text())
    inspector_id: Mapped[int] = mapped_column(Integer, nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    attachments: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class ConservationTreatment(Base):
    __tablename__ = "conservation_treatments"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_item_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    treatment_type: Mapped[str] = mapped_column(String(255), nullable=False)
    conservator_id: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    materials_used: Mapped[list | None] = mapped_column(JSON)
    methodology: Mapped[str | None] = mapped_column(Text())
    before_after_documentation: Mapped[list | None] = mapped_column(JSON)
    result: Mapped[str | None] = mapped_column(Text())
    notes: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(
        String(30),
        default=TreatmentStatus.PLANNED,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


class EnvironmentalObservation(Base):
    __tablename__ = "environmental_observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    storage_area_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    temperature: Mapped[float | None] = mapped_column(Float)
    relative_humidity: Mapped[float | None] = mapped_column(Float)
    light_level: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(100), default="MANUAL")
