from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ConditionReportCreate(BaseModel):
    collection_item_id: UUID
    condition_score: float = Field(ge=0, le=100)
    observed_damage: str | None = None
    environmental_concerns: str | None = None
    recommendations: str | None = None
    report_date: date
    attachments: list | None = None


class TreatmentCreate(BaseModel):
    collection_item_id: UUID
    treatment_type: str
    start_date: date | None = None
    materials_used: list | None = None
    methodology: str | None = None
    before_after_documentation: list | None = None
    result: str | None = None
    notes: str | None = None


class TreatmentStatusUpdate(BaseModel):
    status: str


class EnvironmentalObservationCreate(BaseModel):
    storage_area_id: int
    observed_at: datetime
    temperature: float | None = None
    relative_humidity: float | None = None
    light_level: float | None = None
    source: str = "MANUAL"


def _bearer_from_request(request):
    return request.headers.get("Authorization")
