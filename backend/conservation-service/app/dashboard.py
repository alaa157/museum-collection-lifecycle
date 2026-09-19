from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    ConditionReport,
    ConservationTreatment,
    EnvironmentalObservation,
)


def summary(db: Session) -> dict:
    treatments_in_progress = db.scalar(
        select(func.count(ConservationTreatment.id)).where(
            ConservationTreatment.status == "IN_PROGRESS"
        )
    ) or 0

    planned_treatments = db.scalar(
        select(func.count(ConservationTreatment.id)).where(
            ConservationTreatment.status == "PLANNED"
        )
    ) or 0

    completed_treatments = db.scalar(
        select(func.count(ConservationTreatment.id)).where(
            ConservationTreatment.status == "COMPLETED"
        )
    ) or 0

    reports = db.scalar(
        select(func.count(ConditionReport.id))
    ) or 0

    environmental_warnings = db.scalar(
        select(func.count(EnvironmentalObservation.id)).where(
            (
                (EnvironmentalObservation.temperature < 15) |
                (EnvironmentalObservation.temperature > 25) |
                (EnvironmentalObservation.relative_humidity < 35) |
                (EnvironmentalObservation.relative_humidity > 65)
            )
        )
    ) or 0

    return {
        "condition_reports": reports,
        "treatments_in_progress": treatments_in_progress,
        "planned_treatments": planned_treatments,
        "completed_treatments": completed_treatments,
        "environmental_warnings": environmental_warnings,
    }
