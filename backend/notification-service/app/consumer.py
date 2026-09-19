import json
import logging
import threading
import time

import pika
from sqlalchemy import select

from app.db import Notification, SessionLocal, settings

logger = logging.getLogger(__name__)

EXCHANGE = "museum.events"
QUEUE = "notification-service"

# delivery: required | optional | broadcast
EVENT_ROUTING = {
    "CollectionItemCreated": "optional",
    "CollectionItemMoved": "optional",
    "ConditionReportFailed": "broadcast",
    "ConservationStarted": "optional",
    "ConservationCompleted": "optional",
    "LoanApproved": "optional",
    "LoanReturned": "optional",
    "AttachmentUploaded": "optional",
    "ExhibitionStarted": "broadcast",
    "EnvironmentalWarning": "broadcast",
}

NOTIFICATION_TEMPLATES = {
    "CollectionItemCreated": (
        "Collection item created",
        "A new collection item was added to the institutional collection.",
    ),
    "CollectionItemMoved": (
        "Collection item moved",
        "A collection item movement was completed.",
    ),
    "ConditionReportFailed": (
        "Condition warning",
        "A condition report indicates that attention may be required.",
    ),
    "ConservationStarted": (
        "Conservation started",
        "Conservation treatment has started for a collection item.",
    ),
    "ConservationCompleted": (
        "Conservation completed",
        "A conservation treatment has been completed.",
    ),
    "LoanApproved": (
        "Loan approved",
        "A collection loan has been approved.",
    ),
    "LoanReturned": (
        "Loan returned",
        "A loan has been marked as returned.",
    ),
    "AttachmentUploaded": (
        "Digital asset uploaded",
        "A new digital asset was attached to a collection item.",
    ),
    "ExhibitionStarted": (
        "Exhibition started",
        "An exhibition has become active.",
    ),
    "EnvironmentalWarning": (
        "Environmental warning",
        "An environmental observation exceeded the configured development thresholds.",
    ),
}

# Roles / users that receive system broadcasts (replace with real directory lookup later)
BROADCAST_USER_IDS = (1,)  # e.g. seed admin; load from config/DB in production


def _resolve_recipients(event_name: str, payload: dict) -> list[int]:
    mode = EVENT_ROUTING.get(event_name, "optional")
    raw = payload.get("user_id") or payload.get("recipient_user_id")
    recipients: list[int] = []

    if raw is not None:
        recipients.append(int(raw))

    if mode == "required" and not recipients:
        raise ValueError(f"Event {event_name} requires recipient user_id")

    if mode == "broadcast":
        # include explicit user if present, plus system recipients
        merged = set(recipients)
        merged.update(BROADCAST_USER_IDS)
        return sorted(merged)

    # optional: notify only if a user is present; empty = intentional no-op
    return recipients


def process_event(event: dict) -> None:
    event_name = (
        event.get("event_type")
        or event.get("event_name")
    )

    payload = event.get("payload") or {}
    event_id = event.get("event_id")

    if not event_name:
        raise ValueError(
            "Missing event_name/event_type"
        )

    if not event_id:
        raise ValueError(
            "Missing event_id"
        )

    recipients = _resolve_recipients(
        event_name,
        payload,
    )

    db = SessionLocal()

    try:
        already_processed = db.scalar(
            select(ProcessedEvent.id).where(
                ProcessedEvent.event_id == str(event_id)
            )
        )

        if already_processed:
            return

        if recipients:
            title, message = NOTIFICATION_TEMPLATES.get(
                event_name,
                (
                    "Museum system activity",
                    f"Event received: {event_name}",
                ),
            )

            for user_id in recipients:
                db.add(
                    Notification(
                        user_id=user_id,
                        event_name=event_name,
                        title=title,
                        message=message,
                    )
                )

        db.add(
            ProcessedEvent(
                event_id=str(event_id),
                consumer="notification-service",
            )
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def consume():
    while True:
        connection = None
        try:
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
            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE, durable=True)
            channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key="#")

            def callback(ch, method, properties, body):
                try:
                    process_event(json.loads(body))
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except json.JSONDecodeError:
                    logger.exception("Malformed notification message")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except ValueError:
                    # contract violation (e.g. required recipient missing)
                    logger.exception("Notification contract violation")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                except Exception:
                    logger.exception("Notification persistence failed")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

            channel.basic_qos(prefetch_count=20)
            channel.basic_consume(queue=QUEUE, on_message_callback=callback)
            logger.info("Notification consumer started.")
            channel.start_consuming()
        except Exception:
            logger.exception("Notification RabbitMQ consumer disconnected; retrying.")
            time.sleep(5)
        finally:
            if connection and not connection.is_closed:
                connection.close()


def start_consumer():
    threading.Thread(
        target=consume,
        name="notification-rabbitmq-consumer",
        daemon=True,
    ).start()