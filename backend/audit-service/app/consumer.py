import json
import logging
import threading
import time
import pika
from app.db import AuditLog, SessionLocal, settings


logger = logging.getLogger(__name__)

EXCHANGE = "museum.events"
QUEUE = "audit-service"


ENTITY_MAPPING = {
    "CollectionItemCreated": ("CollectionItem", "ITEM_CREATED"),
    "CollectionItemUpdated": ("CollectionItem", "ITEM_UPDATED"),
    "CollectionItemAcquired": ("CollectionItem", "ITEM_ACQUIRED"),
    "AcquisitionRecorded": ("Acquisition", "ACQUISITION_RECORDED"),
    "CollectionItemMoved": ("CollectionItem", "ITEM_MOVED"),
    "CollectionMovementRequested": ("MovementRequest", "MOVEMENT_REQUESTED"),
    "CollectionMovementApproved": ("MovementRequest", "MOVEMENT_APPROVED"),
    "CollectionMovementRejected": ("MovementRequest", "MOVEMENT_REJECTED"),
    "CollectionMovementStarted": ("MovementRequest", "MOVEMENT_STARTED"),
    "CollectionMovementCompleted": ("MovementRequest", "MOVEMENT_COMPLETED"),
    "CollectionMovementCancelled": ("MovementRequest", "MOVEMENT_CANCELLED"),
    "ProvenanceAdded": ("ProvenanceRecord", "PROVENANCE_ADDED"),
    "ConditionReportCreated": ("ConditionReport", "CONDITION_REPORT_CREATED"),
    "ConditionReportFailed": ("ConditionReport", "CONDITION_REPORT_FAILED"),
    "ConservationStarted": ("ConservationTreatment", "TREATMENT_STARTED"),
    "ConservationCompleted": ("ConservationTreatment", "TREATMENT_COMPLETED"),
    "LoanApproved": ("Loan", "LOAN_APPROVED"),
    "LoanReturned": ("Loan", "LOAN_RETURNED"),
    "AttachmentUploaded": ("Attachment", "ATTACHMENT_UPLOADED"),
    "ExhibitionCreated": ("Exhibition", "EXHIBITION_CREATED"),
    "ExhibitionStarted": ("Exhibition", "EXHIBITION_STARTED"),
    "EnvironmentalWarning": ("EnvironmentalObservation", "ENVIRONMENTAL_WARNING"),
    "LoanApproved": ("Loan", "LOAN_APPROVED"),
    "LoanActivated": ("Loan", "LOAN_ACTIVATED"),
    "LoanReturned": ("Loan", "LOAN_RETURNED"),
}


def process_event(message: dict) -> None:
    event_name = message.get("event_type") or message.get("event_name") or "UNKNOWN"
    payload = message.get("payload") or {}
    event_id = message.get("event_id")

    entity_type, action = ENTITY_MAPPING.get(
        event_name,
        ("SystemEvent", str(event_name).upper()),
    )

    entity_id = (
        payload.get("item_id")
        or payload.get("collection_item_id")
        or payload.get("loan_id")
        or payload.get("treatment_id")
        or payload.get("condition_report_id")
        or payload.get("attachment_id")
        or payload.get("exhibition_id")
        or payload.get("observation_id")
        or payload.get("movement_request_id")
        or payload.get("provenance_id")
        or payload.get("acquisition_id")
    )

    db = SessionLocal()
    try:
        # idempotency (5.3) — skip if already processed
        if event_id and db.scalar(
            select(ProcessedEvent.id).where(ProcessedEvent.event_id == str(event_id))
        ):
            return

        db.add(
            AuditLog(
                user_id=payload.get("user_id"),
                action=action,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                ip_address=payload.get("ip_address"),
                correlation_id=payload.get("correlation_id"),
                old_state=payload.get("old_state"),
                new_state=payload.get("new_state"),
                event_payload=payload,
            )
        )
        if event_id:
            db.add(ProcessedEvent(event_id=str(event_id), consumer="audit-service"))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def callback(ch, method, properties, body):
    try:
        process_event(json.loads(body))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except json.JSONDecodeError:
        logger.exception("Malformed audit message; dead-letter")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception:
        logger.exception("Audit persistence failed; requeue")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

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

            channel.exchange_declare(
                exchange=EXCHANGE,
                exchange_type="topic",
                durable=True,
            )

            channel.queue_declare(
                queue=QUEUE,
                durable=True,
            )

            channel.queue_bind(
                queue=QUEUE,
                exchange=EXCHANGE,
                routing_key="#",
            )

            def callback(ch, method, properties, body):
                try:
                    process_event(json.loads(body))
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                except Exception:
                    logger.exception("Audit event failed.")
                    ch.basic_nack(
                        delivery_tag=method.delivery_tag,
                        requeue=False,
                    )

            channel.basic_qos(prefetch_count=20)

            channel.basic_consume(
                queue=QUEUE,
                on_message_callback=callback,
            )

            logger.info("Audit consumer started.")
            channel.start_consuming()

        except Exception:
            logger.exception(
                "Audit RabbitMQ consumer disconnected; retrying."
            )
            time.sleep(5)

        finally:
            if connection and not connection.is_closed:
                connection.close()


def start_consumer():
    thread = threading.Thread(
        target=consume,
        name="audit-rabbitmq-consumer",
        daemon=True,
    )

    thread.start()
