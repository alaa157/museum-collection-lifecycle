import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.outbox import OutboxEvent


logger = logging.getLogger(__name__)

PRODUCER = "conservation-service"


def enqueue_event(
    db: Session,
    event_type: str,
    payload: dict,
    *,
    event_id: UUID | None = None,
) -> OutboxEvent:
    """
    Add a domain event to the transactional outbox.

    The business transaction and this outbox row are committed
    together by the caller.
    """
    row = OutboxEvent(
        event_id=event_id or uuid4(),
        event_type=event_type,
        schema_version=1,
        producer=PRODUCER,
        payload=payload,
        occurred_at=datetime.now(timezone.utc),
    )

    db.add(row)
    return row