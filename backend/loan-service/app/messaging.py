import logging
import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
import pika

from app.db import settings
from app.models import OutboxEvent


logger = logging.getLogger(__name__)

PRODUCER = "loan-service"


def publish_event(event_type: str, payload: dict) -> None:
    """Publish a non-transactional event for legacy API paths."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=pika.PlainCredentials(
                settings.rabbitmq_user,
                settings.rabbitmq_password,
            ),
            heartbeat=30,
        )
    )
    try:
        channel = connection.channel()
        channel.exchange_declare(
            exchange="museum.events",
            exchange_type="topic",
            durable=True,
        )
        channel.basic_publish(
            exchange="museum.events",
            routing_key=event_type,
            body=json.dumps(payload, default=str),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
        )
    finally:
        connection.close()


def enqueue_event(
    db: Session,
    event_type: str,
    payload: dict,
    *,
    event_id: UUID | None = None,
) -> OutboxEvent:
    """
    Add a domain event to the transactional outbox.

    The caller commits this row together with the business change.
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