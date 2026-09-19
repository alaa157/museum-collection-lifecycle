from datetime import date

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db, settings
from app.messaging import publish_event
from app.models import (
    Exhibition,
    ExhibitionItem,
    ExhibitionStatus,
    Loan,
    LoanItem,
    LoanParty,
    LoanStatus,
)
from app.schemas import (
    ExhibitionCreate,
    ExhibitionItemCreate,
    ExhibitionStatusUpdate,
    LoanCreate,
    LoanStatusUpdate,
)
from app.security import require_permission
from app.messaging import enqueue_event

router = APIRouter()

BLOCKED_ITEM_STATUSES = {
    "ON_LOAN",
    "UNDER_CONSERVATION",
    "MISSING",
    "DEACCESSIONED",
}
ACTIVE_LOAN_STATUSES = {
    LoanStatus.REQUESTED,
    LoanStatus.UNDER_REVIEW,
    LoanStatus.APPROVED,
    LoanStatus.ACTIVE,
    LoanStatus.RETURN_DUE,
}


def _collection_base_url() -> str:
    return getattr(settings, "collection_service_url", None) or "http://127.0.0.1:8002"


def _bearer(request: Request) -> str | None:
    return request.headers.get("Authorization")


def fetch_collection_item(item_id, authorization: str | None) -> dict:
    headers = {"Authorization": authorization} if authorization else {}
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(
                f"{_collection_base_url().rstrip('/')}/api/v1/collection/items/{item_id}",
                headers=headers,
            )
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Collection service unavailable.")

    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Collection item not found: {item_id}")
    if response.status_code >= 400:
        raise HTTPException(status_code=502, detail="Unable to validate collection item.")
    return response.json()


def assert_items_loanable(
    item_ids: list,
    db: Session,
    authorization: str | None,
    *,
    exclude_loan_id: int | None = None,
) -> None:
    for item_id in item_ids:
        item = fetch_collection_item(item_id, authorization)
        status = item.get("status")
        if status in BLOCKED_ITEM_STATUSES:
            raise HTTPException(
                status_code=409,
                detail=f"Collection item {item_id} is not loanable (status={status}).",
            )

        conflict = select(LoanItem.id).join(Loan).where(
            LoanItem.collection_item_id == item_id,
            Loan.status.in_([s.value if hasattr(s, "value") else s for s in ACTIVE_LOAN_STATUSES]),
        )
        if exclude_loan_id is not None:
            conflict = conflict.where(Loan.id != exclude_loan_id)
        if db.scalar(conflict.limit(1)):
            raise HTTPException(
                status_code=409,
                detail=f"Collection item {item_id} is already on another active loan.",
            )


@router.get("/dashboard/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("loans:read")),
):
    active_loans = db.scalar(
        select(func.count(Loan.id)).where(Loan.status == LoanStatus.ACTIVE)
    ) or 0

    overdue = db.scalar(
        select(func.count(Loan.id)).where(
            Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.RETURN_DUE]),
            Loan.due_date < func.current_date(),
        )
    ) or 0

    upcoming_exhibitions = db.scalar(
        select(func.count(Exhibition.id)).where(
            Exhibition.status == ExhibitionStatus.PLANNED,
            Exhibition.start_date >= func.current_date(),
        )
    ) or 0

    return {
        "active_loans": active_loans,
        "overdue_loans": overdue,
        "upcoming_exhibitions": upcoming_exhibitions,
    }


@router.post("", status_code=201)
def create_loan(
    payload: LoanCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("loans:write")),
):
    if payload.due_date < payload.start_date:
        raise HTTPException(
            status_code=422,
            detail="Loan due date cannot precede start date.",
        )

    if not db.get(LoanParty, payload.party_id):
        raise HTTPException(status_code=404, detail="Loan party not found.")

    assert_items_loanable(
        payload.collection_item_ids,
        db,
        _bearer(request),
    )

    loan = Loan(
        direction=payload.direction.value if hasattr(payload.direction, "value") else payload.direction,
        party_id=payload.party_id,
        start_date=payload.start_date,
        due_date=payload.due_date,
        insurance_value=payload.insurance_value,
        agreement_document=payload.agreement_document,
        notes=payload.notes,
        created_by=user_id,
        status=LoanStatus.REQUESTED,
    )

    db.add(loan)
    db.flush()

    for item_id in payload.collection_item_ids:
        db.add(LoanItem(loan_id=loan.id, collection_item_id=item_id))

    db.commit()
    db.refresh(loan)
    return loan


@router.get("")
def list_loans(
    loan_status: LoanStatus | None = None,
    db: Session = Depends(get_db),
    _user_id: int = Depends(require_permission("loans:read")),
):
    statement = select(Loan).order_by(Loan.created_at.desc())
    if loan_status:
        statement = statement.where(Loan.status == loan_status)
    return db.scalars(statement).all()


@router.patch("/{loan_id}/status")
def update_loan_status(
    loan_id: int,
    payload: LoanStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user_id: int = Depends(require_permission("loans:write")),
):
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")

    transitions = {
        LoanStatus.REQUESTED: {LoanStatus.UNDER_REVIEW, LoanStatus.CANCELLED},
        LoanStatus.UNDER_REVIEW: {LoanStatus.APPROVED, LoanStatus.CANCELLED},
        LoanStatus.APPROVED: {LoanStatus.ACTIVE, LoanStatus.CANCELLED},
        LoanStatus.ACTIVE: {LoanStatus.RETURN_DUE},
        LoanStatus.RETURN_DUE: {LoanStatus.RETURNED},
        LoanStatus.RETURNED: set(),
        LoanStatus.CANCELLED: set(),
    }

    desired = payload.status
    if hasattr(desired, "value"):
        desired = desired.value
    current = loan.status

    allowed = transitions.get(current, set())
    allowed_values = {s.value if hasattr(s, "value") else s for s in allowed}
    if desired not in allowed_values and desired not in allowed:
        raise HTTPException(
            status_code=409,
            detail=f"Invalid loan transition: {current} -> {desired}.",
        )

    items = list(
        db.scalars(select(LoanItem).where(LoanItem.loan_id == loan.id)).all()
    )
    item_ids = [row.collection_item_id for row in items]

    if desired == LoanStatus.APPROVED:
        enqueue_event(
            db,
            "LoanApproved",
            {
                "loan_id": loan.id,
                "collection_item_ids": [
                    str(i) for i in item_ids
                ],
                "user_id": user_id,
            },
        )

    elif desired == LoanStatus.ACTIVE:
        enqueue_event(
            db,
            "LoanActivated",
            {
                "loan_id": loan.id,
                "collection_item_ids": [
                    str(i) for i in item_ids
                ],
                "user_id": user_id,
            },
        )

    elif desired == LoanStatus.RETURNED:
        enqueue_event(
            db,
            "LoanReturned",
            {
                "loan_id": loan.id,
                "collection_item_ids": [
                    str(i) for i in item_ids
                ],
                "user_id": user_id,
            },
        )

    loan.status = desired

    db.commit()

    return loan