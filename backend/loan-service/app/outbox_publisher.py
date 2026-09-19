import json
import logging
import threading
import time
from datetime import datetime, timezone

import pika
from sqlalchemy import select

from app.db import SessionLocal, settings
from app.models.outbox import OutboxEvent


logger = logging.getLogger(__name__)

EXCHANGE = "museum.events"
BATCH = 50
MAX_ATTEMPTS = 10


def _publish(channel, row: OutboxEvent) -> None:
    event_id = str(row.event_id)

    body = {
        "event_id": event_id,
        "event_type": row.event_type,
        "event_name": row.event_type,
        "schema_version": row.schema_version,
        "occurred_at": (
            row.occurred_at.isoformat()
            if row.occurred_at
            else None
        ),
        "producer": row.producer,
        "payload": row.payload,
    }

    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=row.event_type,
        body=json.dumps(body, default=str),
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            message_id=event_id,
        ),
    )


def publish_pending_once() -> int:
    db = SessionLocal()
    connection = None
    sent = 0

    try:
        rows = list(
            db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .where(OutboxEvent.attempts < MAX_ATTEMPTS)
                .order_by(OutboxEvent.id)
                .limit(BATCH)
                .with_for_update(skip_locked=True)
            ).all()
        )

        if not rows:
            return 0

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

        channel = connection.channel()

        channel.exchange_declare(
            exchange=EXCHANGE,
            exchange_type="topic",
            durable=True,
        )

        channel.confirm_delivery()

        for row in rows:
            try:
                _publish(channel, row)

                row.published_at = datetime.now(timezone.utc)
                row.last_error = None
                sent += 1

            except Exception as exc:
                row.attempts += 1
                row.last_error = str(exc)[:2000]

                logger.exception(
                    "Loan outbox publish failed event_id=%s",
                    row.event_id,
                )

        db.commit()

    except Exception:
        db.rollback()
        logger.exception("Loan outbox cycle failed")

    finally:
        db.close()

        if connection and not connection.is_closed:
            connection.close()

    return sent


def run_publisher_loop(interval_seconds: float = 1.0) -> None:
    while True:
        try:
            publish_pending_once()
        except Exception:
            logger.exception("Loan outbox loop error")

        time.sleep(interval_seconds)


def start_outbox_publisher() -> None:
    threading.Thread(
        target=run_publisher_loop,
        name="loan-outbox-publisher",
        daemon=True,
    ).start()