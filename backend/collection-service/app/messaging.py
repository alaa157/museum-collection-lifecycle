import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.outbox import OutboxEvent


logger = logging.getLogger(__name__)

PRODUCER = "collection-service"


def enqueue_event(
    db: Session,
    event_type: str,
    payload: dict,
    *,
    event_id: UUID | None = None,
) -> OutboxEvent:
    """
    Add a domain event to the transactional outbox.

    The caller must commit the same SQLAlchemy transaction that
    changes the business data. No RabbitMQ connection is made here.
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