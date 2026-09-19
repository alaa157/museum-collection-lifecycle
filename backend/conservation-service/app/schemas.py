from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db, settings
from app.messaging import publish_event
from app.models import (
    ConditionReport,
    ConservationTreatment,
    EnvironmentalObservation,
    TreatmentStatus,
)
from app.schemas import (
    ConditionReportCreate,
    EnvironmentalObservationCreate,
    TreatmentCreate,
    TreatmentStatusUpdate,
)
from app.security import require_permission

router = APIRouter()


def _collection_base_url() -> str:
    # Prefer settings if present; fall back for local/dev
    return getattr(settings, "collection_service_url", None) or "http://127.0.0.1:8002"


def assert_collection_item_exists(
    item_id,
    authorization: str | None = None,
) -> None:
    headers = {}
    if authorization:
        headers["Authorization"] = authorization

    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{_collection_base_url().rstrip('/')}/api/v1/collection/items/{item_id}",
                headers=headers,
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=502,
            detail="Collection service unavailable.",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail="Collection item not found.",
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail="Unable to validate collection item.",
        )


def _bearer_from_request(request: Request) -> str | None:
    return request.headers.get("Authorization")


@router.post("/condition-reports", status_code=201)
def create_condition_report(
    payload: ConditionReportCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("conservation:write")),
):
    assert_collection_item_exists(
        payload.collection_item_id,
        authorization=_bearer_from_request(request),
    )

    report = ConditionReport(
        **payload.model_dump(),
        inspector_id=user_id,
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    failed = payload.condition_score < 50
    publish_event(
        "ConditionReportFailed" if failed else "ConditionReportCreated",
        {
            "condition_report_id": report.id,
            "collection_item_id": str(payload.collection_item_id),
            "condition_score": payload.condition_score,
            "user_id": user_id,
        },
    )
    return report


@router.get("/condition-reports/{item_id}")
def list_condition_reports(
    item_id: str,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("conservation:read")),
):
    return db.scalars(
        select(ConditionReport)
        .where(ConditionReport.collection_item_id == item_id)
        .order_by(ConditionReport.report_date.desc())
    ).all()


@router.post("/treatments", status_code=201)
def create_treatment(
    payload: TreatmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("conservation:write")),
):
    assert_collection_item_exists(
        payload.collection_item_id,
        authorization=_bearer_from_request(request),
    )

    treatment = ConservationTreatment(
        **payload.model_dump(),
        conservator_id=user_id,
        status=TreatmentStatus.PLANNED,
    )

    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    return treatment


@router.patch("/treatments/{treatment_id}/status")
def update_treatment_status(
    treatment_id: int,
    payload: TreatmentStatusUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("conservation:write")),
):
    treatment = db.get(ConservationTreatment, treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="Treatment not found.")

    desired = payload.status
    if hasattr(desired, "value"):
        desired = desired.value
    elif isinstance(desired, str):
        desired = desired.upper()

    transitions = {
        TreatmentStatus.PLANNED: {
            TreatmentStatus.IN_PROGRESS,
            TreatmentStatus.CANCELLED,
        },
        TreatmentStatus.IN_PROGRESS: {
            TreatmentStatus.COMPLETED,
            TreatmentStatus.CANCELLED,
        },
        TreatmentStatus.COMPLETED: set(),
        TreatmentStatus.CANCELLED: set(),
    }

    # Normalize keys/values to strings so DB str status and Enum both work
    current = treatment.status
    if hasattr(current, "value"):
        current = current.value

    allowed = {
        (s.value if hasattr(s, "value") else s) for s in transitions.get(current, set())
    }
    # Also allow lookup when transitions keys are Enum members
    if not allowed and hasattr(TreatmentStatus, "PLANNED"):
        allowed = {
            (s.value if hasattr(s, "value") else s)
            for key, targets in transitions.items()
            if (key.value if hasattr(key, "value") else key) == current
            for s in targets
        }

    if desired not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid conservation transition: {current} -> {desired}.",
        )

    treatment.status = desired
    if desired == (
        TreatmentStatus.COMPLETED.value
        if hasattr(TreatmentStatus.COMPLETED, "value")
        else TreatmentStatus.COMPLETED
    ):
        treatment.end_date = datetime.now(timezone.utc).date()

    db.commit()
    db.refresh(treatment)

    started = TreatmentStatus.IN_PROGRESS.value if hasattr(TreatmentStatus.IN_PROGRESS, "value") else TreatmentStatus.IN_PROGRESS
    completed = TreatmentStatus.COMPLETED.value if hasattr(TreatmentStatus.COMPLETED, "value") else TreatmentStatus.COMPLETED

    if desired == started:
        publish_event(
            "ConservationStarted",
            {
                "treatment_id": treatment.id,
                "collection_item_id": str(treatment.collection_item_id),
                "user_id": user_id,
            },
        )
    elif desired == completed:
        publish_event(
            "ConservationCompleted",
            {
                "treatment_id": treatment.id,
                "collection_item_id": str(treatment.collection_item_id),
                "user_id": user_id,
            },
        )

    return treatment


@router.get("/treatments/{item_id}")
def list_treatments(
    item_id: str,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("conservation:read")),
):
    return db.scalars(
        select(ConservationTreatment)
        .where(ConservationTreatment.collection_item_id == item_id)
        .order_by(ConservationTreatment.created_at.desc())
    ).all()


@router.post("/environmental-observations", status_code=201)
def create_environmental_observation(
    payload: EnvironmentalObservationCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("conservation:write")),
):
    observation = EnvironmentalObservation(**payload.model_dump())

    db.add(observation)
    db.commit()
    db.refresh(observation)

    abnormal = False
    if observation.temperature is not None:
        abnormal |= observation.temperature < 15 or observation.temperature > 25
    if observation.relative_humidity is not None:
        abnormal |= (
            observation.relative_humidity < 35
            or observation.relative_humidity > 65
        )

    if abnormal:
        publish_event(
            "EnvironmentalWarning",
            {
                "observation_id": observation.id,
                "storage_area_id": observation.storage_area_id,
                "temperature": observation.temperature,
                "relative_humidity": observation.relative_humidity,
                "user_id": user_id,
            },
        )

    return observation


@router.get("/environmental-observations/{storage_area_id}")
def list_environmental_observations(
    storage_area_id: int,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("conservation:read")),
):
    return db.scalars(
        select(EnvironmentalObservation)
        .where(EnvironmentalObservation.storage_area_id == storage_area_id)
        .order_by(EnvironmentalObservation.observed_at.desc())
        .limit(500)
    ).all()


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("conservation:read")),
):
    from app.dashboard import summary

    return summary(db)