from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db, settings
import httpx
from app.models import ( ConditionReport, ConservationTreatment, EnvironmentalObservation, TreatmentStatus,)
from app.schemas import ( ConditionReportCreate, EnvironmentalObservationCreate, TreatmentCreate, TreatmentStatusUpdate, _bearer_from_request,)
from app.messaging import enqueue_event
from app.security import require_permission

router = APIRouter()
collection_service_url: str = "http://127.0.0.1:8002"

def assert_collection_item_exists(item_id, authorization: str | None = None):
    headers = {"Authorization": authorization} if authorization else {}
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(
                f"{settings.collection_service_url}/api/v1/collection/items/{item_id}",
                headers=headers,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Collection service unavailable.")
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Collection item not found.")
    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="Unable to validate collection item.")

@router.post("/condition-reports", status_code=201)
def create_condition_report(
    payload: ConditionReportCreate,
    db: Session = Depends(get_db),
    user=Depends(require_permission("conservation:write")),
):
    assert_collection_item_exists(payload.collection_item_id, authorization=user[1])
    user_id, roles = user

    report = ConditionReport(
        **payload.model_dump(),
        inspector_id=user_id,
    )

    db.add(report)
    failed = payload.condition_score < 50

    enqueue_event(
        db,
        "ConditionReportFailed" if failed else "ConditionReportCreated",
        {
            "condition_report_id": report.id,
            "collection_item_id": str(
                payload.collection_item_id
            ),
            "condition_score": payload.condition_score,
            "user_id": user_id,
        },
    )

    db.commit()
    db.refresh(report)

    return report


@router.get("/condition-reports/{item_id}")
def list_condition_reports(
    item_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("conservation:read")),
):
    return db.scalars(
        select(ConditionReport)
        .where(ConditionReport.collection_item_id == item_id)
        .order_by(ConditionReport.report_date.desc())
    ).all()


@router.post(
    "/treatments",
    status_code=201,
)
def create_treatment(
    payload: TreatmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(
        require_permission("conservation:write")
    ),
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

@router.patch(
    "/treatments/{treatment_id}/status"
)
def update_treatment_status(
    treatment_id: int,
    payload: TreatmentStatusUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(
        require_permission("conservation:write")
    ),
):
    treatment = db.get(
        ConservationTreatment,
        treatment_id,
    )

    if not treatment:
        raise HTTPException(
            status_code=404,
            detail="Treatment not found.",
        )

    desired = payload.status

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

    if desired not in transitions.get(
        treatment.status,
        set(),
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Invalid conservation transition: "
                f"{treatment.status} -> {desired}."
            ),
        )

    treatment.status = desired

    if desired == TreatmentStatus.COMPLETED:
        treatment.end_date = (
            datetime.now(timezone.utc).date()
        )

    if desired == TreatmentStatus.IN_PROGRESS:
        enqueue_event(
            db,
            "ConservationStarted",
            {
                "treatment_id": treatment.id,
                "collection_item_id": str(
                    treatment.collection_item_id
                ),
                "user_id": user_id,
            },
        )

    elif desired == TreatmentStatus.COMPLETED:
        enqueue_event(
            db,
            "ConservationCompleted",
            {
                "treatment_id": treatment.id,
                "collection_item_id": str(
                    treatment.collection_item_id
                ),
                "user_id": user_id,
            },
        )

    db.commit()
    db.refresh(treatment)

    return treatment


@router.get("/treatments/{item_id}")
def list_treatments(
    item_id: str,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("conservation:read")),
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
    user=Depends(require_permission("conservation:write")),
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
                "user_id": user[0],
            },
        )

    return observation


@router.get("/environmental-observations/{storage_area_id}")
def list_environmental_observations(
    storage_area_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("conservation:read")),
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
    _user=Depends(require_permission("conservation:read")),
):
    from app.dashboard import summary
    return summary(db)
